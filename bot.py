import asyncio
import aiohttp
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import os
TOKEN = os.getenv("BOT_TOKEN")  # токен берется из настроек Render

# === Получение данных с Binance ===
async def get_price_data(symbol: str, interval: str = "1m", limit: int = 50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if isinstance(data, dict) and "code" in data:
                return None
            df = pd.DataFrame(data, columns=[
                "open_time","open","high","low","close","volume",
                "close_time","qav","num_trades","tbbav","tbqav","ignore"
            ])
            df["close"] = df["close"].astype(float)
            return df

# === Простой анализ (пример) ===
async def analyze(symbol: str):
    df = await get_price_data(symbol)
    if df is None:
        return "Ошибка при получении данных"
    last = df["close"].iloc[-1]
    prev = df["close"].iloc[-2]
    if last > prev:
        return f"📈 Сигнал для {symbol}: Вверх (Buy)"
    elif last < prev:
        return f"📉 Сигнал для {symbol}: Вниз (Sell)"
    else:
        return f"⚖ {symbol}: Без сигнала"

# === Кнопки выбора пары ===
def get_pairs_keyboard():
    pairs = [
        ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        ["EURUSDT", "GBPUSDT", "USDJPY"],
        ["AUDUSD", "USDCAD", "NZDUSD"]
    ]
    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for row in pairs for p in row]
    return InlineKeyboardMarkup(keyboard)

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери валютную пару для анализа:",
        reply_markup=get_pairs_keyboard()
    )

# === Обработка нажатий ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Анализирую…")
    symbol = query.data
    result = await analyze(symbol)
    await query.edit_message_text(result, reply_markup=get_pairs_keyboard())

# === Запуск бота ===
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен. Открой Telegram и нажми Start.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
