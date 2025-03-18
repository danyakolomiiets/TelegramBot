import os
import logging
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список запрещённых слов
BANNED_WORDS = {"заработок", "работа", "команда"}

# Максимальное количество эмодзи в сообщении
MAX_EMOJIS = 5

# Минимальное количество сообщений, чтобы не считаться новичком
MESSAGE_LIMIT = 5

# Хранение количества сообщений пользователей
user_messages = {}

# Обработчик команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.reply("Я ГОТОВ УБИВАТЬ.")

# Обработчик сообщений
@dp.message()
async def check_message(message: types.Message):
    if not message.text:
        return  # Пропускаем сообщения без текста (например, фото)

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    # Получаем список администраторов чата
    admins = [admin.user.id for admin in await bot.get_chat_administrators(chat_id)]

    # Если пользователь - админ, не баним его
    if user_id in admins:
        return

    # Увеличиваем количество сообщений пользователя
    user_messages[user_id] = user_messages.get(user_id, 0) + 1

    # Если пользователь написал 5+ сообщений, он уже не новичок
    if user_messages[user_id] >= MESSAGE_LIMIT:
        return

    # Подсчёт эмодзи
    emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F]", text))

    # Проверка условий бана (если человек новичок)
    if any(word in text for word in BANNED_WORDS) or emoji_count > MAX_EMOJIS:
        await bot.ban_chat_member(chat_id, user_id)
        logging.info(f"Пользователь {message.from_user.full_name} ({user_id}) забанен в чате {chat_id}, так как он новичок.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())