import os
import logging
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus
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

# Обработчик команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.reply("Привет! Этот бот банит за запрещённые слова, но только если это твоё первое сообщение в чате.")

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

    # Получаем информацию о пользователе
    user_info = await bot.get_chat_member(chat_id, user_id)

    # Проверяем, является ли пользователь новичком
    if user_info.status == ChatMemberStatus.RESTRICTED or user_info.status == ChatMemberStatus.LEFT:
        # Подсчёт эмодзи
        emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F]", text))

        # Если это первое сообщение в чате и оно нарушает правила — баним
        if any(word in text for word in BANNED_WORDS) or emoji_count > MAX_EMOJIS:
            await bot.ban_chat_member(chat_id, user_id)
            logging.info(f"Пользователь {message.from_user.full_name} ({user_id}) забанен в чате {chat_id}, так как это его первое сообщение.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())