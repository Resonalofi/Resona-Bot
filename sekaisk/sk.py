import json 
import os
import sqlite3
import time
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

def get_player_rank(rank=None):
    event_id = current_event()
    if event_id is None:
        return "目前没有活动进行中。"

    db_name = f"./skdata/{event_id}.db"
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()
        if rank is None:
            return "请提供一个有效的排名。"

        try:
            now = int(time.time())  # 当前时间戳（秒）

            # 查询与当前时间戳最接近的玩家数据
            cur.execute("""
                SELECT userId, name, score, time 
                FROM skform 
                WHERE rank = ? 
                ORDER BY ABS(time - ?) 
                LIMIT 1
            """, (rank, now))

            player = cur.fetchone()

            if not player:
                return f"未找到排名为{rank}的玩家的信息。"

            user_id, name, score, last_time = player
            score_w = score / 10000
            result = f"玩家“{name}”的分数为{score_w:.3f}W，排名为{rank}"
            logger.debug(f"获取到的玩家信息: {player}")

            score_changes = get_score_changes(cur, user_id, now, HOUR_SECONDS)

            logger.debug(f"当前时间戳: {now}, 一小时前时间戳: {now - HOUR_SECONDS}")
            logger.debug(f"分数变化数据时间戳: {[sc[1] for sc in score_changes]}")

            # 计算时速
            # 查找最近一小时的得分变化
            last_hour_score = next((sc for sc in score_changes if sc[1] >= now - HOUR_SECONDS), None)
            logger.debug(f"找到的最近一小时分数: {last_hour_score}")

            if last_hour_score:
                hourly_score = score - last_hour_score[0]
                hourly_speed = hourly_score / HOUR_SECONDS / 10000
                result += f"\n时速: {hourly_speed:.1f}W"
            else:
                logger.debug("没有找到最近一小时的得分数据。")

            hour_count = sum(1 for i in range(1, len(score_changes)) if score_changes[i][0] > score_changes[i-1][0])
            result += f"\n本小时周回数: {hour_count}"

            if hour_count > 0 and last_hour_score:
                avg_score = (score - last_hour_score[0]) / 10000 / hour_count
                result += f"\n本小时平均单局pt: {avg_score:.3f}W"

            twenty_min_score = next((sc for sc in score_changes if sc[1] < now - TWENTY_MINUTES), None)
            if twenty_min_score:
                twenty_min_speed = (score - twenty_min_score[0]) * (60 / 20) / 10000
                result += f"\n20min*3时速: {twenty_min_speed:.1f}W"
            else:
                logger.debug("没有找到最近20分钟的得分数据。")

            result += get_rank_differences(cur, rank, score,now)

        except sqlite3.Error as e:
            logger.error(f"数据库错误: {e}")
            return "获取玩家信息时出错，请稍后再试。"

    return result

def get_rank_differences(cur, rank, score,now):
    result = ""
    next_rank = get_next_threshold(rank)
    prev_rank = get_previous_threshold(rank)

    if prev_rank is not None:
        prev_rank_score = cur.execute('''
                                      SELECT score FROM skform 
                                      WHERE rank = ? 
                                      ORDER BY ABS(time - ?) 
                                      LIMIT 1''', (prev_rank,now)).fetchone()
        if prev_rank_score:
            diff_lower = prev_rank_score[0] - score
            result += f"\n上一档排名 {prev_rank} 的分数为 {prev_rank_score[0] / 10000:.1f}W，相差 {diff_lower / 10000:.1f}W"

    if next_rank is not None:
        next_rank_score = cur.execute('''
                                      SELECT score FROM skform 
                                      WHERE rank = ? 
                                      ORDER BY ABS(time - ?) 
                                      LIMIT 1''', (next_rank,now)).fetchone()
        if next_rank_score:
            diff_upper = score - next_rank_score[0]
            result += f"\n下一档排名 {next_rank} 的分数为 {next_rank_score[0] / 10000:.1f}W，相差 {diff_upper / 10000:.1f}W"

    return result

def get_next_threshold(rank):
    return next((t for t in thresholds if t > rank), None)

def get_previous_threshold(rank):
    return next((t for t in reversed(thresholds) if t < rank), None)

def get_score_changes(cur, user_id, now, time_period):
    time_threshold = now - time_period  # 使用秒
    logger.debug(f"查询用户 {user_id} 从 {time_threshold} 到 {now} 的得分变化数据")
    
    sql_query = """ 
        SELECT score, time FROM skform 
        WHERE userId = ? AND time >= ?
        ORDER BY time ASC
    """
    #logger.debug(f"执行 SQL: {sql_query} | 参数: {user_id}, {time_threshold}")
    
    cur.execute(sql_query, (user_id, time_threshold))
    results = cur.fetchall()
    logger.debug(f"获取到的分数变化数据: {results}")  # 添加调试输出
    return results