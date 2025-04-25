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
BANNED_WORDS = {
    "заработок", "работа", "команда", "Доход", "доход", "Заработок", "Работа", "Команда",
    "требуются", "Требуются", "требуется", "Требуется", "Оплата", "оплата", "Удаленка", "удаленка",
    "Партнёрство", "партнёрство", "Партнерство", "партнерство", "заработать", "удаленную",
    "Удаленную", "удаленной", "Удаленной", "деятельности", "Деятельности", "партнеров", "ознакомлю",
    "доп. заработке", "дополнительного заработка", "дополнительного дохода",
    "от 18 лет", "строго от 18", "прибыль", "прибыль вы получите", "получите уже в первый",
    "в первый дни", "всё легально", "все легально", "гарантируем безопасность",
    "доведем вас", "доведём вас", "за ручку", "брокерской компанией",
    "Binance", "биржи", "криптовалютной", "сотрудничества", "предложение приносит",
    "приносит от", "рублей в неделю", "рублей в день", "прибыльное предложение",
    "подработка", "совмещать с основной", "доход не заморачиваясь", "прибыль до",
    "прибыль в неделю", "может быть интересным", "интересен как новичкам", "в личку",
    "в смс", "плюсик", "плюсики", "вышлю предложение", "высылай предложение",
    "обращаюсь к каждому", "советую обратить внимание", "в лс за подробностями",
    "подробней", "напишите мне", "написать мне", "напиши мне", "жду +", "жду плюс",
    "онлайн", "в неделю", "в день", "телефона", "телефон", "компьютера",
    "свободного времени", "свободное время", "не упускай шанс", "подробности",
    "пиши в лс", "в лс за подробностями", "в личные сообщения", "личные сообщения",
    "заинтересованных", "++", "плюс", "+ в лс", "+ в личку", "долларов",
    "возможность получать прибыль", "зарабатывать и расти", "дистанционная занятость",
    "удалённая занятость", "формат, который приносит", "не выходя из дома"
}
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
        await message.delete()
        logging.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) был забанен в чате {chat_id} за подозрительное сообщение.")

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
