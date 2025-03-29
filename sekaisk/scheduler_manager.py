import asyncio
import time
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from .api_client import ApiClient
from .database import update_skdatabase,update_wlskdatabase,update_borderdatabase,update_wlborder_database
from nonebot.log import logger

scheduler = AsyncIOScheduler()

async def refresh_task_sk(client, event_info , user_id):
    event_id = event_info['id']
    event_type = event_info['eventType']
    event_announce = event_info['rankannounce']

    now = int(time.time() * 1000)
    if now > (event_announce + 310000):
        logger.info("榜线已公示，停止获取榜线")
        return

    for retry in range(3):
        result = await client.call_api(f"/user/{user_id}/event/{event_id}/ranking?rankingViewType=top100")
        # logger.debug(f"获取榜线结果：{result}")
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
            logger.error(f"获取榜线失败，尝试 {retry + 1}/3，当前时间: {current_time}")
            await asyncio.sleep(10)



async def refresh_task_border(client, event_info):
    event_id = event_info['id']
    event_type = event_info['eventType']
    event_announce = event_info['rankannounce']

    now = int(time.time() * 1000)
    if now > (event_announce + 310000):
        logger.info("榜线已公示，停止获取榜线")
        return

    for retry in range(3):
        result = await client.call_api(f"/event/{event_id}/ranking-border")
        data_time = int(time.time())
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if result:
            logger.info(f"整百更新成功，时间: {current_time}")
            if event_type in ["marathon", "cheerful_carnival"]:
                update_borderdatabase(result, event_id, event_type, data_time)
            elif event_type == "world_bloom":
                update_wlborder_database(result, event_id, event_type, data_time)
            break
        else:
            logger.error(f"获取整百榜线失败，尝试 {retry + 1}/3，当前时间: {current_time}")
            await asyncio.sleep(10)



async def start_tasks(event_info, user_id):
    """启动刷新任务"""
    client = await ApiClient.create(user_id)

    # 需要取消的任务ID列表，包括原有的任务和停止任务
    task_names = ['refresh_task_sk', 'refresh_task_border', 'stop_tasks_job']
    
    # 取消已有任务
    for task_name in task_names:
        if scheduler.get_job(task_name):
            scheduler.remove_job(task_name)
            logger.info(f"已取消任务: {task_name}")

    if event_info and event_info['eventStatus'] == "going":
        logger.info("活动正在进行，启动刷新任务...")

        # 立即执行一次任务
        await refresh_task_sk(client, event_info, user_id)
        await refresh_task_border(client, event_info)

        # 添加定时任务
        scheduler.add_job(
            refresh_task_sk,
            'interval',
            seconds=60,
            args=[client, event_info, user_id],
            id='refresh_task_sk'
        )
        scheduler.add_job(
            refresh_task_border,
            'interval',
            seconds=120,
            args=[client, event_info],
            id='refresh_task_border'
        )

        # 榜线公布后310秒取消榜线获取任务
        stop_time = datetime.fromtimestamp((event_info['rankannounce'] + 310000) / 1000)
        scheduler.add_job(
            stop_and_schedule_next,
            trigger=DateTrigger(run_date=stop_time),
            args=[user_id],
            id='stop_tasks_job'
        )
        logger.info(f"已设置榜线停止时间在: {stop_time}")
    else:
        logger.info("当前活动不在进行中")


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


async def find_next_event_start_time():
    with open('./twmasterdata/events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    now = int(time.time() * 1000)
    next_event_start_time = None

    for event in data:
        start_at = event.get('startAt')
        if start_at and start_at > now:
            if not next_event_start_time or start_at < next_event_start_time:
                next_event_start_time = start_at

    return next_event_start_time


async def schedule_next_event(user_id):
    next_event_start_time = await find_next_event_start_time()
    if next_event_start_time:
        trigger_time = datetime.fromtimestamp(next_event_start_time / 1000)
        logger.info(f"下一个活动将在 {trigger_time} 开始，设置定时任务...")
        scheduler.add_job(
            auto_start_scheduler,  # 直接传递异步函数
            trigger=DateTrigger(run_date=trigger_time),
            args=[user_id],  # 通过 args 传递参数
            id=f"next_event_{int(next_event_start_time)}"
        )
    else:
        logger.error("未找到未来的活动，定时任务不会启动")


async def auto_start_scheduler(user_id):
    event_info = current_event()
    if event_info:
        if event_info['eventStatus'] == "going":
            await start_tasks(event_info, user_id)
        else:
            logger.info("当前活动已结束，开始寻找下一个活动")
            await schedule_next_event(user_id)
    else:
        logger.info("当前无活动进行中，开始寻找下一个活动")
        await schedule_next_event(user_id)

async def stop_and_schedule_next(user_id):

    # 移除任务
    for job_id in ['refresh_task_sk', 'refresh_task_border']:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"已停止任务: {job_id}")
    # 设置下一个活动的定时
    await schedule_next_event(user_id)

async def init_scheduler(user_id):
    global scheduler
    if not scheduler.running:
        scheduler.start()
        await auto_start_scheduler(user_id)
        logger.info("调度器已成功启动")
    else:
        logger.info("调度器已经运行，跳过启动")
    # 在调度器启动后立即检查当前是否有活动进行中
    

def stop_scheduler():
    scheduler.shutdown()