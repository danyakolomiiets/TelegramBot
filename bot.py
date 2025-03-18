import os
import logging
import re
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Удаляем вебхук перед запуском
requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
