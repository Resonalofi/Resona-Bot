import sqlite3
import os
from nonebot.log import logger

def initialize_skdatabase(event_id):
    db_path = f"./skdata/{event_id}.db"
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

def get_skdb_connection(event_id):
    db_path = f"./skdata/{event_id}.db"
    if not os.path.exists(db_path):
        initialize_skdatabase(event_id) 
    return db_path

def update_skdatabase(data,event_id,data_time):
    extracted_data = []
    for ranking in data.get('rankings', []):
        user_id = ranking.get('userId')
        score = ranking.get('score')
        rank = ranking.get('rank')
        name = ranking.get('name')
        
        extracted_data.append((user_id, score, rank, name, data_time))
    db_name = f"./skdata/{event_id}.db"
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()
        cur.executemany('''
            INSERT INTO skform (userId, score, rank, name, time) 
            VALUES (?, ?, ?, ?, ?)
        ''', extracted_data)
        conn.commit()

def get_player_history(event_id, user_id):
    db_name = f"./skdata/{event_id}.db"
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, score, rank FROM skform WHERE userId = ? ORDER BY time DESC LIMIT 1", (user_id,))
        return cur.fetchone()
    
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
