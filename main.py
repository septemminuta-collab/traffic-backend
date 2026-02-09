import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Налаштування логування для відстеження помилок
logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8526257359:AAGBveK0Hcg8Fcfl1QHUBKQ7U1rHg7-JenA"
GAME_URL = "https://septemminuta-collab.github.io/crypto_game/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

# --- ОБРОБКА КОМАНД БОТА ---
@dp.message(Command("start"))
async def start(m: types.Message):
    user_id = m.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    
    # Отримуємо поточний баланс для привітання
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    balance = res[0] if res else 0
    conn.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="ГРАТИ ТА ЗАРОБЛЯТИ 🎮", web_app=WebAppInfo(url=GAME_URL))
    ]])
    await m.answer(
        f"Привіт, {m.from_user.first_name}!\n"
        f"Твій баланс: 💰 {balance} балів.\n"
        "Тисни кнопку нижче, щоб почати майнінг:", 
        reply_markup=kb
    )

# --- ОБРОБКА ЗАПИТІВ ВІД ГРИ (API) ---
async def handle_reward(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        points = data.get('points', 0)
        
        if not user_id:
            return web.json_response({"error": "no_user_id"}, status=400)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        # Додаємо бали до існуючого балансу
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (points, user_id))
        conn.commit()
        conn.close()
        
        logging.info(f"Нараховано {points} балів користувачу {user_id}")
        
        # Додаємо заголовки CORS, щоб браузер не блокував запит
        return web.json_response({"status": "ok", "new_reward": points}, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    except Exception as e:
        logging.error(f"Помилка API: {e}")
        return web.json_response({"error": str(e)}, status=500)

# Додатковий метод для CORS (браузери спочатку шлють OPTIONS)
async def handle_options(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

# --- ЗАПУСК УСЬОГО РАЗОМ ---
async def main():
    init_db()
    
    # Створюємо веб-сервер aiohttp
    app = web.Application()
    app.router.add_post('/reward', handle_reward)
    app.router.add_options('/reward', handle_options)
    
    runner = web.AppRunner(app)
    await runner.setup()
    # Render автоматично надає порт 10000 для безкоштовних сервісів
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    
    logging.info("API сервер запущено на порту 10000")
    
    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
