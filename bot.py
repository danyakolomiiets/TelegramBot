import os
import logging
import re
import asyncio
import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаём сервер FastAPI, чтобы Render не отключал процесс
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is running"}

# Список запрещённых слов
BANNED_WORDS = {"заработок", "работа", "команда", "тест"}  # Добавили "тест" для проверки

# Максимальное количество эмодзи в сообщении
MAX_EMOJIS = 5

# Хранение данных о пользователях, кто уже написал хоть одно сообщение
user_messages = set()

# Обработчик команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    logging.info(f"/start от {message.from_user.full_name} ({message.from_user.id})")
    await message.reply("Я ГОТОВ УБИВАТЬ.")

# Обработчик сообщений
@dp.message()
async def check_message(message: types.Message):
    if not message.text:
        logging.info(f"Пропущено сообщение без текста от {message.from_user.id}")
        return  

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    logging.info(f"Получено сообщение от {message.from_user.full_name} ({user_id}): {text}")

    # Получаем список администраторов чата
    admins = [admin.user.id for admin in await bot.get_chat_administrators(chat_id)]

    # Если пользователь - админ, не баним его
    if user_id in admins:
        logging.info(f"Пользователь {message.from_user.full_name} ({user_id}) - АДМИН, не баним.")
        return

    # Если пользователь уже писал в чате, он не считается новичком
    if user_id in user_messages:
        logging.info(f"Пользователь {message.from_user.full_name} ({user_id}) уже писал в чате, не баним.")
        return

    # Добавляем пользователя в список тех, кто уже писал
    user_messages.add(user_id)
    logging.info(f"Пользователь {message.from_user.full_name} ({user_id}) - его первое сообщение в чате.")

    # Подсчёт эмодзи
    emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F]", text))

    # Если это первое сообщение в чате и оно нарушает правила — баним
    if any(word in text for word in BANNED_WORDS) or emoji_count > MAX_EMOJIS:
        logging.info(f"БАН {message.from_user.full_name} ({user_id}) за сообщение: {text}")
        await bot.ban_chat_member(chat_id, user_id)
    else:
        logging.info(f"Сообщение от {message.from_user.full_name} ({user_id}) не нарушает правил.")

# Функция для старта бота
async def run_bot():
    logging.info("Бот запущен и слушает сообщения...")
    await dp.start_polling(bot)

# Функция для запуска FastAPI и бота
def start():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

if __name__ == "__main__":
    start()