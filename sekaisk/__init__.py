import re
import os
import shutil
from pathlib import Path
import time
from PIL import Image, ImageFont, ImageDraw
from nonebot import get_plugin_config, on_command, get_driver
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent,MessageSegment,Message
from .twmusicleak import twmusicleak
from .pjskprofile import pjskprofile
from .database import update_binddatabase,value_to_key,get_bindid
from .sk import get_player_rank,get_player_singlerank,get_border_scores,get_dangours_speed,get_border_speed,get_stop_time
from .texttoimg import create_text_image
from .scheduler_manager import init_scheduler
from .config import Config



__plugin_meta__ = PluginMetadata(
    name="sekaisk",
    description="",
    usage="",
    config=Config,
)

api_account_id = Config.user_id
driver = get_driver()

#开机自启动
@driver.on_startup
async def startup():
    await init_scheduler(user_id=api_account_id)

refresh_sk = on_command("rsk", priority=1, block=True,permission=SUPERUSER)

@refresh_sk.handle()
async def refresh_sk_handler(bot: Bot, event: GroupMessageEvent):
    await init_scheduler(user_id=api_account_id)
    await refresh_sk.finish("已启动榜线刷新")

twsk = on_command("twsk", priority=1, block=True)

@twsk.handle()
async def twsk_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    command_part = raw_input[4:].strip()
    qqnum = event.user_id
    userId , _ , ban , theme = get_bindid(qqnum)
    if ban == 1:
           await twsk.finish("您已被封禁")
    elif userId is None:
           return
    if not command_part:        
        # logger.info(f"{userId},{ban}")
        
       results = get_player_rank(userId=userId)
       await twsk.finish(results)

    parts = command_part.split()
    #logger.info(f"Parsed parts: {parts}")

    if all(part.isdigit() for part in parts) and len(parts) <= 8:
       results = [get_player_rank(rank=int(rank)) for rank in parts]
       last = "\n-------------------------------\n".join(results)
    
       img = create_text_image(
       text=last,
       font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
       font_size=25,
       max_width=800,
       line_spacing=15,
       alignment="left",
       bg_color=theme,
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
 userId , _ , ban , theme = get_bindid(qqnum)
 if ban == 1:
    await twscoreline.finish("您已被封禁")
 elif userId is None:
    return

 try:
       results , last_time = get_border_scores()
       image = create_text_image(
       text=results,
       font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
       font_size=25,
       max_width=800,
       line_spacing=15,
       alignment="left",
       include_footer =False,
       bg_color=theme,
       )

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       message=Message([
           f'分数线有至高5min误差，请谨慎参考\n数据更新于：{last_time}',
           MessageSegment.image(f"file://{output_path}")
       ])
       await bot.send(event, message)
 except Exception as e:
       await bot.send(event, message=f"查不到捏，怎么会是呢")

twspeed = on_command("tw速", priority=1, block=True) 

@twspeed.handle()
async def twspeed_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban , theme = get_bindid(qqnum)
 if ban == 1:
    await twwlspeed.finish("您已被封禁")
 elif userId is None:
    return
    
 try:
       results , last_time = get_border_speed()

       image = create_text_image(
       text=results,
       font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
       font_size=25,
       max_width=800,
       line_spacing=15,
       alignment="left",
       include_footer =False,
       bg_color=theme,
       )

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       message=Message([
           f'档线计算时速有至高5min误差，请谨慎参考\n数据更新于：{last_time}',
           MessageSegment.image(f"file://{output_path}")
       ])
       await bot.send(event, message)
 except Exception as e:
       await bot.send(event, message=f"查不到捏，怎么会是呢")


twwlscoreline = on_command("wl线", priority=1, block=True) 

@twwlscoreline.handle()
async def twwlscore_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban , theme = get_bindid(qqnum)
 if ban == 1:
    await twwlscoreline.finish("您已被封禁")
 elif userId is None:
    return

 try:
       raw_input = event.get_plaintext().strip()
       command_part = raw_input[3:].strip()
       character_id = value_to_key(command_part)
       if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl线 角色罗马音")
            return

       results , last_time = get_border_scores(character_id)

       image = create_text_image(
       text=results,
       font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
       font_size=25,
       max_width=800,
       line_spacing=15,
       alignment="left",
       include_footer =False,
       bg_color=theme,
       )

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       message=Message([
           f'档线有至高5min误差，请谨慎参考\n数据更新于：{last_time}',
           MessageSegment.image(f"file://{output_path}")
       ])
       await bot.send(event, message)
 except Exception as e:
       await bot.send(event, message=f"查不到捏，怎么会是呢")

twwlspeed = on_command("wl速", priority=1, block=True) 

@twwlspeed.handle()
async def twwlspeed_handler(bot: Bot, event: GroupMessageEvent):
 qqnum = event.user_id
 userId , _ , ban , theme = get_bindid(qqnum)
 if ban == 1:
    await twwlspeed.finish("您已被封禁")
 elif userId is None:
    return
    
 try:
       raw_input = event.get_plaintext().strip()
       command_part = raw_input[3:].strip()
       character_id = value_to_key(command_part)
       if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl速 角色罗马音")
            return

       results , last_time = get_border_speed(character_id)
       image = create_text_image(
       text=results,
       font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
       font_size=25,
       max_width=800,
       line_spacing=15,
       alignment="left",
       include_footer =False,
       bg_color=theme,
       )

       output_path = f"./data/piccache/{int(time.time())}.png"
       image.save(output_path)
       output_path = Path(output_path).resolve()
       message=Message([
           f'档线计算时速有至高5min误差，请谨慎参考\n数据更新于：{last_time}',
           MessageSegment.image(f"file://{output_path}")
       ])
       await bot.send(event, message)
 except Exception as e:
       await bot.send(event, message=f"查不到捏，怎么会是呢")

twprofile = on_command("tw个人信息",aliases={'twpjskprofile'},priority=1,block=True)
@twprofile.handle()
async def profile_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    userId , private , ban , _ = get_bindid(qqnum)
    if ban == 1:
        await twprofile.finish("您已被封禁")
    elif userId is None:
        return
    try:
        piccache_dir = "./data/piccache"
        if not os.path.exists(piccache_dir):
            os.makedirs(piccache_dir)
        
        image_path = await pjskprofile(userid=userId,private=private,qqnum=qqnum)
        image_path = Path(image_path).resolve()
        message=MessageSegment.image(f"file://{image_path}")
        await bot.send(event, message)
    except Exception as e:
        await bot.send(event, message=f"查不到捏，怎么会是呢")


twwl = on_command("wl", priority=1, block=True)
@twwl.handle()
async def tw_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    userId , _ , ban , theme = get_bindid(qqnum)
    if ban == 1:
       await twwl.finish("您已被封禁")
    elif userId is None:
        return
        
    raw_input = event.get_plaintext().strip()
    
    match = re.match(r'^(\d+(?:\s+\d+)*)\s+(\w+)$', raw_input[2:].strip())
    if match:
        ranks_str, character_value = match.groups()
        ranks = [int(rank) for rank in ranks_str.split()]
        if len(ranks) > 6:
            await bot.send(event, "最多只能查询6个位次")
            return
        
        character_id = value_to_key(character_value)
        if character_id is None:
            await bot.send(event, "查不到角色哦，指令为wl 角色罗马音")
            return
        
        results = []
        for rank in ranks:
            result = get_player_singlerank(rank=rank,character_id=character_id)
            results.append(result)
        
        last = "\n-------------------------------\n".join(results)
        try:
               image = create_text_image(
                     text=last,
                     font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
                     font_size=25,
                     max_width=800,
                     line_spacing=15,
                     alignment="left",
                     bg_color=theme,
                     )

               output_path = f"./data/piccache/{int(time.time())}.png"
               image.save(output_path)
               output_path = Path(output_path).resolve()
               await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
        except Exception as e:
               await bot.send(event, message=f"查不到捏，怎么会是呢")

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
               await bot.send(event, message=f"查不到捏，怎么会是呢")


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
    userId , _ , ban , _ = get_bindid(qqnum)
    if ban == 1:
        await twzs.finish("您已被封禁")
    elif userId is None:
        return

    try:
        
        result = get_dangours_speed(userId,character_id)
        await bot.send(event, result)      
    except Exception as e:
        await bot.send(event, message=f"查不到捏，怎么会是呢")

twbind = on_command("tw绑定", priority=1, block=True)
@twbind.handle()
async def twbind_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    userId = raw_input[4:].strip()
    qqnum = int(event.user_id)
    now = int(time.time())
    if not userId:
        await twbind.finish("请输入正确的id")
    try:
        registertime = int(userId) / 1024 / 1024 / 4096
    except ValueError:
        await twbind.finish("请输入正确的id")
    if registertime <= 1601438400 or registertime >= now:
        await twbind.finish("请输入正确的id")
    else:
        try:
            update_binddatabase(userId, qqnum)
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
    user_userId , _ , ban , _ = get_bindid(user_qqnum)

    if ban == 1:
        await twcf.finish("您已被封禁")
    elif user_userId is None:
        return
    
    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]
    # logger.info(f"{at_id}")
    if not at_id:
        return
    for qqnum in at_id:
        userId , private , _ , _ = get_bindid(qqnum)
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
    user_userId , _ , ban , _ = get_bindid(user_qqnum)
    character_value = raw_input[4:].strip()
    character_id = value_to_key(character_value)

    if character_id is None:
        await wlcf.finish("查不到角色哦，指令为wlcf 角色罗马音")
        return
    
    if ban == 1:
        await wlcf.finish("您已被封禁")
    elif user_userId is None:
        return
    
    at_id = [segment.data["qq"] for segment in event.message if segment.type == "at"]

    if not at_id:
        return
    for qqnum in at_id:
        userId , private , _ , _ = get_bindid(qqnum)
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


change_skbg = on_command('theme', priority=1, block=True)

@change_skbg.handle()
async def change_skbg_send(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    qqnum = event.user_id
    user_userId , _ , ban , _ = get_bindid(qqnum)
    if ban == 1:
        await change_skbg.finish("您已被封禁")
    elif user_userId is None:
        await change_skbg.finish("您还没有绑定，请输入tw绑定+id进行绑定")
    color = raw_input[5:].strip()
    pattern = r"^#([0-9a-f]{3}|[0-9a-f]{6})$"
    if re.match(pattern, color, re.IGNORECASE):
        update_binddatabase(qqnum=qqnum,theme=color)
        await change_skbg.finish("主题已更新")
    else:
        await change_skbg.finish("请输入正确的16进制颜色码,例如#8888cc或者#9CF") 

twcsb = on_command("twcsb",aliases={'tw查水表'}, priority=1, block=True)

@twcsb.handle()
async def twcsb_handler(bot: Bot, event: GroupMessageEvent):
    raw_input = event.get_plaintext().strip()
    command_part = raw_input[5:].strip()
    qqnum = event.user_id
    userId , _ , ban , theme = get_bindid(qqnum)
    if ban == 1:
        await twcsb.finish("您已被封禁")
    elif userId is None:
        return
    try:
       if command_part:
          results,is_draw = get_stop_time(rank=command_part)
       else:
          results,is_draw = get_stop_time(userId=userId)
          
       if is_draw:
           
           img = create_text_image(
              text=results,
              font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
              font_size=25,
              max_width=800,
              line_spacing=15,
              alignment="left",
              bg_color=theme,
              )
                 
           output_path = f"./data/piccache/{int(time.time())}.png"
           img.save(output_path)

           if not Path(output_path).exists():
               await bot.send("图片生成失败，请检查日志。")

           output_path = Path(output_path).resolve()
    
           await bot.send(event, message=MessageSegment.image(f"file://{output_path}"))
       else:
           await bot.send(event, results)
    except Exception as e:
        await twcsb.finish(f"查不到捏，怎么会是呢")

wlcsb = on_command("wlcsb",aliases={'wl查水表'}, priority=1, block=True)

@wlcsb.handle()
async def wlcsb_handler(bot: Bot, event: GroupMessageEvent):
    qqnum = event.user_id
    userId, _, ban, theme = get_bindid(qqnum)
    if ban == 1:
        await wlcsb.finish("您已被封禁")
    elif userId is None:
        await wlcsb.finish("您还没有绑定，请输入tw绑定+id进行绑定")

    raw_input = event.get_plaintext().strip()[5:].strip() 
    match = re.match(r'^(\d+\s+)?(\w+)$', raw_input)
    if match:
        ranks_str, character_value = match.groups()
        # logger.debug(f"Ranks: {ranks_str}, Character: {character_value}")
        if ranks_str:
            ranks_str = ranks_str.strip()
            if not ranks_str.isdigit():
                await bot.send(event, "位次必须为数字")
                return
            ranks = [int(ranks_str)]
        else:
            ranks = None

        character_id = value_to_key(character_value)
        if character_id is None:
            await bot.send(event, "查不到角色哦，指令为：wlcsb [位次] 角色罗马音")
            return

        try:
            if ranks:
                # 位次查询模式
                results, is_draw = get_stop_time(rank=ranks[0], character=character_id)
            else:
                # 用户ID查询模式
                results, is_draw = get_stop_time(userId=userId, character=character_id)

            if is_draw:
                img = create_text_image(
                    text=results,
                    font_path="data/HarmonyOS_Sans_SC_Medium.ttf",
                    font_size=25,
                    max_width=800,
                    line_spacing=15,
                    alignment="left",
                    bg_color=theme,
                )
                output_path = f"./data/piccache/{int(time.time())}.png"
                img.save(output_path)
                if not Path(output_path).exists():
                    await bot.send(event, "图片生成失败，请检查日志。")
                await bot.send(event, message=MessageSegment.image(f"file://{Path(output_path).resolve()}"))
            else:
                await bot.send(event, results)
        except Exception as e:
            await wlcsb.finish(f"查不到捏，怎么会是呢？")
            logger.error(f"Error: {e}")
    else:
        await bot.send(event, "指令格式错误，请使用：wlcsb [位次] 角色罗马音")

          

