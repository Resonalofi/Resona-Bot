import sqlite3
import os
from nonebot.log import logger

def initialize_database(event_id):
    if not os.path.exists("./skdata"):
        os.makedirs("./skdata")

    db_name = f"./skdata/{event_id}.db"
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()
        cur.execute(f'''
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

def update_database(data,event_id,data_time):
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