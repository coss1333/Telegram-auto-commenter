import os, asyncio, random, json, datetime, time
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel, PeerChat, PeerUser
from utils import keywords_from_messages, build_reply

load_dotenv()
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
TARGET_CHAT = os.getenv("TARGET_CHAT", "")
TZ = os.getenv("TZ", "Europe/Riga")
os.environ["TZ"] = TZ
try:
    import time as _time; _time.tzset()
except Exception:
    pass

POST_WINDOW_START = int(os.getenv("POST_WINDOW_START", "9"))
POST_WINDOW_END = int(os.getenv("POST_WINDOW_END", "21"))
MIN_COMMENTS = int(os.getenv("MIN_COMMENTS_PER_DAY", "1"))
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS_PER_DAY", "2"))
LANG = os.getenv("LANG", "ru")

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_date": None, "made_today": 0}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def ensure_daily_quota(state):
    today = datetime.date.today().isoformat()
    if state.get("last_date") != today:
        state["last_date"] = today
        state["made_today"] = 0
        # choose today's target between MIN and MAX
        state["target_today"] = random.randint(MIN_COMMENTS, MAX_COMMENTS)
        save_state(state)
    return state

async def choose_random_time_in_window():
    hour = random.randint(POST_WINDOW_START, POST_WINDOW_END)
    minute = random.randint(0,59)
    return hour, minute

async def fetch_last_messages(client, entity, limit=10):
    msgs = []
    async for m in client.iter_messages(entity, limit=limit):
        if m.message and not m.from_id == (await client.get_me()).id:
            msgs.append(m)
    msgs.reverse()
    return msgs

async def pick_reply_target(messages):
    # pick the newest human message to reply to
    for m in reversed(messages):
        if not m.out and m.message:
            return m
    return messages[-1] if messages else None

async def post_one_comment(client, entity):
    msgs = await fetch_last_messages(client, entity, limit=10)
    texts = [m.message or "" for m in msgs]
    kws = keywords_from_messages(texts, lang=LANG, topn=5)
    reply_text = build_reply(kws, lang=LANG)
    target = await pick_reply_target(msgs)
    if target:
        await client.send_message(entity, reply_text, reply_to=target.id)
        return True
    else:
        # no messages available, just post a standalone message
        await client.send_message(entity, reply_text)
        return True

async def daily_runner(client, entity):
    state = load_state()
    state = await ensure_daily_quota(state)
    if state["made_today"] >= state.get("target_today", MAX_COMMENTS):
        return

    # post one comment now
    ok = await post_one_comment(client, entity)
    if ok:
        state["made_today"] += 1
        save_state(state)

async def schedule_jobs(client, entity):
    scheduler = AsyncIOScheduler(timezone=TZ)
    # launch N random times/day by scheduling a minute check each minute in window,
    # but we control quota via state, so it's safe.
    scheduler.add_job(lambda: asyncio.create_task(daily_runner(client, entity)),
                      CronTrigger(minute="*/7", hour=f"{POST_WINDOW_START}-{POST_WINDOW_END}"))
    scheduler.start()

async def main():
    if not all([API_ID, API_HASH, SESSION_STRING, TARGET_CHAT]):
        raise SystemExit("Please set API_ID, API_HASH, SESSION_STRING, TARGET_CHAT in .env")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        entity = await client.get_entity(TARGET_CHAT)
        await schedule_jobs(client, entity)
        print("Auto commenter is running. Press Ctrl+C to stop.")
        # keep the loop alive
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
