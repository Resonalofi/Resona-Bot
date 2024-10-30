import ujson as json
import os
import sqlite3
import time
from .database import get_skdb_connection
from nonebot.log import logger

thresholds = [1, 2, 4, 8, 9, 10, 20, 30, 40, 50, 70, 90, 100]
HOUR_SECONDS = 3600
TWENTY_MINUTES = 1200

def current_event():
    events_path = os.path.join(os.path.dirname(__file__), 'sekaisk', 'twdata', 'events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    now = int(time.time() * 1000)
    for event in data:
        if event['startAt'] < now < event['closedAt']:
            return event['id']
    return None

def calculate_score_info(score_changes, current_score, now):
    result = ""
    last_hour_score = next((sc for sc in score_changes if sc[1] >= now - HOUR_SECONDS), None)

    if last_hour_score:
        hourly_score = current_score - last_hour_score[2]  
        hourly_speed = hourly_score / HOUR_SECONDS / 10000 
        result += f"\n时速: {hourly_speed:.1f}W"

        hour_count = sum(1 for i in range(1, len(score_changes)) if score_changes[i][2] > score_changes[i-1][2])
        result += f"\n本小时周回数: {hour_count}"

        if hour_count > 0:
            avg_score = (current_score - last_hour_score[2]) / 10000 / hour_count
            result += f"\n本小时平均单局pt: {avg_score:.3f}W"

    twenty_min_score = next((sc for sc in score_changes if sc[1] < now - TWENTY_MINUTES), None)
    if twenty_min_score:
        twenty_min_speed = (current_score - twenty_min_score[2]) * (60 / 20) / 10000
        result += f"\n20min*3时速: {twenty_min_speed:.1f}W"
    else:
        logger.debug("没有找到最近20分钟的得分数据。")

    return result

def fetch_user_info(cur, identifier, now, by_rank=False):

    if by_rank:
        cur.execute("""
            SELECT userId, name, rank, score, time 
            FROM skform 
            WHERE rank = ? 
            ORDER BY ABS(time - ?) 
            LIMIT 1
        """, (identifier, now))
        user_data = cur.fetchone()
        if not user_data:
            return None
        userId, name, rank, last_score, last_time = user_data
    else:
        cur.execute("""
            SELECT userId, name, rank, score, time 
            FROM skform 
            WHERE userId = ? 
            ORDER BY time DESC 
            LIMIT 1
        """, (identifier,))
        user_data = cur.fetchone()
        if not user_data:
            return None
        userId, name, rank, last_score, last_time = user_data

    score_changes = get_score_changes(cur, userId, now)
    return userId, name, rank, last_score, last_time, score_changes


def get_score_changes(cur, userId, now=None):
    time_threshold = now - HOUR_SECONDS
    cur.execute(""" 
        SELECT name, rank, score, time 
        FROM skform 
        WHERE userId = ? AND time >= ? 
        ORDER BY time ASC
    """, (userId, time_threshold))
    
    changes = cur.fetchall()
    if not changes:
        logger.debug(f"用户 {userId} 在最近一小时内没有得分变化。")
    return changes

def format_time(timestamp):
    local_time = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", local_time)

def get_player_rank(rank=None, userId=None):

    event_id = current_event()
    if event_id is None:
        return "目前没有活动进行中。"

    db_name = get_skdb_connection(event_id)
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()
        now = int(time.time())
        user_info = fetch_user_info(cur, rank or userId, now, by_rank=bool(rank))
        if user_info is None:
            return "未找到玩家的信息,可能是没进前100" if rank else "未找到该玩家的信息。"

        userId, name, rank, last_score, last_time, score_changes = user_info

        score_w = last_score / 10000
        result = f"玩家{name}的分数为{score_w:.3f}W，排名为{rank if rank is not None else '未知'}\n以上数据更新于: {format_time(last_time)}"

        if score_changes:
            result += calculate_score_info(score_changes, last_score, now)
        else:
            result += "\n未找到最近一小时的得分变化数据。"

        rank_diff_result = get_rank_differences(cur, rank, last_score, now)
        result += rank_diff_result

        return result

def get_rank_differences(cur, rank, score, now):
    result = ""
    next_rank = get_next_threshold(rank)
    prev_rank = get_previous_threshold(rank)

    if prev_rank is not None:
        prev_rank_score = cur.execute(''' 
                                      SELECT score FROM skform 
                                      WHERE rank = ? 
                                      ORDER BY ABS(time - ?) 
                                      LIMIT 1''', (prev_rank, now)).fetchone()
        if prev_rank_score:
            diff_lower = prev_rank_score[0] - score
            result += f"\n上一档排名 {prev_rank} 的分数为 {prev_rank_score[0] / 10000:.1f}W，相差 {diff_lower / 10000:.1f}W"

    if next_rank is not None:
        next_rank_score = cur.execute(''' 
                                      SELECT score FROM skform 
                                      WHERE rank = ? 
                                      ORDER BY ABS(time - ?) 
                                      LIMIT 1''', (next_rank, now)).fetchone()
        if next_rank_score:
            diff_upper = score - next_rank_score[0]
            result += f"\n下一档排名 {next_rank} 的分数为 {next_rank_score[0] / 10000:.1f}W，相差 {diff_upper / 10000:.1f}W"

    return result

def get_next_threshold(rank):
    return next((t for t in thresholds if t > rank), None)

def get_previous_threshold(rank):
    return next((t for t in reversed(thresholds) if t < rank), None)