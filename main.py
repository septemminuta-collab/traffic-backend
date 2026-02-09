import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8526257359:AAGBveK0Hcg8Fcfl1QHUBKQ7U1rHg7-JenA"
GAME_URL = " https://septemminuta-collab.github.io/crypto_game/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def start(m: types.Message):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    conn.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="ГРАТИ ТА ЗАРОБЛЯТИ 🎮", web_app=WebAppInfo(url=GAME_URL))
    ]])
    await m.answer(f"Привіт, {m.from_user.first_name}! Твій баланс збережено. Тисни кнопку:", reply_markup=kb)

async def main():
    init_db()
    await dp.start_polling(bot)


from aiohttp import web

# Функція для обробки запиту від гри
async def handle_reward(request):
    data = await request.json()
    user_id = data.get('user_id')
    points = data.get('points', 0)
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()
    return web.json_response({"status": "ok"})

# Запуск веб-сервера разом з ботом
async def main():
    init_db()
    app = web.Application()
    app.router.add_post('/reward', handle_reward)
    
    # Запускаємо бота
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
