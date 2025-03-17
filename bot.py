import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Проверяем, видит ли бот переменную
print(f"🔍 Проверка BOT_TOKEN: {TOKEN}")

if not TOKEN:
    raise ValueError("🚨 Ошибка! BOT_TOKEN не найден. Проверь .env или переменные окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Стоп-слова и лимит эмодзи
STOP_WORDS = {"заработок", "работа", "команда"}
EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F6FF]', re.UNICODE)  # Поиск эмодзи
MESSAGE_LIMIT = 5  # Лимит сообщений

# Храним количество сообщений пользователей
user_messages = {}

# Функция для проверки количества сообщений
async def get_user_messages_count(chat_id: int, user_id: int):
    chat = await bot.get_chat(chat_id)
    members = await bot.get_chat_administrators(chat_id)

    # Проверяем, есть ли пользователь в админах (не баним админов)
    for member in members:
        if member.user.id == user_id:
            return MESSAGE_LIMIT + 1  # Делаем вид, что он отправил больше 5 сообщений

    return user_messages.get((chat_id, user_id), 0)

# Обработчик новых сообщений
@dp.message()
async def check_message(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    # Считаем количество сообщений пользователя
    user_messages[(chat_id, user_id)] = user_messages.get((chat_id, user_id), 0) + 1
    msg_count = await get_user_messages_count(chat_id, user_id)

    # Проверяем наличие стоп-слов
    if any(word in text for word in STOP_WORDS):
        if msg_count < MESSAGE_LIMIT:
            await bot.ban_chat_member(chat_id, user_id)
            await message.answer(f"🚫 Пользователь @{message.from_user.username} забанен за нарушение правил.")
            return

    # Проверяем количество эмодзи
    if len(EMOJI_PATTERN.findall(text)) > 5:
        if msg_count < MESSAGE_LIMIT:
            await bot.ban_chat_member(chat_id, user_id)
            await message.answer(f"🚫 Пользователь @{message.from_user.username} забанен за спам эмодзи.")
            return

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())