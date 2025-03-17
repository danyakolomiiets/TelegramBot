import os
import re
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# 🔹 Получаем токен и вебхук URL из переменных окружения
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Укажи этот URL в Render

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("🚨 Ошибка! TOKEN или WEBHOOK_URL не найдены. Проверь переменные окружения в Render!")

# 🔹 Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🔹 Создаем Aiohttp-приложение
app = web.Application()

# 🔹 Регистрируем вебхук в aiogram
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)

# 🔹 Храним количество сообщений пользователей
user_messages = {}

# 🔹 Стоп-слова и лимит эмодзи
STOP_WORDS = {"заработок", "работа", "команда"}
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F6FF]', re.UNICODE)  # Поиск эмодзи
MESSAGE_LIMIT = 5  # Лимит сообщений

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

async def set_webhook():
    """ Устанавливает вебхук """
    webhook_info = await bot.get_webhook_info()
    
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Webhook установлен на {WEBHOOK_URL}")

async def on_startup(app):
    """ Выполняется при старте приложения """
    await set_webhook()

app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=8080)  # Запуск веб-приложения
