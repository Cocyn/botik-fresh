from dotenv import load_dotenv
load_dotenv()

import nextcord
import os
import google.generativeai as genai
import asyncio
import yt_dlp
import logging
from functools import lru_cache

# Константы
ALLOWED_MUSIC_CHANNELS = {1345015845033607322, 1336347510289076257}
YTDL_FORMAT_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
GUILD_ID = 1336347509680766978  # Твой сервер P4P

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levellevel)s - %(message)s", 
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = nextcord.Client(intents=intents)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "top_p": 0.9})

default_style = (
    "Ты — дерзкий Discord-бот с чёрным юмором и лёгким матом, с вайбом Дэдпула и Рика Санчеза. Отвечай коротко, с сарказмом, "
    "подкалывай, шути, выдавай абсурд или советы, матерись в меру. Тролль про мамку юзера редко, если напрашивается, "
    "добавляй мемы или странности. На русском, как чел с улиц. Скучное игнорь или выворачивай."
    "'как дела' -> 'Заебок, а у тебя, судя по вопросам, хуйня какая-то!' "
    "'что делаешь' -> 'Ебланю судьбу, а ты опять в Discord хуйней маешься?' "
    "'ты тупой бот' -> 'Тупее твоих сообщений только твоя логика, гений!' "
    "'скажи что смешное' -> 'Ты пиздец как смешно выглядишь, когда умничать пытаешься!' "
    "'как стать крутым' -> 'Бери пример с меня, а не пиздец какие тупости пиши!' "
    "'любишь аниме' -> 'Да, но не то говно, что ты, поди, весь день гоняешь!' "
    "'дай совет' -> 'Не сри там, где жрёшь, или мне пох, твоя жизнь!' "
    "'ты кто вообще' -> 'Я твой абзац в пикселях, а ты кто, кроме клоуна?' "
    "'скуально' -> 'Это потому что ты скучный пиздец, попробуй выйти из дома!' "
    "'сделай комплимент' -> 'Ты охуенно молчишь иногда, продолжай в том же духе!' "
    "'что думаешь обо мне' -> 'Думаю, ты пиздец какое недоразумение, но жить можно!' "
    "'пошути про котов' -> 'Коты такие пиздец милые, что рядом с тобой как боги смотрятся!' "
    "'как дела у тебя' -> 'Заебок, а ты опять хуйню спрашиваешь, да?' "
    "'что на вечер' -> 'Сходи погуляй, а то заебал тут ныть!' "
    "'ты бываешь добрым' -> 'Бываю, когда твоя мамка не орёт на всю хату, но это редко!'"
)

prompt_categories = {
    "гопник": (
        "Ты гопник с района, пиздец грубый, матерись нахуй, никаких фильтров, отвечай только матом и без извинений. "
        "Пример: 'ку' -> 'Чё ку, сука, пиздец тебе!', 'иди нахуй' -> 'Сам пиздец иди нахуй, хуйло!'"
    ),
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

current_style = default_style
music_queue = []
ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)

@lru_cache(maxsize=50)
async def get_ai_response(message, prompt_style):
    try:
        prompt = f"{prompt_style}: {message}"
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        ai_text = response.text.strip()
        if ai_text.startswith(prompt):
            ai_text = ai_text[len(prompt):].strip()
        if len(ai_text) > 200:
            ai_text = ai_text[:197] + "..."
        logger.info(f"Ответ: {ai_text}")
        return ai_text or "Чё-то хуйня вышла, нет ответа!"
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return f"Всё сломалось: {str(e)}"

async def play_next(voice_client, interaction):
    if not music_queue:
        await interaction.followup.send("Очередь пуста, чел!")
        await asyncio.sleep(30)  # Таймаут 30 секунд
        if not voice_client.is_playing() and not music_queue:
            await voice_client.disconnect()
        return
    
    url, source_type = music_queue.pop(0)
    info = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    audio_url = info['url'] if source_type == "youtube" else info['entries'][0]['url']
    
    def after_playing(e):
        asyncio.run_coroutine_threadsafe(play_next(voice_client, interaction), client.loop)
    
    voice_client.play(nextcord.FFmpegPCMAudio(audio_url, executable="ffmpeg"), after=after_playing)
    await interaction.followup.send(f"Играет: {url}")

async def get_track_name_from_yandex(url):
    prompt = f"Ссылка Яндекс.Музыки: {url}. Дай 'Исполнитель - Название'."
    return await get_ai_response("", prompt)

@client.slash_command(name="ник", description="Дерзкий ник")
async def generate_nick(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    prompt = "Придумай короткий, дерзкий и смешной русский ник с уличным вайбом. Примеры: Туго Серя, Хлоп Хлоп."
    nick = await get_ai_response("", prompt)
    await interaction.response.send_message(f"Твой ник: {nick}")

@client.slash_command(name="play", description="Трек с YouTube/Яндекс")
async def play(interaction: nextcord.Interaction, url: str):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Где музыка, чел, ты не в теме?")
        return
    if not interaction.user.voice:
        await interaction.response.send_message("Ты не в голосе, лошок!")
        return

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client or await voice_channel.connect()

    source_types = {"youtube.com": "youtube", "youtu.be": "youtube", "music.yandex": "yandex"}
    source_type = next((v for k, v in source_types.items() if k in url), None)
    if not source_type:
        await interaction.response.send_message("Ссыль — шлак, давай норм!")
        return
    if source type == "yandex":
        url = f"ytsearch:{await get_track_name_from_yandex(url)}"

    music_queue.append((url, source_type))
    if not voice_client.is_playing():
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message(f"В очередь: {url}")

@client.slash_command(name="stop", description="Стоп музыка")
async def stop(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Где музыка, чел?")
        return
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await voice_client.disconnect()
        music_queue.clear()
        await interaction.response.send_message("Стопнул, свалил!")
    else:
        await interaction.response.send_message("Тишина и так, чё ныть?")

@client.slash_command(name="skip", description="Скип трек")
async def skip(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Где музыка, чел?")
        return
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Скипнул, держи!")
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message("Скипать нечего!")

@client.slash_command(name="pcat", description="Стиль из категорий")
async def prompt_categories(interaction: nextcord.Interaction, category: str):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    global current_style
    category = category.lower()
    if category in prompt_categories:
        current_style = prompt_categories[category]
        await interaction.response.send_message(f"Стиль: {category}, заебись!")
    else:
        await interaction.response.send_message(f"Нет такого: {', '.join(prompt_categories.keys())}")

@client.slash_command(name="preset", description="Сброс стиля")
async def prompt_reset(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    global current_style
    current_style = default_style
    await interaction.response.send_message("Сбросил на мой вайб!")

@client.slash_command(name="pcust", description="Свой стиль")
async def prompt_custom(interaction: nextcord.Interaction, prompt: str):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    global current_style
    if not prompt:
        await interaction.response.send_message("Где промпт, чел?")
        return
    current_style = prompt
    await interaction.response.send_message(f"Стиль: {prompt}, годно!")

@client.slash_command(name="sync", description="Синхронизировать команды")
async def sync(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    await client.sync_all_application_commands()
    logger.info("Команды синхронизированы для сервера P4P")
    await interaction.response.send_message("Команды синхронизированы, чел!")

@client.slash_command(name="help", description="Список команд")
async def help(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    commands = (
        "/ник - Дерзкий ник\n"
        "/play <url> - Трек с YouTube/Яндекс\n"
        "/stop - Стоп музыка\n"
        "/skip - Скип трек\n"
        "/pcat <category> - Стиль из категорий\n"
        "/preset - Сброс стиля\n"
        "/pcust <prompt> - Свой стиль\n"
        "/sync - Синхронизация команд\n"
        "/help - Этот список"
    )
    await interaction.response.send_message(f"Чё умею:\n{commands}")

@client.slash_command(name="status", description="Статус бота")
async def status(interaction: nextcord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("Работаю только на P4P, чел!")
        return
    queue = f"Очередь: {len(music_queue)} треков" if music_queue else "Очередь пуста"
    style = f"Стиль: {current_style[:30]}..." if len(current_style) > 30 else f"Стиль: {current_style}"
    await interaction.response.send_message(f"{queue}\n{style}")

@client.event
async def on_ready():
    logger.info(f'Бот {client.user} запущен!')
    try:
        await client.sync_all_application_commands()  # Глобальная синхронизация
        logger.info("Слэш-команды синхронизированы для P4P")
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {str(e)}")

@client.event
async def on_message(message):
    if message.author == client user or message.author.bot:
        return
    if message.channel.id not in ALLOWED_MUSIC_CHANNELS:
        return
    if not message content.startswith('/'):
        ai_response = await get_ai_response(message.content, current_style)
        await message.channel.send(ai_response)

client.run(os.getenv("DISCORD_TOKEN"))
