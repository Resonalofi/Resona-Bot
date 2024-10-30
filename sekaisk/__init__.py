from sqlite3 import SQLITE_ERROR
from nonebot import get_plugin_config, on_command, get_driver
from .config import Config
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from .api_client import ApiClient
from .database import update_skdatabase,updata_binddatabase,get_bindid
from .sk import get_player_rank,current_event
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
    event_id = current_event()
    api_url = f"/user/{user_id}/event/{event_id}/ranking?rankingViewType=top100"
    
    while True:
      result = client.call_api(api_url)
      data_time = int(time.time())
      current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

      if result :
            logger.info(f"榜线更新成功，时间: {current_time}")
            client.save_json(result, "sk.json", indent=4)
            update_skdatabase(result,event_id,data_time)

            await asyncio.sleep(120) 



twsk = on_command("twsk", priority=1, block=True)

@twsk.handle()
async def twsk_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    command_part = raw_input[4:].strip()
    qqnum = event.user_id

    if not command_part:
        userId = get_bindid(qqnum)
        if userId is None:
            await twsk.finish("你还没有绑定，请输入 tw绑定 + id 进行绑定。")
        results = get_player_rank(None, userId)
        await twsk.finish(results)
    parts = command_part.split()

    if len(parts) == 1 and parts[0].isdigit():
        userId = int(parts[0])
        results = get_player_rank(None, userId)
        await twsk.finish(results)
    elif all(part.isdigit() for part in parts) and len(parts) <= 3:
       
        results = [get_player_rank(int(rank)) + "\n" for rank in parts]
        await twsk.finish("\n".join(results))
    else:
        await twsk.finish("请提供有效的排名或用户 ID，单次最多查询3个")



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