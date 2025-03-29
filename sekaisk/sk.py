import ujson as json
import sqlite3
import time
from .database import get_skdb_connection,wl_chapter
from nonebot.log import logger

thresholds = [1, 2, 3, 5, 7, 10, 20, 30, 40, 50, 70, 100]
borders = [100, 200, 300, 400, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 10000, 20000, 30000, 40000, 50000, 100000]
HOUR_SECONDS = 3600
TWENTY_MINUTES = 1200

def current_event():

    with open('./twmasterdata/events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    now = int(time.time() * 1000)

    for event in data:
        start_at = event['startAt']
        ranking_announce_at = event['rankingAnnounceAt']
        closed_at = event['closedAt']

        if now < start_at:
            event_status = "not_start"
        elif start_at <= now < ranking_announce_at + 120000:
            event_status = "going"
        elif ranking_announce_at <= now < closed_at:
            event_status = "finished"
        else:
            event_status = "ended"

        if start_at <= now < closed_at:
            return {
                'id': event['id'],
                'eventType': event['eventType'],
                'rankannounce': event['rankingAnnounceAt'],
                'eventStatus': event_status
            }
        
    return None

def calculate_finish(now,current=True):
    if not current:
        return "当前章节已结束。"
    event_info = current_event()
    if not event_info:
        return "目前没有活动进行中。"
    
    event_type = event_info['eventType']
    ms_now = now * 1000 

    if event_type == "world_bloom":
        with open('./twmasterdata/worldBlooms.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for info in data:
            if info['chapterStartAt'] < ms_now < info['aggregateAt']:
                aggregate_at = info['aggregateAt']
                time_difference = aggregate_at - ms_now  
                return time_difference / 1000 
    
    elif event_type == "marathon" or event_type == "cheerful_carnival":
        with open('./twmasterdata/events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for info in data:
            if info['chapterStartAt'] < ms_now < info['aggregateAt']:
                aggregate_at = info['aggregateAt']
                time_difference = aggregate_at - ms_now  
                return time_difference / 1000  
    else:
        return "未找到匹配的活动信息"

def get_dangours_speed(userId=None, character_id=None):
    now = int(time.time())
    event_info = current_event()
    if not event_info:
        return "目前没有活动进行中"
    
    event_id = event_info['id']
    event_type = event_info['eventType']

    if event_type == "world_bloom":
        character = character_id
        _, db_singlepath, _, _ = get_skdb_connection(event_id, event_type, character)
        with sqlite3.connect(db_singlepath) as conn:
            cur = conn.cursor()
            user_info_self = fetch_user_info(cur=cur, rank=userId, now=now, by_rank=False)
            user_info_100 = fetch_user_info(cur=cur, rank=100, now=now, by_rank=True)
            
            if user_info_self is None:
                return "未找到你的wl信息，可能是没进前单人榜100" if userId else "未找到该玩家的wl信息，可能是没进前100"
            
            userId_self, name_self, rank_self, score_self, last_time_self , _ = user_info_self

            if user_info_100 is None:
                return "未找到第100位的wl信息，可能是有bug，请提醒bot主" if rank_self else "未找到该玩家的wl信息，可能是没进前100"
            
            userId_100, name_100, rank_100, score_100, last_time_100 , _ = user_info_100

            time_difference_stamp = calculate_finish(now)
            time_difference = time_difference_stamp / 3600

            # logger.debug(f"time_difference is {time_difference}")
            score_difference = (score_self - score_100) / 10000
            # logger.debug(f"score_difference is {score_difference}")

            if time_difference > 0:
                speed = score_difference / time_difference
                # logger.debug(f"speed is {speed}")
                time_remaining_str = format_time_remaining(time_difference_stamp)
                return f"你当前排名为{rank_self}，分数{score_self/10000:.4f}w\n排名第100的{name_100}的分数是{score_100/10000:.3f}w\n到本章节结束还有{time_remaining_str}，第100名追到你所在位次所需时速约为{speed:.2f}w"
            else:
                return "无法计算速度"
    else:
        return "仅worldlink单榜进行中可使用"

def calculate_score_info(score_changes, current_score, now):
    result = ""
    last_hour_scores = []
    seen_scores = set()

    for sc in reversed(score_changes):
        if sc[3] >= now - HOUR_SECONDS and sc[2] not in seen_scores:
            last_hour_scores.append(sc)
            seen_scores.add(sc[2])
        elif sc[3] < now - HOUR_SECONDS:
            break
    last_hour_scores.reverse()

    if last_hour_scores:
        first_last_hour_score = last_hour_scores[0]
        hourly_score = current_score - first_last_hour_score[2]       
        hourly_speed = hourly_score / 10000
        result += f"\n时速: {hourly_speed:.2f}W"

        hour_count = sum(1 for i in range(1, len(last_hour_scores)) if last_hour_scores[i][2] > last_hour_scores[i-1][2])
        result += f"\n一小时周回: {hour_count}"

        if hour_count > 0:
            avg_score = hourly_score / hour_count / 10000
            result += f"\n一小时平均单局pt: {avg_score:.3f}W"

            if len(last_hour_scores) > 1:
                last_game_score_change = last_hour_scores[-1]
                second_last_game_score_change = last_hour_scores[-2]
                last_game_score = last_game_score_change[2] - second_last_game_score_change[2]
                result += f"\n最近一局pt: {last_game_score / 10000:.3f}W"
            else:
                result += "\n最近一局pt: 无数据"

    twenty_min_score = next((sc for sc in score_changes if sc[3] >= now - TWENTY_MINUTES), None)
    if twenty_min_score:
        twenty_min_speed = (current_score - twenty_min_score[2]) * (60 / 20) / 10000
        result += f"\n20min*3时速: {twenty_min_speed:.2f}W"
    else:
        logger.debug("没有最近20分钟的得分数据。")

    return result

def fetch_user_info(cur, rank, now, by_rank=False, mode= "normal"):
    #logger.info(f"by_rank={by_rank}")
    if by_rank:
        cur.execute("""
            SELECT userId, name, rank, score, time 
            FROM skform 
            WHERE rank = ? 
            ORDER BY ABS(time - ?) 
            LIMIT 1
        """, (rank, now))
        user_data = cur.fetchone()
        #logger.info(f"userdata={user_data}")
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
        """, (rank,))
        user_data = cur.fetchone()
        #logger.info(f"by_rank={user_data}")
        if not user_data:
            return None
        userId, name, rank, last_score, last_time = user_data

    score_changes = get_score_changes(cur, userId, now ,mode)
    # logger.debug(f"score_changes={score_changes}")
    return userId, name, rank, last_score, last_time, score_changes

def get_score_changes(cur, userId, now ,mode):

    if mode == "normal":
       time_threshold = now - HOUR_SECONDS
    elif mode == "stop":
       time_threshold = 0

    cur.execute(""" 
        SELECT name, rank, score, time 
        FROM skform 
        WHERE userId = ? AND time >= ? 
        ORDER BY time ASC
    """, (userId, time_threshold))
    
    changes = cur.fetchall()
    if not changes:
        pass
        # logger.debug(f"玩家 {userId} 在最近一小时内没有得分变化。")
    return changes

def format_time(timestamp):
    local_time = time.localtime(timestamp)
    return time.strftime("%m-%d %H:%M:%S", local_time)

def format_time_remaining(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    
    time_parts = []
    if days > 0:
        time_parts.append(f" {int(days)}天")
    if hours > 0 or days > 0:
        time_parts.append(f"{int(hours)}小时")
    if minutes > 0 or hours > 0 or days > 0:
        time_parts.append(f"{int(minutes)}分钟")
    
    return " ".join(time_parts)

def get_player_rank(rank=None, userId=None):
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']
        event_status = event_info['eventStatus']

        if event_id is None:
            return "目前没有活动进行中。"
        
        if event_type == "world_bloom":
            now = int(time.time())
            db_fullpath, _ = get_skdb_connection(event_id, event_type, ignore=True)
            with sqlite3.connect(db_fullpath) as conn:
                cur = conn.cursor()
                user_info = fetch_user_info(cur, rank or userId, now, by_rank=bool(rank))
                if user_info is None:
                    return "未找到玩家的信息，档线查询请用tw线" if rank else "未找到该玩家的信息,可能是没进前100"
                
                userId, name, rank, last_score, last_time, score_changes = user_info

                score_w = last_score / 10000

                if last_time < now - 600 and event_status == 'going':
                    result = f"{name}已于：{format_time(last_time)}离开top100"
                    return result
                else:
                   result = f"{name}\n分数: {score_w:.4f}W，排名{rank if rank is not None else '未知'}"

                if score_changes:
                    result += calculate_score_info(score_changes, last_score, now)
                else:
                    result += "\n未找到最近一小时的得分变化数据。"

                rank_diff_result = get_rank_differences(cur, rank, last_score, now)
                result += rank_diff_result

                return result
        elif event_type == "marathon" or event_type == "cheerful_carnival":
            db_path , _ = get_skdb_connection(event_id, event_type)
            #logger.info(f"Database path: {db_path}")
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                now = int(time.time())
                user_info = fetch_user_info(cur, rank or userId, now, by_rank=bool(rank))
                #logger.info(f"{user_info}")
                if user_info is None:
                    return "未找到玩家的信息，非前100查询请用tw线" if rank else "未找到该玩家的信息,可能是没进前100"
                
                userId, name, rank, last_score, last_time, score_changes = user_info

                score_w = last_score / 10000
                if last_time < now - 600 and event_status == 'going':
                    result = f"{name}已于：{format_time(last_time)}离开top100"
                    return result
                else:
                   result = f"{name}\n分数: {score_w:.4f}W，排名{rank if rank is not None else '未知'}"

                if score_changes:
                    result += calculate_score_info(score_changes, last_score, now)
                else:
                    result += "\n未找到最近一小时的得分变化数据。"

                rank_diff_result = get_rank_differences(cur, rank, last_score, now)
                result += rank_diff_result

                return result
        else: 
            return "活动比对错误，请检查后台"
    else:
        return "未获取到活动信息。"

def get_player_singlerank(rank=None, userId=None, character_id=None):
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']
        event_status = event_info['eventStatus']
        
        if event_id is None:
            return "目前没有活动进行中。"
        
        if event_type == "world_bloom":
            character = character_id
            
            _ , db_singlepath , _ , _= get_skdb_connection(event_id, event_type, character)
            with sqlite3.connect(db_singlepath) as conn:
                cur = conn.cursor()
                now = int(time.time())
                user_info = fetch_user_info(cur, rank or userId, now, by_rank=bool(rank))
                if user_info is None:
                    return "未找到玩家的信息，非前100查询请用wl线+角色名" if rank else "未找到该玩家的wl信息，可能是没进前100"
                
                userId, name, rank, last_score, last_time, score_changes = user_info

                score_w = last_score / 10000
                
                if last_time < now - 600 and event_status == 'going':
                    result = f"{name}已于：{format_time(last_time)}离开top100"
                    return result
                else:
                   result = f"{name}\n分数: {score_w:.4f}W，排名{rank if rank is not None else '未知'}"

                if score_changes:
                    result += calculate_score_info(score_changes, last_score, now)
                else:
                    result += "\n未找到最近一小时的得分变化数据。"

                rank_diff_result = get_rank_differences(cur, rank, last_score, now)
                result += rank_diff_result

                return result
        else: 
            return "当前不是worldlink活动"
    else:
        return "未获取到活动信息。"

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
            result += f"\n{prev_rank}位分数: {prev_rank_score[0] / 10000:.1f}W，↑ {diff_lower / 10000:.1f}W"

    if next_rank is not None:
        next_rank_score = cur.execute(''' 
                                      SELECT score FROM skform 
                                      WHERE rank = ? 
                                      ORDER BY ABS(time - ?) 
                                      LIMIT 1''', (next_rank, now)).fetchone()
        if next_rank_score:
            diff_upper = score - next_rank_score[0]
            result += f"\n{next_rank}位分数: {next_rank_score[0] / 10000:.1f}W，↓ {diff_upper / 10000:.1f}W"

    return result

def get_next_threshold(rank):
    return next((t for t in thresholds if t > rank), None)

def get_previous_threshold(rank):
    return next((t for t in reversed(thresholds) if t < rank), None)

def get_border_scores(character_id=None):
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']

        if event_id is None:
            return "没有活动进行中" , None
        if event_type == "world_bloom" and character_id is None:
            _, db_fullborder = get_skdb_connection(event_id, event_type,ignore=True)
            db_path = db_fullborder
        elif event_type == "world_bloom" and character_id:
            _, _, _, db_singleborder = get_skdb_connection(event_id, event_type,character=character_id)
            db_path = db_singleborder
        else:
            _, db_borderpath = get_skdb_connection(event_id, event_type)
            db_path = db_borderpath
        
        # logger.info(f"{db_path}")
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            now = int(time.time())
            result = "各档线分数线如下:\n"
            for border in borders:
                cur.execute('''
                    SELECT score,time
                    FROM skform 
                    WHERE rank = ? 
                    ORDER BY ABS(time - ?) 
                    LIMIT 1
                ''', (border, now))
                score_data = cur.fetchone()
                # logger.info(f"{score_data}")
                if score_data:
                    score, timestamp = score_data
                    last_time = format_time(timestamp)
                    score_str = f"{score / 10000:.1f}W"
                    result += f"{border}: {score_str} \n"
                else:
                    result += f"{border}: -\n"
            return result,last_time
    else:
        return "未获取到活动信息。", None 
    
def get_border_speed(character_id=None):
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']

        if event_id is None:
            return "目前没有活动进行中。", None

        if event_type == "world_bloom" and character_id is None:
            _, db_fullborder = get_skdb_connection(event_id, event_type, ignore=True)
            db_path = db_fullborder
        elif event_type == "world_bloom" and character_id:
            _, _, _, db_singleborder = get_skdb_connection(event_id, event_type, character=character_id)
            db_path = db_singleborder
        else:
            _, db_borderpath = get_skdb_connection(event_id, event_type)
            db_path = db_borderpath
        # logger.info(f"{db_path}")
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            now = int(time.time())
            one_hour_ago = now - HOUR_SECONDS
            result = "各档线时速如下:\n"
            for border in borders:
                cur.execute('''
                    SELECT score, time
                    FROM skform 
                    WHERE rank = ? AND time BETWEEN ? AND ?
                    ORDER BY time ASC
                ''', (border, one_hour_ago, now))
                score_data = cur.fetchall()

                if len(score_data) >= 2:
                    first_score, _ = score_data[0]
                    last_score, _ = score_data[-1]
                    score_diff = last_score - first_score
                    speed = score_diff
                    speed_str = f"{speed / 10000:.3f}w"
                    result += f"{border}: {speed_str} \n"
                else:
                    result += f"{border}: -\n"
            last_time = format_time(now)
            return result, last_time
    else:
        return "未获取到活动信息。", None

def timeremain(seconds, detailed=True):

    if seconds < 0:
        return "已结束"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if detailed:
        return f"{hours}小时{minutes}分钟{seconds}秒" if hours > 0 else f"{minutes}分钟{seconds}秒"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
def get_stop_time(rank=None, userId=None, character=None):
    event_info = current_event()
    now = int(time.time())
    is_draw = False
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']

        if event_id is None:
            return "目前没有活动进行中", is_draw

        if event_type == "marathon" or event_type == "cheerful_carnival":
            db_path, _ = get_skdb_connection(event_id, event_type)
        elif event_type == "world_bloom" and character:
            _, db_singlepath, _, _ = get_skdb_connection(event_id, event_type, character)
            db_path = db_singlepath
        elif event_type == "world_bloom" and character is None:
            db_path, _ = get_skdb_connection(event_id, event_type, ignore=True)
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()

            user_data = fetch_user_info(cur, rank or userId, now, mode="stop", by_rank=bool(rank))

            if not user_data:
                return "未找到对应玩家的信息",is_draw

            userId, name, user_rank, last_score, last_time, score_records = user_data
            # 计算停车时间段
            stop_segments = []

            if score_records:
                prev_score = score_records[0][2]  # 初始分数
                prev_time = score_records[0][3]   # 初始时间戳

                for record in score_records[1:]:
                    score = record[2]       # 当前分数
                    timestamp = record[3]  # 当前时间戳

                    time_gap = timestamp - prev_time

                    if score == prev_score:
                        if time_gap > 300:  # 分数未变间隔超过5分钟
                            if stop_segments and stop_segments[-1]["start"] == prev_time:
                                stop_segments[-1]["end"] = timestamp  # 合并连续停车段
                            else:
                                stop_segments.append({"start": prev_time, "end": timestamp})
                    else:
                        prev_time = timestamp
                    # 更新score
                    prev_score = score

            if stop_segments:
                result = f"第{user_rank}名 {name}的分数为{last_score} 停车时间段:\n"
                total_stop_time = 0
                for i, segment in enumerate(stop_segments, 1):
                    start_time = format_time(segment["start"])
                    end_time = format_time(segment["end"])
                    duration = segment["end"] - segment["start"]
                    total_stop_time += duration
                    result += f"{i}. {start_time} ~ {end_time} ({timeremain(duration, False)})\n"
                is_draw=True
                result += f"总停车时间：{timeremain(total_stop_time, True)}\n仅记录在前100名内的数据。"
            else:
                result = f"{name}\n未停车，仅记录在前100名内的数据。"

            return result , is_draw
    else:
        return "未获取到活动信息" , is_draw