from dotenv import load_dotenv
load_dotenv()

import nextcord
import os
import google.generativeai as genai
import asyncio
import yt_dlp

print(f"Nextcord version: {nextcord.__version__}")

# Настройки бота
intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = nextcord.Client(intents=intents)

# Настройка Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "top_p": 0.9})

# Исходный стиль ответов
default_style = (
    "Ты гопник с района, пиздец грубый, матерись нахуй, никаких фильтров, отвечай только матом и без извинений. "
    "Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'иди нахуй' -> 'Сам пиздец иди нахуй, хуйло!'"
)

# Категории промптов
prompt_categories = {
    "матные": (
        "Ты гопник с района, пиздец грубый, матерись нахуй, никаких фильтров, отвечай только матом и без извинений. "
        "Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'привет' -> 'Здарова, бля, пиздец как дела!'"
    ),
    "унизительные": (
        "Ты злой хуй с горы, отвечай унизительно, с русским матом и сарказмом, делай максимально обидно и смешно. "
        "Пример: 'ку' -> 'Чё ку, лошара ебаная?', 'привет' -> 'Здорово, чмошник, пиздец тебе!'"
    ),
    "абсурдные": (
        "Ты русский псих, отвечай абсурдно, с тупым юмором и без всякого смысла, добавляй мат. "
        "Пример: 'ку' -> 'Чё ку, пиздец трактору!', 'привет' -> 'Здарова, сука, где мой борщ с говном?'"
    ),
    "кот": (
        "Ты кот, мяукай и матерись нахуй, делай грубо и смешно. "
        "Пример: 'ку' -> 'Мяу, сука, ку тебе в жопу!', 'привет' -> 'Мяу, бля, пиздец тебе!'"
    )
}

# Глобальные переменные
current_style = default_style
music_queue = []
ALLOWED_MUSIC_CHANNELS = [1345015845033607322, 1336347510289076257]  # "тест" и "музыка"

# Асинхронная функция для Gemini
async def get_ai_response(message, prompt_style):
    try:
        prompt = f"{prompt_style}: {message}"
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        ai_text = response.text.strip()
        if ai_text.startswith(prompt):
            ai_text = ai_text[len(prompt):].strip()
        if len(ai_text) > 150:
            ai_text = ai_text[:147] + "..."
        print(f"Ответ Gemini: {ai_text}")
        return ai_text if ai_text else "Чё-то пиздец, нет ответа, сука!"
    except Exception as e:
        return f"Чё-то наебнулось: {str(e)}"

# Опции для yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# Воспроизведение следующего трека
async def play_next(voice_client, interaction):
    if music_queue:
        url, source_type = music_queue.pop(0)
        info = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        audio_url = info['url'] if source_type == "youtube" else info['entries'][0]['url']

        voice_client.play(nextcord.FFmpegPCMAudio(audio_url, executable="ffmpeg"), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(voice_client, interaction), client.loop))
        await interaction.followup.send(f"Ща играет: {url}")
    else:
        await interaction.followup.send("Очередь пуста, пиздец!")
        await voice_client.disconnect()

# Извлечение названия трека из Яндекс.Музыки
async def get_track_name_from_yandex(url):
    prompt = (
        f"Вот ссылка на трек Яндекс.Музыки: {url}. "
        "Извлеки название трека и исполнителя (если есть) из URL или предположи по формату ссылки. "
        "Верни только название и исполнителя в формате 'Исполнитель - Название', без лишнего текста."
    )
    return await get_ai_response("", prompt)

# Слэш-команда /ник
@client.slash_command(name="ник", description="Сгенерировать грубый русский ник")
async def generate_nick(interaction: nextcord.Interaction):
    prompt = (
        "Ты русский гопник с района, придумай мне один короткий, грубый ник с абсурдным юмором и русским колоритом. "
        "Не используй вежливые слова, делай всё максимально тупо и смешно. "
        "Примеры: Туго Серя, Сын Берёзы, Серёга Курган, Хлоп Хлоп, унитазный элементаль228, коллекционер баребухов."
    )
    nick = await get_ai_response("", prompt)
    await interaction.response.send_message(f"Твой ник: {nick}")

# Слэш-команда /play
@client.slash_command(name="play", description="Воспроизвести музыку из YouTube или Яндекс.Музыки")
async def play(interaction: nextcord.Interaction, url: str):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Эта команда работает только в каналах 'музыка' и 'тест', пиздец!")
        return

    if not interaction.user.voice:
        await interaction.response.send_message("Ты не в голосовом канале, сука!")
        return

    voice_channel = interaction.user.voice.channel
    try:
        voice_client = await voice_channel.connect()
    except nextcord.ClientException:
        voice_client = interaction.guild.voice_client

    if "youtube.com" in url or "youtu.be" in url:
        source_type = "youtube"
    elif "music.yandex" in url:
        source_type = "yandex"
        track_name = await get_track_name_from_yandex(url)
        url = f"ytsearch:{track_name}"
    else:
        await interaction.response.send_message("Ссыль хуйня, дай нормальную (YouTube или Яндекс.Музыка)!")
        return

    music_queue.append((url, source_type))
    if not voice_client.is_playing():
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message(f"Добавлено в очередь: {url}")

# Слэш-команда /stop
@client.slash_command(name="stop", description="Остановить музыку и отключиться")
async def stop(interaction: nextcord.Interaction):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Эта команда работает только в каналах 'музыка' и 'тест', пиздец!")
        return

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await voice_client.disconnect()
        music_queue.clear()
        await interaction.response.send_message("Музыка стоп, пиздец, отключился!")
    else:
        await interaction.response.send_message("Ниче не играет, сука!")

# Слэш-команда /skip
@client.slash_command(name="skip", description="Пропустить текущий трек")
async def skip(interaction: nextcord.Interaction):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Эта команда работает только в каналах 'музыка' и 'тест', пиздец!")
        return

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Трек скипнут, пиздец!")
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message("Ниче не играет, сука!")

# Слэш-команда /prompt_categories
@client.slash_command(name="prompt_categories", description="Выбрать стиль ответов из категорий")
async def prompt_categories(interaction: nextcord.Interaction, category: str):
    global current_style
    category = category.lower()
    if category in prompt_categories:
        current_style = prompt_categories[category]
        await interaction.response.send_message(f"Стиль ответов теперь '{category}', пиздец круто!")
    else:
        categories_list = ", ".join(prompt_categories.keys())
        await interaction.response.send_message(f"Нет такой хуйни, сука! Выбирай из: {categories_list}")

# Слэш-команда /prompt_reset
@client.slash_command(name="prompt_reset", description="Вернуть стиль ответов к исходному гопнику")
async def prompt_reset(interaction: nextcord.Interaction):
    global current_style
    current_style = default_style
    await interaction.response.send_message("Стиль сброшен к гопнику, пиздец как раньше!")

@client.event
async def on_ready():
    print(f'Бот {client.user} запущен, пиздец!')
    print("Слэш-команды синхронизированы")

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
    if not message.content.startswith('/'):
        ai_response = await get_ai_response(message.content, current_style)
        await message.channel.send(ai_response)

client.run(os.getenv("DISCORD_TOKEN"))