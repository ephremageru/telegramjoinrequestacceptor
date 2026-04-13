import asyncio
import logging
import sys
import json
import os
from datetime import datetime, date
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ChatJoinRequest
from aiogram.filters import Command, CommandObject, Filter
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError

# ================= Configuration =================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
DATA_FILE = "bot_data.json"

if not BOT_TOKEN or not ADMIN_IDS:
    raise ValueError("Missing BOT_TOKEN or ADMIN_IDS in .env file.")

# ================= State Management & Database =================
class BotState:
    def __init__(self):
        self.total_joins: int = 0
        self.today_joins: int = 0
        self.last_date: str = date.today().isoformat()
        self.welcome_enabled: bool = True
        self.start_time: datetime = datetime.now()
        self.users: set = set()

    def load(self):
        """Loads data from a JSON file so stats survive restarts."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.total_joins = data.get("total_joins", 0)
                    self.today_joins = data.get("today_joins", 0)
                    self.last_date = data.get("last_date", date.today().isoformat())
                    self.welcome_enabled = data.get("welcome_enabled", True)
                    self.users = set(data.get("users", []))
            except Exception as e:
                logging.error(f"Error loading data: {e}")

    def save(self):
        """Saves current state to a JSON file."""
        data = {
            "total_joins": self.total_joins,
            "today_joins": self.today_joins,
            "last_date": self.last_date,
            "welcome_enabled": self.welcome_enabled,
            "users": list(self.users)
        }
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving data: {e}")

state = BotState()
state.load()
router = Router()

# ================= Filters =================
class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS

# ================= Helper Functions =================
def check_new_day():
    current_date = date.today().isoformat()
    if current_date != state.last_date:
        state.today_joins = 0
        state.last_date = current_date
        state.save()

# ================= Core Handlers =================
@router.chat_join_request()
async def process_join_request(update: ChatJoinRequest, bot: Bot):
    check_new_day()
    user_id = update.from_user.id
    
    try:
        if user_id not in state.users:
            state.users.add(user_id)
            state.total_joins += 1
            state.today_joins += 1
            state.save() 

        await update.approve()
        
        if state.welcome_enabled:
            welcome_text = (
                "✅ Subscription Approved\n\n"
                "🎥 @Joab_movies"
            )
            await bot.send_message(chat_id=user_id, text=welcome_text)
            
    except Exception as e:
        logging.error(f"Failed to process join request for user {user_id}: {e}")

# ================= Registration =================
@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id not in state.users:
        state.users.add(message.from_user.id)
        state.save()
        
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("👋 Hello! Send a join request to our channel to get access.")
    else:
        await message.answer("👑 Hello Admin! Use /status or /stats to see system info.")

# ================= Admin Commands (DMs Only) =================
@router.message(Command("stats"), IsAdmin(), F.chat.type == "private")
async def cmd_stats(message: Message):
    check_new_day()
    text = (
        "📊 <b>Join Analytics</b>\n\n"
        f"📅 Today: <b>{state.today_joins}</b>\n"
        f"🌍 Total: <b>{state.total_joins}</b>\n"
        f"👥 Reachable Users: <b>{len(state.users)}</b>"
    )
    await message.answer(text)

@router.message(Command("welcome_on"), IsAdmin(), F.chat.type == "private")
async def cmd_welcome_on(message: Message):
    state.welcome_enabled = True
    state.save()
    await message.answer("✅ <b>Welcome DMs are now ON.</b>")

@router.message(Command("welcome_off"), IsAdmin(), F.chat.type == "private")
async def cmd_welcome_off(message: Message):
    state.welcome_enabled = False
    state.save()
    await message.answer("❌ <b>Welcome DMs are now OFF.</b>")

@router.message(Command("status"), IsAdmin(), F.chat.type == "private")
async def cmd_status(message: Message):
    uptime = datetime.now() - state.start_time
    welcome_status = "✅ Enabled" if state.welcome_enabled else "❌ Disabled"
    
    text = (
        "⚙️ <b>System Status</b>\n\n"
        f"⏱ Uptime: <code>{str(uptime).split('.')[0]}</code>\n"
        f"✉️ Welcome DM: {welcome_status}\n"
        f"🟢 Bot Health: <b>Excellent</b>\n"
        f"💾 Database: <b>Active (bot_data.json)</b>"
    )
    await message.answer(text)

@router.message(Command("reset"), IsAdmin(), F.chat.type == "private")
async def cmd_reset(message: Message):
    state.total_joins = 0
    state.today_joins = 0
    state.last_date = date.today().isoformat()
    state.save()
    await message.answer("🔄 <b>Analytics have been reset to 0.</b> (User broadcast list kept intact)")

@router.message(Command("broadcast"), IsAdmin(), F.chat.type == "private")
async def cmd_broadcast(message: Message, command: CommandObject, bot: Bot):
    if not command.args:
        await message.answer("⚠️ Please provide a message.\nExample: <code>/broadcast Hello everyone!</code>")
        return

    users_to_message = list(state.users)
    if not users_to_message:
        await message.answer("❌ No users found in the database.")
        return

    await message.answer(f"🚀 Starting broadcast to <b>{len(users_to_message)}</b> users...")
    
    success_count = 0
    fail_count = 0
    users_to_remove = []

    for user_id in users_to_message:
        try:
            await bot.send_message(chat_id=user_id, text=command.args)
            success_count += 1
            await asyncio.sleep(0.05) # Rate limit protection
        except TelegramForbiddenError:
            fail_count += 1
            users_to_remove.append(user_id)
        except TelegramAPIError:
            fail_count += 1

    # Clean up blocked users
    for user_id in users_to_remove:
        state.users.discard(user_id)
    if users_to_remove:
        state.save()

    await message.answer(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📤 Delivered: {success_count}\n"
        f"🚫 Failed/Blocked: {fail_count}"
    )

# ================= Main Entry Point =================
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    
    logging.info("Starting Channel Join Acceptor bot...")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        state.save()
        logging.info("Bot stopped smoothly and data saved.")
