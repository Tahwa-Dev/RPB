import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from telethon import TelegramClient, functions, errors
import os

# --- Load config ---
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["bot_token"]
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Load admins ---
ADMINS_FILE = "admins.json"
try:
    with open(ADMINS_FILE) as f:
        admins_data = json.load(f)
except:
    admins_data = {"admins": []}

# --- Load accounts ---
ACCOUNTS_FILE = "accounts.json"
try:
    with open(ACCOUNTS_FILE) as f:
        accounts_data = json.load(f)
except:
    accounts_data = {"accounts": []}

# --- Main menu ---
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ Add Account", callback_data="add_account"),
        InlineKeyboardButton("📋 List Accounts", callback_data="list_accounts")
    )
    kb.add(
        InlineKeyboardButton("🚨 Report", callback_data="report"),
        InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")
    )
    return kb

# --- FSM States ---
class AddAccountStates(StatesGroup):
    waiting_phone = State()
    waiting_api_id = State()
    waiting_api_hash = State()

class ReportStates(StatesGroup):
    waiting_target = State()
    waiting_reason = State()
    waiting_text = State()

# --- Start command ---
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    if message.from_user.id not in admins_data["admins"]:
        await message.reply("❌ You are not an admin.")
        return
    await message.reply("🤖 Welcome to the bot", reply_markup=main_menu())

# --- Callback handler ---
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in admins_data["admins"]:
        await call.answer("❌ You are not an admin.", show_alert=True)
        return

    if call.data == "add_admin":
        await call.message.reply("Enter new admin ID:")
        dp.register_message_handler(add_admin, state="waiting_admin_id")

    elif call.data == "add_account":
        await call.message.reply("Enter account phone number (example +98912xxxxxxx):")
        await AddAccountStates.waiting_phone.set()

    elif call.data == "list_accounts":
        if not accounts_data["accounts"]:
            await call.message.reply("📭 No accounts found")
        else:
            text = "\n".join([f"{a['phone']} | {a['api_id']}" for a in accounts_data["accounts"]])
            await call.message.reply(f"📋 Accounts:\n{text}")

    elif call.data == "report":
        await call.message.reply("🚩 Enter username to report (without @):")
        await ReportStates.waiting_target.set()

# --- Add Admin ---
async def add_admin(message: types.Message):
    try:
        new_admin = int(message.text)
        if new_admin not in admins_data["admins"]:
            admins_data["admins"].append(new_admin)
            with open(ADMINS_FILE, "w") as f:
                json.dump(admins_data, f)
            await message.reply(f"✅ Admin {new_admin} added")
        else:
            await message.reply("⚠️ This admin already exists")
    except:
        await message.reply("⚠️ Enter a valid number")
    dp.unregister_message_handler(add_admin, state="waiting_admin_id")

# --- Add Account ---
@dp.message_handler(state=AddAccountStates.waiting_phone)
async def add_account_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.reply("🔢 Enter API ID:")
    await AddAccountStates.waiting_api_id.set()

@dp.message_handler(state=AddAccountStates.waiting_api_id)
async def add_account_api_id(message: types.Message, state: FSMContext):
    await state.update_data(api_id=int(message.text.strip()))
    await message.reply("🔑 Enter API Hash:")
    await AddAccountStates.waiting_api_hash.set()

@dp.message_handler(state=AddAccountStates.waiting_api_hash)
async def add_account_api_hash(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data["phone"]
    api_id = data["api_id"]
    api_hash = message.text.strip()

    # Check session file exists
    session_file = f"sessions/{phone}.session"
    if not os.path.exists(session_file):
        await message.reply("⚠️ Session file not found. Make sure the account is logged in and session file uploaded.")
        await state.finish()
        return

    accounts_data["accounts"].append({"phone": phone, "api_id": api_id, "api_hash": api_hash})
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts_data, f, indent=4)
    await message.reply(f"✅ Account {phone} added successfully!", reply_markup=main_menu())
    await state.finish()

# --- Report ---
@dp.message_handler(state=ReportStates.waiting_target)
async def report_target(message: types.Message, state: FSMContext):
    await state.update_data(target=message.text.strip())
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Scam", callback_data="reason_scam"),
        InlineKeyboardButton("Spam", callback_data="reason_spam"),
        InlineKeyboardButton("Violence", callback_data="reason_violence"),
        InlineKeyboardButton("Other", callback_data="reason_other")
    )
    await message.reply("🚩 Select reason:", reply_markup=kb)
    await ReportStates.waiting_reason.set()

@dp.callback_query_handler(lambda c: c.data.startswith("reason_"), state=ReportStates.waiting_reason)
async def report_reason(call: types.CallbackQuery, state: FSMContext):
    reason = call.data.split("_")[1]
    await state.update_data(reason=reason)
    await call.message.reply("✏️ Enter custom report text:")
    await ReportStates.waiting_text.set()

@dp.message_handler(state=ReportStates.waiting_text)
async def report_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data["target"]
    reason = data["reason"]
    text = message.text.strip()

    await message.reply(f"🚀 Reporting {target} with reason {reason} and text: {text}...")

    for account in accounts_data["accounts"]:
        phone = account["phone"]
        api_id = account["api_id"]
        api_hash = account["api_hash"]
        session_file = f"sessions/{phone}.session"
        client = TelegramClient(session_file.replace(".session",""), api_id, api_hash)
        await client.connect()
        try:
            await client(functions.messages.ReportRequest(
                peer=target,
                reason=functions.messages.ReportReasonSpam(),  # you can adjust reason dynamically
                message=text
            ))
        except Exception as e:
            await message.reply(f"⚠️ Error reporting from {phone}: {e}")
        await client.disconnect()

    await message.reply("✅ Reporting completed!", reply_markup=main_menu())
    await state.finish()

# --- Run bot ---
if __name__ == "__main__":
    print("🤖 Bot is running...")
    executor.start_polling(dp, skip_updates=True)
