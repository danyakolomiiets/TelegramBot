import os
import re
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ChatMemberUpdated
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверь .env файл.")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Запрещённые слова
BANNED_WORDS = ["заработок", "работа", "команда"]

# Функция для подсчёта эмоджи в сообщении
def count_emojis(text):
    emoji_pattern = re.compile(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\U0001F680-\U0001F6C0\U0001F1E0-\U0001F1FF]+', flags=re.UNICODE)
    return len(emoji_pattern.findall(text))

@dp.message_handler()
async def check_messages(message: types.Message):
    """ Проверяет количество сообщений пользователя в чате """
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Запрашиваем статистику сообщений в чате
    chat_member = await bot.get_chat_member(chat_id, user_id)
    messages_count = chat_member.user.id  # Количество сообщений в чате (айди члена чата)

    # Если юзер написал меньше 5 сообщений и использовал стоп-слово — бан
    if messages_count < 5 and any(word in message.text.lower() for word in BANNED_WORDS):
        try:
            await bot.kick_chat_member(chat_id, user_id)
            await message.reply(f"🔨 {message.from_user.first_name} я те дам блять заработок.")
        except Exception as e:
            await message.reply(f"⚠ Ошибка: {e}")

# Запуск бота
if __name__ == "__main__":
    print("✅ Бот запущен!")
    executor.start_polling(dp, skip_updates=True)
