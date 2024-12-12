import re
import os
import shutil
from nonebot import get_plugin_config, on_command, get_driver
from .config import Config
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent,MessageSegment
from .twmusicleak import twmusicleak
from .api_client import ApiClient
from .pjskprofile import pjskprofile
from .database import update_skdatabase,update_binddatabase,update_wlskdatabase,update_borderdatabase,update_wlborder_database,value_to_key,get_bindid
from .sk import current_event,get_player_rank,get_player_singlerank,get_border_scores,get_dangours_speed,get_border_speed
from PIL import Image, ImageFont, ImageDraw
from .texttoimg import t2i
from pathlib import Path
import asyncio
import time


__plugin_meta__ = PluginMetadata(
    name="sekaisk",
    description="",
    usage="",
    config=Config,
)
config = get_plugin_config(Config)
superusers = get_driver()


refresh_sk = on_command("rsk", priority=1, block=True, permission=SUPERUSER)

@refresh_sk.handle()
async def handle_refresh_sk(bot: Bot, event: Event):
    admin = config.admin
    user_id = config.user_id
    client = ApiClient(user_id)
    event_info = current_event()
    if event_info:
        event_id = event_info['id']
        event_type = event_info['eventType']
        event_announce = event_info['rankannounce']
        await bot.send(event,message=f"开始获取榜线")

        async def refresh_task_sk():
            while True:
                now = int(time.time() * 1000)
                if now > (event_announce + 120000):
                    logger.info("榜线已公示，停止获取榜线")
                    break

                for retry in range(3):
                    result = client.call_api(f"/user/{user_id}/event/{event_id}/ranking?rankingViewType=top100")
                    data_time = int(time.time())
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                    if result:
                        logger.info(f"榜线更新成功，时间: {current_time}")
                        if event_type in ["marathon", "cheerful_carnival"]:
                            update_skdatabase(result, event_id, event_type, data_time)
                        elif event_type == "world_bloom":
                            update_wlskdatabase(result, event_id, event_type, data_time)
                        break
                    else:
                        logger.debug(f"获取榜线失败，尝试 {retry + 1}/3，当前时间: {current_time}")
                        await asyncio.sleep(10)
                else:
                    try:
                        await bot.send_private_msg(user_id=admin, message=f"获取T100榜线失败，当前时间: {current_time}")
                    except Exception as e:
                        pass

                await asyncio.sleep(57)

        async def refresh_task_border():
            while True:
                now = int(time.time() * 1000)
                if now > (event_announce + 310000):
                    logger.info("榜线已公示，停止获取榜线")
                    break

                for retry in range(3):
                    result = client.call_api(f"/event/{event_id}/ranking-border")
                    data_time = int(time.time())
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                    if result:
                        logger.info(f"整百更新成功，时间: {current_time}")
                        client.save_json(result, f"{event_id}{event_type}border_sk.json", indent=4)
                        if event_type in ["marathon", "cheerful_carnival"]:
                            update_borderdatabase(result, event_id, event_type, data_time)
                        elif event_type == "world_bloom":
                            update_wlborder_database(result, event_id, event_type, data_time)
                        break
                    else:
                        logger.debug(f"获取整百榜线失败，尝试 {retry + 1}/3，当前时间: {current_time}")
                        await asyncio.sleep(10)
                else:
                    try:
                        await bot.send_private_msg(user_id=admin, message=f"获取整百榜线失败，当前时间: {current_time}")
                    except Exception as e:
                        pass

                await asyncio.sleep(177)

        async def start_tasks():
            task1 = asyncio.create_task(refresh_task_sk())
            task2 = asyncio.create_task(refresh_task_border())
            try:
                await asyncio.gather(task1, task2)
            except Exception as e:
                logger.debug(f"任务执行过程中发生错误: {e}")

        await start_tasks()


twsk = on_command("twsk", priority=1, block=True)

@twsk.handle()
async def twsk_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    command_part = raw_input[4:].strip()
    qqnum = event.user_id

    if not command_part:
        userId , _ , ban = get_bindid(qqnum)
        logger.info(f"{userId},{ban}")
        if ban == 1:
           await twsk.finish("您已被封禁")
        elif userId is None:
           await twsk.finish("您还没有绑定，请输入tw绑定+id进行绑定")
        results = get_player_rank(userId=userId)
        await twsk.finish(results)

    parts = command_part.split()
    #logger.info(f"Parsed parts: {parts}")

    if all(part.isdigit() for part in parts) and len(parts) <= 5:
       results = [get_player_rank(rank=int(rank)) for rank in parts]
       last = "\n-----------------------\n".join(results)
    
       img = t2i(
       text=last,
       font_size=25,
       font_color='#000000',
       padding=(25, 25, 25, 25),
       max_width=560,
       wrap_type='left',
       line_interval=5,
       include_footer=True  
       )
       
       output_path = f"./data/piccache/{int(time.time())}.png"
       img.save(output_path)

       if not Path(output_path).exists():
        #   logger.error(f"File not saved: {output_path}")
          await bot.send("图片生成失败，请检查日志。")
          return

       output_path = Path(output_path).resolve()
    #    logger.debug(f"Resolved path: {output_path}")
       await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
    else:
       await twsk.finish("请提供有效的排名，单次最多查询5个")

twscoreline = on_command("tw线", priority=1, block=True)

@twscoreline.handle()
async def twscore_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban = get_bindid(qqnum)
 if ban == 1:
    await twscoreline.finish("您已被封禁")
 elif userId is None:
    await twscoreline.finish("您还没有绑定，请输入tw绑定+id进行绑定")

 try:
       results , last_time = get_border_scores()
       font = ImageFont.truetype('data/HarmonyOS_Sans_SC_Medium.ttf',25)
       image = Image.new("RGB",(550,750),(255,255,255))
       draw = ImageDraw.Draw(image)
       text_pos = (20,20)
       draw.text(text_pos,results,'#000000',font)

       footer_text = f"Generated by Resona Bot\n分数线有至高5min误差，请谨慎参考\n数据更新于：{last_time}"
       lines = footer_text.split('\n')
       footer_width = max(draw.textlength(line, font=font) for line in lines)
       footer_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)   
       footer_pos = (image.width - footer_width - 20, image.height - footer_height - 20)
       draw.text(footer_pos, footer_text, '#8888cc', font)

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
 except Exception as e:
       await bot.send(event, message=f"发生错误：{str(e)}")

twspeed = on_command("tw速", priority=1, block=True) 

@twspeed.handle()
async def twspeed_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban = get_bindid(qqnum)
 if ban == 1:
    await twwlspeed.finish("您已被封禁")
 elif userId is None:
    await twwlspeed.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    
 try:

       results , last_time = get_border_speed()

       font = ImageFont.truetype('data/HarmonyOS_Sans_SC_Medium.ttf',25)
       image = Image.new("RGB",(550,750),(255,255,255))
       draw = ImageDraw.Draw(image)
       text_pos = (20,20)
       draw.text(text_pos,results,'#000000',font)

       footer_text = f"Generated by Resona Bot\n时速有至高5min误差，请谨慎参考\n数据更新于：{last_time}"
       lines = footer_text.split('\n')
       footer_width = max(draw.textlength(line, font=font) for line in lines)
       footer_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)   
       footer_pos = (image.width - footer_width - 20, image.height - footer_height - 20)
       draw.text(footer_pos, footer_text, '#8888cc', font)

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
 except Exception as e:
       await bot.send(event, message=f"发生错误：{str(e)}")


twwlscoreline = on_command("wl线", priority=1, block=True) 

@twwlscoreline.handle()
async def twwlscore_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban = get_bindid(qqnum)
 if ban == 1:
    await twwlscoreline.finish("您已被封禁")
 elif userId is None:
    await twwlscoreline.finish("您还没有绑定，请输入tw绑定+id进行绑定")

 try:
       raw_input = event.get_plaintext().strip()
       command_part = raw_input[3:].strip()
       character_id = value_to_key(command_part)
       if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl线 角色罗马音")
            return


       results , last_time = get_border_scores(character_id)

       font = ImageFont.truetype('data/HarmonyOS_Sans_SC_Medium.ttf',25)
       image = Image.new("RGB",(550,750),(255,255,255))
       draw = ImageDraw.Draw(image)
       text_pos = (20,20)
       draw.text(text_pos,results,'#000000',font)

       footer_text = f"Generated by Resona Bot\n分数线有至高5min误差，请谨慎参考\n数据更新于：{last_time}"
       lines = footer_text.split('\n')
       footer_width = max(draw.textlength(line, font=font) for line in lines)
       footer_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)   
       footer_pos = (image.width - footer_width - 20, image.height - footer_height - 20)
       draw.text(footer_pos, footer_text, '#8888cc', font)

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
 except Exception as e:
       await bot.send(event, message=f"发生错误：{str(e)}")

twwlspeed = on_command("wl速", priority=1, block=True) 

@twwlspeed.handle()
async def twwlspeed_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban = get_bindid(qqnum)
 if ban == 1:
    await twwlspeed.finish("您已被封禁")
 elif userId is None:
    await twwlspeed.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    
 try:
       raw_input = event.get_plaintext().strip()
       command_part = raw_input[3:].strip()
       character_id = value_to_key(command_part)
       if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl速 角色罗马音")
            return


       results , last_time = get_border_speed(character_id)

       font = ImageFont.truetype('data/HarmonyOS_Sans_SC_Medium.ttf',25)
       image = Image.new("RGB",(550,750),(255,255,255))
       draw = ImageDraw.Draw(image)
       text_pos = (20,20)
       draw.text(text_pos,results,'#000000',font)

       footer_text = f"Generated by Resona Bot\n时速有至高5min误差，请谨慎参考\n数据更新于：{last_time}"
       lines = footer_text.split('\n')
       footer_width = max(draw.textlength(line, font=font) for line in lines)
       footer_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)   
       footer_pos = (image.width - footer_width - 20, image.height - footer_height - 20)
       draw.text(footer_pos, footer_text, '#8888cc', font)

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
 except Exception as e:
       await bot.send(event, message=f"发生错误：{str(e)}")



twprofile = on_command("tw个人信息",aliases={'twpjskprofile'},priority=1,block=True)
@twprofile.handle()
async def profile_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    userId , private , ban = get_bindid(qqnum)
    if ban == 1:
        await twprofile.finish("您已被封禁")
    elif userId is None:
        await twprofile.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    try:
        piccache_dir = "./data/piccache"
        if not os.path.exists(piccache_dir):
            os.makedirs(piccache_dir)
        
        image_path = pjskprofile(userid=userId,private=private,qqnum=qqnum)
        image_path = Path(image_path).resolve()
        message=MessageSegment.image(f"file://{image_path}")
        await bot.send(event, message)
    except Exception as e:

        await bot.send(event, message=f"发生错误：{str(e)}")


twwl = on_command("wl", priority=1, block=True)
@twwl.handle()
async def tw_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    userId , _ , ban = get_bindid(qqnum)
    if ban == 1:
       await twwl.finish("您已被封禁")
    elif userId is None:
        await twwl.finish("您还没有绑定，请输入tw绑定+id进行绑定")
        
    raw_input = event.get_plaintext().strip()
    
    match = re.match(r'^(\d+(?:\s+\d+)*)\s+(\w+)$', raw_input[2:].strip())
    if match:
        ranks_str, character_value = match.groups()
        ranks = [int(rank) for rank in ranks_str.split()]
        if len(ranks) > 3:
            await bot.send(event, "最多只能查询3个位次")
            return
        
        character_id = value_to_key(character_value)
        if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl 角色罗马音")
            return
        
        results = []
        for rank in ranks:
            result = get_player_singlerank(rank=rank,character_id=character_id)
            results.append(result)
        
        last = "\n".join(results)
        try:
               font = ImageFont.truetype('data/HarmonyOS_Sans_SC_Medium.ttf',25)
               image = Image.new("RGB",(700,760),(255,255,255))
               draw = ImageDraw.Draw(image)
               text_pos = (20,20)
               draw.text(text_pos,last,'#000000',font)

               footer_text = f"Generated by Resona Bot"
               lines = footer_text.split('\n')
               footer_width = max(draw.textlength(line, font=font) for line in lines)
               footer_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)   
               footer_pos = (image.width - footer_width - 20, image.height - footer_height - 20)
               draw.text(footer_pos, footer_text, '#8888cc', font)

               output_path = f"./data/piccache/{int(time.time())}.png"
               image.save(output_path)
               output_path = Path(output_path).resolve()
               await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
        except Exception as e:
               await bot.send(event, message=f"发生错误：{str(e)}")

    else:
        try:
               character_value = raw_input[2:].strip()
               character_id = value_to_key(character_value)
               if character_id is None:
                  await bot.send(event, "查不到角色哦，指令为wl 角色罗马音")
                  return
        
               result = get_player_singlerank(userId=userId,character_id=character_id)
               await bot.send(event, result)
        except Exception as e:
               await bot.send(event, message=f"发生错误：{str(e)}")


twzs = on_command("zs", priority=1, block=True)
@twzs.handle()
async def twzs_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    character_value = raw_input[2:].strip()
    character_id = value_to_key(character_value)
    if character_id is None:
        await bot.send(event, "查不到角色哦，指令为“zs 角色缩写”")
        return
    qqnum = event.user_id
    userId , _ , ban = get_bindid(qqnum)
    if ban == 1:
        await twzs.finish("您已被封禁")
    elif userId is None:
        await twzs.finish("您还没有绑定，请输入tw绑定+id进行绑定")

    try:
        
        result = get_dangours_speed(userId,character_id)
        await bot.send(event, result)      
    except Exception as e:
        await bot.send(event, message=f"发生错误：{str(e)}")

twbind = on_command("tw绑定", priority=1, block=True)
@twbind.handle()
async def twbind_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    id_part = raw_input[4:].strip()
    qqnum = int(event.user_id)
    now = int(time.time())
    if not id_part:
        await twbind.finish("请输入正确的id")
    try:
        registertime = int(id_part) / 1024 / 1024 / 4096
    except ValueError:
        await twbind.finish("请输入正确的id")
    if registertime <= 1601438400 or registertime >= now:
        await twbind.finish("请输入正确的id")
    else:
        try:
            update_binddatabase(id_part, qqnum)
        except Exception as e:
            await bot.send(event, f"fail，可能是数据库连接问题: {e}")
        else:
            await bot.send(event, "success")


twsongleak = on_command("tw新歌", priority=1, block=True)

@twsongleak.handle()
async def twsongleak_handler(bot: Bot, event: GroupMessageEvent):
   musiclist = twmusicleak()
   if not musiclist:
        await bot.send(event, "暂时没有即将发布的歌曲信息。")
   else:
        msg = "即将发布的歌曲列表：\n"
        for music in musiclist:
            msg += f"歌名: {music['name']}\n发布日期: {music['publishtime']}\n作曲: {music['composer']}\n\n"
        await bot.send(event, msg)

twban = on_command("ban", priority=1, block=True, permission=SUPERUSER)

@twban.handle()
async def twban_handler(bot: Bot, event: GroupMessageEvent):
    if event.reply:
        return

    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]
    # logger.debug(f"{at_id}")
    if not at_id:
        return
    for qqnum in at_id:
        # logger.debug(f"{qqnum}")
        update_binddatabase(qqnum=qqnum,ban=1)
        await bot.send(event, f"已加入黑名单")

twunban = on_command("unban", priority=1, block=True, permission=SUPERUSER)

@twunban.handle()
async def twunban_handler(bot: Bot, event: GroupMessageEvent):
    if event.reply:
        return

    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]
    # logger.debug(f"{at_id}")
    if not at_id:
        return
    for qqnum in at_id:
        # logger.debug(f"{qqnum}")
        update_binddatabase(qqnum=qqnum,ban=0)
        await bot.send(event, f"已解除黑名单")


twcf = on_command("twcf", priority=1, block=True)

@twcf.handle()
async def twcf_handler(bot: Bot, event: GroupMessageEvent):
    if event.reply:
        return

    user_qqnum = event.user_id
    user_userId , _ , ban = get_bindid(user_qqnum)

    if ban == 1:
        await twcf.finish("您已被封禁")
    elif user_userId is None:
        await twcf.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    
    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]
    # logger.info(f"{at_id}")
    if not at_id:
        return
    for qqnum in at_id:
        userId , private , _ = get_bindid(qqnum)
        if private == 1:
            await twcf.finish("查不到哦，可能是不给看")
            return
        # logger.info(f"{userId}")
        results = get_player_rank(userId=userId)
        await twcf.finish(results)

wlcf = on_command("wlcf", priority=1, block=True)

@wlcf.handle()
async def wlcf_handler(bot: Bot, event: GroupMessageEvent):
    if event.reply:
        return
    raw_input = event.get_plaintext().strip()
    user_qqnum = event.user_id
    user_userId , _ , ban = get_bindid(user_qqnum)
    character_value = raw_input[4:].strip()
    character_id = value_to_key(character_value)

    if character_id is None:
        await wlcf.finish("查不到角色哦，指令为wlcf 角色罗马音")
        return
    
    if ban == 1:
        await wlcf.finish("您已被封禁")
    elif user_userId is None:
        await wlcf.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    
    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]

    if not at_id:
        return
    for qqnum in at_id:
        userId , private , _ = get_bindid(qqnum)
        if private == 1:
            await wlcf.finish("查不到哦，可能是不给看")
            return
        logger.info(f"{userId}+{character_id}")
        result = get_player_singlerank(userId=userId,character_id=character_id)
        await wlcf.finish(result)


private = on_command("tw不给看", priority=1, block=True)

@private.handle()
async def private_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    update_binddatabase(qqnum=qqnum,private=1)
    await private.finish("已设置隐藏")

public = on_command("tw给看", priority=1, block=True)

@public.handle()
async def public_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    update_binddatabase(qqnum=qqnum,private=0)
    await public.finish("已设置公开")


change_bg = on_command('更新背景',aliases={'背景更新'}, priority=1, block=True)

@change_bg.handle()
async def change_bg_send(bot: Bot, event: GroupMessageEvent):
    msg = str(event.get_message())
    qqnum = event.get_user_id()
    file_match = re.search(r'file=([^,]+)', msg)
    
    if file_match:
        file_value = file_match.group(1)
        # logger.debug(f"提取的 file 参数值: {file_value}")

        try:
            image_info = await bot.get_image(file=file_value)
            image_path = image_info["file"]
            # logger.debug(f"获取到图片: {image_path}")
            _, ext = os.path.splitext(image_path)

            if ext.lower() not in ['.jpg', '.png']:
                await bot.send(event, "图片格式不支持，请上传 jpg 或 png 格式的图片")
                return
            
            with Image.open(image_path) as img:
                width, height = img.size
                if width != 1600 or height != 1100:
                    await bot.send(event, f"图片尺寸为 {width}x{height}，请裁剪为1600x1100后重新上传")
                    return

            save_path = f"./pics/bg/{qqnum}{ext}"
            for ext in ['.png', '.jpg']:
                existing_file = f"./pics/bg/{qqnum}{ext}"
                if os.path.exists(existing_file):
                    os.remove(existing_file)

            shutil.move(image_path, save_path)
            # logger.debug(f"图片已保存到 {save_path}")
            await bot.send(event, "背景已更新")
        except Exception as e:
            await bot.send(event, f"获取图片失败{e}")
    else:
        return
