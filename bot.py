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

# Исходный стиль ответов
default_style = (
    "Ты гопник с района, пиздец грубый, матерись нахуй, никаких фильтров, отвечай только матом и без извинений. "
    "Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'иди нахуй' -> 'Сам пиздец иди нахуй, хуйло!'"
)

# Глобальная переменная для текущего стиля
current_style = default_style

# Асинхронная функция для Gemini
async def get_ai_response(message, prompt_style):
    try:
        prompt = f"{prompt_style}: {message}"
        response = await asyncio.get_running_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        ai_text = response.text.strip()
        if ai_text.startswith(prompt):
            ai_text = ai_text[len(prompt):].strip()
        if len(ai_text) > 150:
            ai_text = ai_text[:147] + "..."
        print(f"Ответ Gemini: {ai_text}")
        return ai_text if ai_text else "Чё-то пиздец, нет ответа, сука!"
    except Exception as e:
        return f"Чё-то наебнулось: {str(e)}"

# Слэш-команда /ник
@tree.command(name="ник", description="Сгенерировать грубый русский ник")
async def generate_nick(interaction: discord.Interaction):
    prompt = (
        "Ты русский гопник с района, придумай мне один короткий, грубый ник с абсурдным юмором и русским колоритом. "
        "Не используй вежливые слова, делай всё максимально тупо и смешно. "
        "Примеры: Туго Серя, Сын Берёзы, Серёга Курган, Хлоп Хлоп, унитазный элементаль228, коллекционер баребухов."
    )
    nick = await get_ai_response("", prompt)
    await interaction.response.send_message(f"Твой ник: {nick}")

# Слэш-команда /промпт
@tree.command(name="промпт", description="Обновить стиль ответов бота")
@app_commands.describe(style="Введи новый стиль ответов (например, 'Ты кот, мяукай')")
async def update_prompt(interaction: discord.Interaction, style: str):
    global current_style
    current_style = style
    await interaction.response.send_message(f"Стиль ответов обновлён на: '{style}'")

# Слэш-команда /сброс
@tree.command(name="сброс", description="Вернуть стиль ответов к исходному")
async def reset_prompt(interaction: discord.Interaction):
    global current_style
    current_style = default_style
    await interaction.response.send_message("Стиль ответов сброшен к исходному, пиздец!")

# Когда бот готов
@client.event
async def on_ready():
    print(f'Бот {client.user} запущен, пиздец!')
    await tree.sync()  # Синхронизация слэш-команд
    print("Слэш-команды синхронизированы")

# Обработка текстовых сообщений
@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
    if not message.content.startswith('/'):  # Игнорируем слэш-команды
        ai_response = await get_ai_response(message.content, current_style)
        await message.channel.send(ai_response)

# Запуск бота
client.run(os.getenv("DISCORD_TOKEN"))