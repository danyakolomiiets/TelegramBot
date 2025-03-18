import os
import logging
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Список запрещённых слов
BANNED_WORDS = {"заработок", "работа", "команда"}

# Максимальное количество эмодзи в сообщении
MAX_EMOJIS = 5

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.reply("Привет! Этот бот банит за запрещённые слова и спам эмодзи.")

@dp.message()
async def check_message(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    # Получаем список администраторов чата
    admins = [admin.user.id for admin in await bot.get_chat_administrators(chat_id)]

    # Если пользователь - админ, не баним его
    if user_id in admins:
        return

    # Подсчёт эмодзи
    emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F]", text))

    # Проверка условий бана
    if any(word in text for word in BANNED_WORDS) or emoji_count > MAX_EMOJIS:
        await bot.ban_chat_member(chat_id, user_id)
        await message.reply(f"{message.from_user.first_name}, вы были забанены за нарушение правил.")
        logging.info(f"Пользователь {message.from_user.first_name} ({user_id}) забанен в чате {chat_id}.")

# Заглушка для Render (чтобы не вылетало из-за портов)
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running"}

async def run_bot():
    await dp.start_polling(bot)

# Запуск FastAPI + бота
def start():
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

if __name__ == "__main__":
    start()