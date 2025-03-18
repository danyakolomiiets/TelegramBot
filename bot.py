import os
import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Список запрещённых слов
BANNED_WORDS = {"заработок", "работа", "команда"}

# Максимальное количество эмодзи в сообщении
MAX_EMOJIS = 5

@dp.message_handler(content_types=types.ContentType.TEXT)
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
        await bot.kick_chat_member(chat_id, user_id)
        await message.reply(f"{message.from_user.first_name}, вы были забанены за нарушение правил.")
        logging.info(f"Пользователь {message.from_user.first_name} ({user_id}) забанен в чате {chat_id}.")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
