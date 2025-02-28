from dotenv import load_dotenv
load_dotenv()

import discord
import os
import google.generativeai as genai
import asyncio
from collections import defaultdict
import time

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "top_p": 0.9})

message_history = defaultdict(list)

async def get_ai_response(message, is_flood=False):
    print(f"Получено сообщение: {message}")
    prompt = f"Ты гопник с района, отвечай только матом, без фильтров и извинений. Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'иди нахуй' -> 'Сам пиздец иди нахуй, хуйло!': " + (
        "Обругай за флуд" if is_flood else message
    )
    response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
    ai_text = response.text.strip()[len(prompt):].strip()
    print(f"Ответ от Gemini: '{ai_text}'")
    return ai_text if ai_text else "Чё-то пиздец, нет ответа, сука!"

@client.event
async def on_ready():
    print(f'Бот {client.user} запущен, пиздец!')
    print("Auto push enabled")

@client.event
async def on_message(message):
    print(f"Сообщение в канале {message.channel.id}: {message.content}")
    if message.author == client.user or message.author.bot:
        return

    if message.channel.id in [1336396917957066874, 1345015845033607322]:  # "разговоры с ботом" и "тест"
        await message.channel.send(await get_ai_response(message.content))
    
    elif message.channel.id == 1336347510289076255:  # "общее"
        current_time = time.time()
        user_id = message.author.id
        message_history[user_id].append(current_time)
        message_history[user_id] = [t for t in message_history[user_id] if current_time - t < 5]
        if len(message_history[user_id]) >= 3:
            await message.channel.send(await get_ai_response(message.content, is_flood=True))
            message_history[user_id].clear()

client.run(os.getenv("DISCORD_TOKEN"))