import re
from nonebot import get_plugin_config, on_command, get_driver
from .config import Config
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from .api_client import ApiClient
from .database import update_skdatabase,updata_binddatabase,update_wlskdatabase,value_to_key,get_bindid
from .sk import current_event,get_player_rank,get_player_singlerank
import asyncio
import time


__plugin_meta__ = PluginMetadata(
    name="sekaisk",
    description="",
    usage="",
    config=Config,
)
config = get_plugin_config(Config)
superusers = get_driver().config.superusers


refresh_sk = on_command("rsk", priority=1, block=True, permission=SUPERUSER)

@refresh_sk.handle()
async def handle_refresh_sk(bot: Bot, event: Event):
    user_id = "7428837976920283959"
    client = ApiClient(user_id)
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']
        event_announce = event_info['rankannounce']
        api_url = f"/user/{user_id}/event/{event_id}/ranking?rankingViewType=top100"

        async def refresh_task():
            while True:
                now = int(time.time() * 1000)
                if now > (event_announce + 120000):
                    logger.info("榜线已公示，停止获取榜线")
                    break
                result = client.call_api(api_url)
                data_time = int(time.time())
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                if result:
                    logger.info(f"榜线更新成功，时间: {current_time}")
                    client.save_json(result, f"{event_id}{event_type}sk.json", indent=4)
                    if event_type in ["marathon", "cheerful_carnival"]:
                        update_skdatabase(result, event_id, event_type, data_time)
                    elif event_type == "world_bloom":
                        update_wlskdatabase(result, event_id, event_type, data_time)

                await asyncio.sleep(90)

        task = asyncio.create_task(refresh_task())
        await bot.send(event, "开始刷新榜线...")
    else:
        await bot.send(event, "当前没有进行中的活动")


twsk = on_command("twsk", priority=1, block=True)

@twsk.handle()
async def twsk_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    command_part = raw_input[4:].strip()
    qqnum = event.user_id

    if not command_part:
        userId = get_bindid(qqnum)
        if userId is None:
            await twsk.finish("你还没有绑定，请输入 tw 绑定 + id 进行绑定")
        results = get_player_rank(userId=userId)
        await twsk.finish(results)

    parts = command_part.split()
    #logger.info(f"Parsed parts: {parts}")

    if all(part.isdigit() for part in parts) and len(parts) <= 3:
        results = [get_player_rank(rank=int(rank)) + "\n" for rank in parts]
        await twsk.finish("\n".join(results))
    else:
        await twsk.finish("请提供有效的排名，单次最多查询3个")





twwl = on_command("twwl", priority=1, block=True)

@twwl.handle()
async def tw_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    
    match = re.match(r'^(\d+(?:\s+\d+)*)\s+(\w+)$', raw_input[4:].strip())
    if match:
        ranks_str, character_value = match.groups()
        ranks = [int(rank) for rank in ranks_str.split()]
        if len(ranks) > 3:
            await bot.send(event, "最多只能查询3个位次")
            return
        
        character_id = value_to_key(character_value)
        if character_id is None:
            await bot.send(event, "查不到角色哦，暂时仅支持罗马音缩写")
            return
        
        results = []
        for rank in ranks:
            result = get_player_singlerank(rank=rank,character_id=character_id)
            results.append(result)
        
        await bot.send(event, "\n".join(results))
    else:
        character_value = raw_input[4:].strip()
        character_id = value_to_key(character_value)
        if character_id is None:
            await bot.send(event, "查不到角色哦，暂时仅支持罗马音缩写")
            return
        
        qqnum = event.user_id
        userId = get_bindid(qqnum)
        if userId is None:
            await bot.send(event, "查不到哦，可能是没绑定")
            return
        
        result = get_player_singlerank(userId=userId,character_id=character_id)
        await bot.send(event, result)



twbind = on_command("tw绑定", priority=1, block=True)

@twbind.handle()
async def twbind_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    id_part = raw_input[4:].strip()
    qqnum = int(event.user_id)

    if not id_part:
        await twbind.finish("请输入正确的ID")

    try:
        updata_binddatabase(id_part, qqnum)
    except Exception as e:
        await bot.send(event, f"绑定失败，可能是数据库连接问题: {e}")
    else:
        await bot.send(event, "绑定成功")