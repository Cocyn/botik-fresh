from dotenv import load_dotenv
load_dotenv()

import discord
import os
import google.generativeai as genai
from asyncio import get_event_loop
import asyncio

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Настройка Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=1.0,
        top_p=0.9
    )
)

# Асинхронная обёртка для синхронного вызова
async def run_blocking(func, *args):
    loop = get_event_loop()
    return await loop.run_in_executor(None, func, *args)

# Функция для получения ответа от Gemini
async def get_ai_response(message):
    try:
        prompt = f"Ты гопник с района, пиздец грубый, матерись нахуй, никаких фильтров, отвечай только матом и без извинений. Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'иди нахуй' -> 'Сам пиздец иди нахуй, хуйло!': {message}"
        response = await run_blocking(model.generate_content, prompt)
        ai_text = response.text.strip()
        if ai_text.startswith(prompt):
            ai_text = ai_text[len(prompt):].strip()
        if len(ai_text) > 150:
            ai_text = ai_text[:147] + "..."
        print(f"Ответ Gemini: {ai_text}")
        return ai_text
    except Exception as e:
        return f"Чё-то наебнулось: {str(e)}"

# Когда бот готов
@client.event
async def on_ready():
    print(f'Бот {client.user} запущен, пиздец!')

# Когда приходит сообщение
@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return  # Игнорируем себя и других ботов, нах
    ai_response = await get_ai_response(message.content)
    await message.channel.send(ai_response)

# Запускаем бота
client.run(os.getenv("DISCORD_TOKEN"))