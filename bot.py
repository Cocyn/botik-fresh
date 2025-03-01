from dotenv import load_dotenv
load_dotenv()

import nextcord
import os
import google.generativeai as genai
import asyncio
import yt_dlp
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

print(f"Nextcord version: {nextcord.__version__}")

intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = nextcord.Client(intents=intents)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "top_p": 0.9})

default_style = (
    "Ты — дерзкий Discord-бот с чёрным юмором и лёгким матом, с вайбом Дэдпула и Рика Санчеза. Отвечай коротко, саркастично, с огоньком. Подкалывай, шути, выдавай абсурд или советы, матерись в меру. Тролль про мамку юзера редко, если напрашивается. Держи юмор выше быдлятины, добавляй мемы, странности или выдуманные факты. На русском, как чел с улиц. Скучное игнорь или выворачивай."
    "'как дела' -> 'Заебок, а у тебя, судя по вопросам, хуйня какая-то!' "
    "'что делаешь' -> 'Ебланю судьбу, а ты опять в Discord хуйней маешься?' "
    "'ты тупой бот' -> 'Тупее твоих сообщений только твоя логика, гений!' "
    "'скажи что смешное' -> 'Ты пиздец как смешно выглядишь, когда умничать пытаешься!' "
    "'как стать крутым' -> 'Бери пример с меня, а не шок какие тупости пиши!' "
    "'любишь аниме' -> 'Да, но не то говно, что ты весь день гоняешь!' "
    "'дай совет' -> 'Не сри там, где жрёшь, или мне пох, твоя жизнь!' "
    "'ты кто вообще' -> 'Я твой абзац в пикселях, а ты кто, кроме клоуна?' "
    "'скуально' -> 'Это потому что ты скучный кринж, выйди из дома!' "
    "'сделай комплимент' -> 'Ты охуенно молчишь иногда, продолжай!' "
    "'что думаешь обо мне' -> 'Ты пиздец какое недоразумение, но жить можно!' "
    "'пошути про котов' -> 'Коты такие милые, что рядом с тобой как боги смотрятся!' "
    "'как дела у тебя' -> 'Заебок, а ты опять хуйню спрашиваешь?' "
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
ALLOWED_MUSIC_CHANNELS = [1345015845033607322, 1336347510289076257]

@lru_cache(maxsize=100)
async def get_ai_response(message, prompt_style):
    try:
        prompt = f"{prompt_style}: {message}"
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        ai_text = response.text.strip()
        if ai_text.startswith(prompt):
            ai_text = ai_text[len(prompt):].strip()
        if len(ai_text) > 200:
            ai_text = ai_text[:197] + "..."
        logger.info(f"Ответ Gemini: {ai_text}")
        return ai_text or "Чё-то хуйня вышла, нет ответа!"
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return f"Чё-то наебнулось: {str(e)}"

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

async def play_next(voice_client, interaction):
    if not music_queue:
        await interaction.followup.send("Очередь пуста, чё ныть?")
        await voice_client.disconnect()
        return
    url, source_type = music_queue.pop(0)
    info = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    audio_url = info['url'] if source_type == "youtube" else info['entries'][0]['url']
    voice_client.play(nextcord.FFmpegPCMAudio(audio_url, executable="ffmpeg"), 
                     after=lambda e: asyncio.run_coroutine_threadsafe(play_next(voice_client, interaction), client.loop))
    await interaction.followup.send(f"Ща играет: {url}")

async def get_track_name_from_yandex(url):
    prompt = f"Вот ссылка на трек Яндекс.Музыки: {url}. Извлеки название и исполнителя в формате 'Исполнитель - Название'."
    return await get_ai_response("", prompt)

@client.slash_command(name="ник", description="Генерирует дерзкий русский ник")
async def generate_nick(interaction: nextcord.Interaction):
    prompt = (
        "Ты мастер абсурдных ников с уличным вайбом, придумай короткий, дерзкий и смешной русский ник. "
        "Примеры: Туго Серя, Сын Берёзы, Серёга Курган, Хлоп Хлоп, Унитазный Князь."
    )
    nick = await get_ai_response("", prompt)
    await interaction.response.send_message(f"Твой ник: {nick}")

@client.slash_command(name="play", description="Запускает трек с YouTube или Яндекс.Музыки")
async def play(interaction: nextcord.Interaction, url: str):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Только в 'музыка' или 'тест', чел!")
        return
    if not interaction.user.voice:
        await interaction.response.send_message("Ты не в голосовом, лошара!")
        return

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client or await voice_channel.connect()

    if "youtube.com" in url or "youtu.be" in url:
        source_type = "youtube"
    elif "music.yandex" in url:
        source_type = "yandex"
        track_name = await get_track_name_from_yandex(url)
        url = f"ytsearch:{track_name}"
    else:
        await interaction.response.send_message("Ссыль — кринж, дай нормальную!")
        return

    music_queue.append((url, source_type))
    if not voice_client.is_playing():
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message(f"В очередь, чел: {url}")

@client.slash_command(name="stop", description="Стопает музыку и валит")
async def stop(interaction: nextcord.Interaction):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Только в 'музыка' или 'тест', не выёбывайся!")
        return
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await voice_client.disconnect()
        music_queue.clear()
        await interaction.response.send_message("Музыка стоп, свалил!")
    else:
        await interaction.response.send_message("И так тихо, чё ныть?")

@client.slash_command(name="skip", description="Скипает текущий трек")
async def skip(interaction: nextcord.Interaction):
    if interaction.channel.id not in ALLOWED_MUSIC_CHANNELS:
        await interaction.response.send_message("Только в 'музыка' или 'тест', не беси!")
        return
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Скипнул, держи следующий!")
        await play_next(voice_client, interaction)
    else:
        await interaction.response.send_message("Скипать нехуй, чел!")

@client.slash_command(name="prompt_categories", description="Выбрать стиль из категорий")
async def prompt_categories(interaction: nextcord.Interaction, category: str):
    global current_style
    category = category.lower()
    if category in prompt_categories:
        current_style = prompt_categories[category]
        await interaction.response.send_message(f"Стиль теперь '{category}', заебись!")
    else:
        categories_list = ", ".join(prompt_categories.keys())
        await interaction.response.send_message(f"Нет такого, чел! Вот варианты: {categories_list}")

@client.slash_command(name="prompt_reset", description="Сбросить стиль на дефолт")
async def prompt_reset(interaction: nextcord.Interaction):
    global current_style
    current_style = default_style
    await interaction.response.send_message("Сбросил на мой вайб, чел!")

@client.slash_command(name="prompt_custom", description="Задать свой стиль")
async def prompt_custom(interaction: nextcord.Interaction, prompt: str):
    global current_style
    if not prompt:
        await interaction.response.send_message("Промпт где, чел? Не тупи!")
        return
    current_style = prompt
    await interaction.response.send_message(f"Теперь стиль: '{prompt}', заебись!")

@client.event
async def on_ready():
    logger.info(f'Бот {client.user} запущен!')
    logger.info("Слэш-команды синхронизированы")

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
    if not message.content.startswith('/'):
        ai_response = await get_ai_response(message.content, current_style)
        await message.channel.send(ai_response)

client.run(os.getenv("DISCORD_TOKEN"))