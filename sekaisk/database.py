import sqlite3
import os
import ujson as json
from nonebot.log import logger


characterdic = {
    1: "ick",
    2: "saki",
    3: "hnm",
    4: "shiho",
    5: "mnr",
    6: "hrk",
    7: "airi",
    8: "szk",
    9: "khn",
    10: "an",
    11: "akt",
    12: "toya",
    13: "tks",
    14: "emu",
    15: "nene",
    16: "rui",
    17: "knd",
    18: "mfy",
    19: "ena",
    20: "mzk",
    21: "miku",
    22: "rin",
    23: "len",
    24: "luka",
    25: "meiko",
    26: "kaito"
}

def value_to_key(value):
    for key, val in characterdic.items():
        if val == value:
            return key
    return None

def wl_chapter(data_time):
    wlinfo_path = os.path.join(os.path.dirname(__file__),'sekaisk','twdata','worldBlooms.json')
    with open(wlinfo_path,'r', encoding='utf-8') as f:
        data = json.load(f)
    for info in data:
        if info['chapterStartAt'] < data_time*1000 < info['aggregateAt']:
            return info['gameCharacterId']

def initialize_skdatabase(event_id,event_type):
    db_path = f"./skdata/{event_id}{event_type}.db"
    db_border = f"./skdata/{event_id}{event_type}border.db"
    if not os.path.exists("./skdata"):
        os.makedirs("./skdata")
    
    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skform (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId INTEGER,
                    score INTEGER,
                    rank INTEGER,
                    name TEXT,
                    time INTEGER
                )
            ''')
            conn.commit()

    if not os.path.exists(db_border):
        with sqlite3.connect(db_border) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skform (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId INTEGER,
                    score INTEGER,
                    rank INTEGER,
                    name TEXT,
                    time INTEGER
                )
            ''')
            conn.commit()

def initialize_wlskdatabase(event_id, event_type, character, ignore=False):
    db_fullpath = f"./skdata/{event_id}{event_type}.db"
    db_fullborder = f"./skdata/{event_id}{event_type}border.db"

    if not os.path.exists("./skdata"):
        os.makedirs("./skdata")

    if not os.path.exists(db_fullpath):
        with sqlite3.connect(db_fullpath) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skform (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId INTEGER,
                    score INTEGER,
                    rank INTEGER,
                    name TEXT,
                    time INTEGER
                )
            ''')
            conn.commit()

    if not os.path.exists(db_fullborder):
        with sqlite3.connect(db_fullborder) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skform (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId INTEGER,
                    score INTEGER,
                    rank INTEGER,
                    name TEXT,
                    time INTEGER
                )
            ''')
            conn.commit()

    if ignore is False:
            
            db_singlepath = f"./skdata/{event_id}{event_type}{characterdic[character]}.db"
            db_singleborder = f"./skdata/{event_id}{event_type}{characterdic[character]}border.db"

            if not os.path.exists(db_singlepath):
                with sqlite3.connect(db_singlepath) as conn:
                    cur = conn.cursor()
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS skform (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            userId INTEGER,
                            score INTEGER,
                            rank INTEGER,
                            name TEXT,
                            time INTEGER
                        )
                    ''')
                    conn.commit()

            if not os.path.exists(db_singleborder):
                with sqlite3.connect(db_singleborder) as conn:
                    cur = conn.cursor()
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS skform (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            userId INTEGER,
                            score INTEGER,
                            rank INTEGER,
                            name TEXT,
                            time INTEGER
                        )
                    ''')
                    conn.commit()

def get_skdb_connection(event_id, event_type, character=None, ignore=False):
    if event_type == "world_bloom":
        db_fullpath = f"./skdata/{event_id}{event_type}.db"
        db_fullborder = f"./skdata/{event_id}{event_type}border.db"
        
        if ignore is False:
            if character:
                character_value = characterdic.get(character)
                if character_value is None:
                    raise ValueError(f"Invalid character ID: {character}")
            else:
                raise ValueError("Character cannot be None")
            
            db_singlepath = f"./skdata/{event_id}{event_type}{character_value}.db"
            db_singleborder = f"./skdata/{event_id}{event_type}{character_value}border.db"

            if not os.path.exists(db_fullpath) or not os.path.exists(db_singlepath) or not os.path.exists(db_fullborder) or not os.path.exists(db_singleborder):
                initialize_wlskdatabase(event_id, event_type, character)
            
            return db_fullpath, db_singlepath, db_fullborder, db_singleborder
        else:
            if not os.path.exists(db_fullpath)  or not os.path.exists(db_fullborder):
                initialize_wlskdatabase(event_id, event_type, character,ignore=True)
            return db_fullpath, db_fullborder
    else:
        db_path = f"./skdata/{event_id}{event_type}.db"
        db_border = f"./skdata/{event_id}{event_type}border.db"
        if not os.path.exists(db_path) or not os.path.exists(db_border):
            initialize_skdatabase(event_id, event_type)
        return db_path, db_border

def update_skdatabase(data,event_id,event_type,data_time):
    extracted_data = []
    for ranking in data.get('rankings', []):
        user_id = ranking.get('userId')
        score = ranking.get('score')
        rank = ranking.get('rank')
        name = ranking.get('name')
        extracted_data.append((user_id, score, rank, name, data_time))
    db_path , _ = get_skdb_connection(event_id,event_type)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', extracted_data)
        conn.commit()

def update_wlskdatabase(data, event_id, event_type, data_time):
    try:
        full_data = []
        rankings = data.get('rankings', [])
        for ranking in rankings:
                user_id = ranking.get('userId')
                score = ranking.get('score')
                rank = ranking.get('rank')
                name = ranking.get('name')
                full_data.append((user_id, score, rank, name, data_time))

        db_fullpath, _ = get_skdb_connection(event_id, event_type, character=None,ignore=True)
        with sqlite3.connect(db_fullpath) as conn:
            cur = conn.cursor()
            cur.executemany('''
                INSERT INTO skform (userId, score, rank, name, time) 
                VALUES (?, ?, ?, ?, ?)
            ''', full_data)
            conn.commit()
            
        user_world_bloom_chapter_rankings = data.get('userWorldBloomChapterRankings', [])
        if not user_world_bloom_chapter_rankings:
            logger.info("No userWorldBloomChapterRankings found. Skipping...")
            return

        for chapter_data in user_world_bloom_chapter_rankings:
            game_character_id = chapter_data.get('gameCharacterId')
            rankings = chapter_data.get('rankings', [])

            if not rankings:
                logger.info(f"No rankings found for gameCharacterId: {game_character_id}. Skipping...")
                continue

            single_data = []
            for ranking in rankings:
                user_id = ranking.get('userId')
                score = ranking.get('score')
                rank = ranking.get('rank')
                name = ranking.get('name')
                single_data.append((user_id, score, rank, name, data_time))

            if single_data:
                _, db_singlepath, _, _ = get_skdb_connection(event_id, event_type, character=game_character_id)
                with sqlite3.connect(db_singlepath) as conn:
                    cur = conn.cursor()
                    cur.executemany('''
                        INSERT INTO skform (userId, score, rank, name, time) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', single_data)
                    conn.commit()
    except Exception as e:
        logger.info(f"Error processing data. Error: {e}")

def update_borderdatabase(data,event_id,event_type,data_time):
    extracted_data = []
    for ranking in data.get('borderRankings', []):
        user_id = ranking.get('userId')
        score = ranking.get('score')
        rank = ranking.get('rank')
        name = ranking.get('name')
        extracted_data.append((user_id, score, rank, name, data_time))
    _ , db_borderpath = get_skdb_connection(event_id,event_type)
    with sqlite3.connect(db_borderpath) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', extracted_data)
        conn.commit()

def update_wlborder_database(data, event_id, event_type, data_time):
    try:
        full_data = []
        for ranking in data.get('borderRankings', []):
            user_id = ranking.get('userId')
            score = ranking.get('score')
            rank = ranking.get('rank')
            name = ranking.get('name')
            full_data.append((user_id, score, rank, name, data_time))

        _, db_fullborder = get_skdb_connection(event_id, event_type, character=None,ignore=True)
        with sqlite3.connect(db_fullborder) as conn:
            cur = conn.cursor()
            cur.executemany('''
                INSERT INTO skform (userId, score, rank, name, time) 
                VALUES (?, ?, ?, ?, ?)
            ''', full_data)
            conn.commit()

        user_world_bloom_chapter_Borders = data.get('userWorldBloomChapterRankingBorders', [])
        if not user_world_bloom_chapter_Borders:
            logger.info("No userworldbloomchapterBorders found. Skipping...")
            return
        
        for chapter_data in user_world_bloom_chapter_Borders:
            game_character_id = chapter_data.get('gameCharacterId')
            rankings = chapter_data.get('borderRankings', [])

            if not rankings:
                logger.info(f"No borders found for gameCharacterId: {game_character_id}. Skipping...")
                continue

            single_data = []
            for ranking in rankings:
                user_id = ranking.get('userId')
                score = ranking.get('score')
                rank = ranking.get('rank')
                name = ranking.get('name')
                single_data.append((user_id, score, rank, name, data_time))

            if single_data:
               _, _, _, db_singleborder = get_skdb_connection(event_id, event_type, character=game_character_id)
               with sqlite3.connect(db_singleborder) as conn:
                cur = conn.cursor()
                cur.executemany('''
                    INSERT INTO skform (userId, score, rank, name, time) 
                    VALUES (?, ?, ?, ?, ?)
                ''', single_data)
                conn.commit()

    except Exception as e:
        logger.debug(f"Error processing data. Error: {e}")

def initialize_binddatabase():

    binddata_path = "./skdata/binddata"
    if not os.path.exists(binddata_path):
        os.makedirs(binddata_path)

    db_path = f"{binddata_path}/bind.db"

    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bindform (
                    userId INTEGER,
                    qqnum INTEGER PRIMARY KEY,
                    private INTEGER DEFAULT 0,
                    ban INTEGER DEFAULT 0
                        
                )
            ''')
            conn.commit()

def get_binddb_connection():

    db_path = f"./skdata/binddata/bind.db"
    
    if not os.path.exists(db_path):
        initialize_binddatabase()  
    
    return db_path

def update_binddatabase(userId=None, qqnum=None, private=None, ban=None): 
    db_path = get_binddb_connection()

    if qqnum is None:
        logger.info("Error: qqnum must be provided to identify the row.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM bindform WHERE qqnum = ?", (qqnum,))
            exists = cur.fetchone()

            if exists:
                updates = []
                params = []

                if userId is not None:
                    updates.append("userId = ?")
                    params.append(userId)
                if private is not None:
                    updates.append("private = ?")
                    params.append(private)
                if ban is not None:
                    updates.append("ban = ?")
                    params.append(ban)

                if updates:
                    sql = f"UPDATE bindform SET {', '.join(updates)} WHERE qqnum = ?"
                    params.append(qqnum)
                    cur.execute(sql, tuple(params))
            else:
                cur.execute('''
                    INSERT INTO bindform (userId, qqnum, private, ban) 
                    VALUES (?, ?, ?, ?)
                ''', (userId, qqnum, private or 0, ban or 0))

            conn.commit()
    except Exception as e:
        logger.info(f"Error updating or inserting database: {e}")

def get_bindid(qqnum):
    db_path = get_binddb_connection()

    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, private, ban FROM bindform WHERE qqnum = ?", (qqnum,))
            result = cur.fetchone()  
            if result:
                userId = result[0]  
                private = result[1]
                ban = result[2]
                return userId, private, ban          
            else:
                return None, 0 , 0  
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        pass