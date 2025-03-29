import json
import os
import time



now = time.time()

def wl_chapter(data_time):
    wlinfo_path = os.path.join(os.path.dirname(__file__), 'sekaisk', 'twdata', 'worldBlooms.json')
    
    try:
        with open(wlinfo_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {wlinfo_path}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from file: {wlinfo_path}")
        return None

    for info in data:
        if info['chapterStartAt'] < data_time * 1000 < info['aggregateAt']:
            print(info['gameCharacterId'])
            return info['gameCharacterId']
    
    print("No matching chapter found for the given data_time.")
    return None

# 示例调用
if __name__ == "__main__":
    data_time = now  # 示例时间戳
    game_character_id = wl_chapter(data_time)
    if game_character_id is not None:
        print(f"Found gameCharacterId: {game_character_id}")
    else:
        print("No gameCharacterId found.")