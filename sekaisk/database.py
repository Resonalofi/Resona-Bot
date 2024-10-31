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

def initialize_wlskdatabase(event_id,event_type,character):
    db_fullpath = f"./skdata/{event_id}{event_type}.db"
    db_singlepath = f"./skdata/{event_id}{event_type}{characterdic[character]}.db"
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

def get_skdb_connection(event_id,event_type,character=None):
    if event_type == "world_bloom":
       db_fullpath = f"./skdata/{event_id}{event_type}.db"
       db_singlepath = f"./skdata/{event_id}{event_type}{characterdic[character]}.db"
       if not os.path.exists(db_fullpath) or not os.path.exists(db_singlepath):
           initialize_wlskdatabase(event_id,event_type,character) 
       return db_fullpath,db_singlepath
    else:
        db_path = f"./skdata/{event_id}{event_type}.db"
        if not os.path.exists(db_path):
            initialize_skdatabase(event_id,event_type)
        return db_path

def update_skdatabase(data,event_id,event_type,data_time):
    extracted_data = []
    for ranking in data.get('rankings', []):
        user_id = ranking.get('userId')
        score = ranking.get('score')
        rank = ranking.get('rank')
        name = ranking.get('name')
        extracted_data.append((user_id, score, rank, name, data_time))
    db_path = get_skdb_connection(event_id,event_type)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', extracted_data)
        conn.commit()

def update_wlskdatabase(data,event_id,event_type,data_time):
    full_data = []
    for ranking in data.get('rankings', []):
        user_id = ranking.get('userId')
        score = ranking.get('score')
        rank = ranking.get('rank')
        name = ranking.get('name')
        character = ranking.get('gameCharacterId')
        full_data.append((user_id, score, rank, name, data_time))
    db_fullpath, _ = get_skdb_connection(event_id,event_type,character)
    with sqlite3.connect(db_fullpath) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', full_data)
        conn.commit()
    single_data=[]
    current_character_id=wl_chapter(data_time)
    for ChapterRanking in data.get('userWorldBloomChapterRankings', []):
        user_id = ChapterRanking.get('userId')
        score = ChapterRanking.get('score')
        rank = ChapterRanking.get('rank')
        name = ChapterRanking.get('name')
        character = ChapterRanking.get('gameCharacterId')
        if character == current_character_id:
           single_data.append((user_id, score, rank, name, data_time))
    _, db_singlepath = get_skdb_connection(event_id,event_type,character)
    with sqlite3.connect(db_singlepath) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', single_data)
        conn.commit()

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
                    qqnum INTEGER PRIMARY KEY
                )
            ''')
            conn.commit()

def get_binddb_connection():

    db_path = f"./skdata/binddata/bind.db"
    
    if not os.path.exists(db_path):
        initialize_binddatabase()  
    
    return db_path

def updata_binddatabase(userId,qqunm=None):
    db_path = get_binddb_connection()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(f'''
            INSERT INTO bindform (userId, qqnum) VALUES (?, ?)
            ON CONFLICT(qqnum) DO UPDATE SET userId = excluded.userId;
        ''', (userId, qqunm))
        conn.commit()

def get_bindid(qqnum): 
    db_path = get_binddb_connection()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM bindform WHERE qqnum = ?", (qqnum,))
        result = cur.fetchone()  
        logger.debug(f"查询结果: {result}")

        if result:
            return result[0]  
        else:
            return None 
