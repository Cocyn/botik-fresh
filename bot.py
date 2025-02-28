from dotenv import load_dotenv
load_dotenv()

import discord
from discord import app_commands
import os
import google.generativeai as genai
import asyncio

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Настройка Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "top_p": 0.9})

# Асинхронная функция для Gemini
async def get_ai_response(prompt):
    try:
        response = await asyncio.get_running_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        ai_text = response.text.strip()
        print(f"Ответ Gemini: {ai_text}")
        return ai_text if ai_text else "Чё-то пиздец, нет ника, сука!"
    except Exception as e:
        return f"Пиздец, ошибка: {str(e)}"

# Слэш-команда /ник
@tree.command(name="ник", description="Сгенерировать грубый русский ник")
async def generate_nick(interaction: discord.Interaction):
    prompt = (
        "Ты русский гопник с района, придумай мне один короткий, грубый ник с абсурдным юмором и русским колоритом. "
        "Не используй вежливые слова, делай всё максимально тупо и смешно. "
        "Примеры: Туго Серя, Сын Берёзы, Серёга Курган, Хлоп Хлоп, унитазный элементаль228, коллекционер баребухов, "
        "сектор пудж, Я Hy6uK Tы Tpynuk, олежа трансмиссия, ВсЕ УмРуТ а Я гРеЙфРуКт, шиноби скрытого пула, "
        "буханка пива, анальная мозоль, пт на клизму, полноприводная мaндaвошка, синичка без яичка, задоджил аборт."
    )
    nick = await get_ai_response(prompt)
    await interaction.response.send_message(f"Твой ник: {nick}")

# Когда бот готов
@client.event
async def on_ready():
    print(f'Бот {client.user} запущен, пиздец!')
    await tree.sync()  # Синхронизация слэш-команд
    print("Слэш-команды синхронизированы")

# Запуск бота
client.run(os.getenv("DISCORD_TOKEN"))