import os
import re
import logging
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.fsm.storage.memory import MemoryStorage

# 🎯 Логирование ошибок
logging.basicConfig(level=logging.INFO)

# 🔥 Настройки
TOKEN = os.getenv("TOKEN", "7888371111:AAEdOKdeLH1fmZygscWXttr4vwwQGwrJNTk")  # ЗАМЕНИ НА СВОЙ ТОКЕН
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegrambot-tnm7.onrender.com/")  # Твой Render URL

if not TOKEN or "7888371111:AAEdOKdeLH1fmZygscWXttr4vwwQGwrJNTk" in TOKEN:
    raise ValueError("🚨 Ошибка! Укажи правильный TOKEN в переменных окружения!")

# 🔥 Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🔹 FastAPI сервер
app = FastAPI()

# 🔹 Стоп-слова и лимит эмодзи
STOP_WORDS = {"заработок", "работа", "команда"}
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F6FF]', re.UNICODE)
MESSAGE_LIMIT = 5

# 🔹 Храним количество сообщений пользователей
user_messages = {}

async def get_user_messages_count(chat_id: int, user_id: int):
    """ Проверка количества сообщений пользователя """
    chat = await bot.get_chat(chat_id)
    members = await bot.get_chat_administrators(chat_id)

    for member in members:
        if member.user.id == user_id:
            return MESSAGE_LIMIT + 1  # Не баним админов

    return user_messages.get((chat_id, user_id), 0)

@dp.message()
async def check_message(message: types.Message):
    """ Проверка сообщений пользователей на стоп-слова и спам эмодзи """
    if not message.text:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    user_messages[(chat_id, user_id)] = user_messages.get((chat_id, user_id), 0) + 1
    msg_count = await get_user_messages_count(chat_id, user_id)

    if any(word in text for word in STOP_WORDS):
        if msg_count < MESSAGE_LIMIT:
            await bot.ban_chat_member(chat_id, user_id)
            await message.answer(f"🚫 Пользователь @{message.from_user.username} забанен за нарушение правил.")
            return

    if len(EMOJI_PATTERN.findall(text)) > 5:
        if msg_count < MESSAGE_LIMIT:
            await bot.ban_chat_member(chat_id, user_id)
            await message.answer(f"🚫 Пользователь @{message.from_user.username} забанен за спам эмодзи.")
            return

@app.post("/")
async def process_webhook(request: Request):
    """ Обрабатывает входящие запросы от Telegram """
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logging.error(f"❌ Ошибка в обработке вебхука: {e}")
        return {"ok": False, "error": str(e)}

@app.on_event("startup")
async def on_startup():
    """ Устанавливаем вебхук при старте сервера """
    webhook_info = await bot.get_webhook_info()
    
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"✅ Webhook установлен на {WEBHOOK_URL}")

if __name__ == "__main__":
    import uvicorn
    logging.info("🚀 Запускаем сервер на 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)