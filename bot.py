import os
import logging
import re
import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 10000))  # Порт для Render

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Настройки модерации
BANNED_WORDS = {"заработок", "работа", "команда"}
MAX_EMOJIS = 5
MAX_MESSAGES_FOR_NEW_USERS = 5
user_messages = {}

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    member = await bot.get_chat_member(chat_id, user_id)
    if member.is_chat_admin():
        await message.answer("Я ГОТОВ УБИВАТЬ.")

# Обработка сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def check_message(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    user_messages[user_id] = user_messages.get(user_id, 0) + 1
    emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F]", text))

    if (any(word in text for word in BANNED_WORDS) or emoji_count > MAX_EMOJIS) and user_messages[user_id] < MAX_MESSAGES_FOR_NEW_USERS:
        await bot.kick_chat_member(chat_id, user_id)

# HTTP-сервер для Render
async def handle_ping(request):
    return web.Response(text="pong")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# Самопинг
async def self_pinger():
    await asyncio.sleep(5)
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/ping"
    logging.info("Pinging self every 60 seconds to prevent sleep.")
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url) as response:
                    logging.info(f"Pinged self: {response.status}")
            except Exception as e:
                logging.warning(f"Ping failed: {e}")
            await asyncio.sleep(60)

# Основной запуск
async def main():
    await asyncio.gather(
        run_web_server(),
        self_pinger(),
        dp.start_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
