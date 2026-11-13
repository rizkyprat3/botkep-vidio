import os
import re
import asyncio
import traceback
from pathlib import Path

import discord
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


VIDEO_PATTERNS = (
    # YouTube
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/",
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?",
    r"(?:https?://)?youtu\.be/",

    # TikTok
    r"(?:https?://)?(?:www\.)?tiktok\.com/@[^/]+/video/",

    # Instagram
    r"(?:https?://)?(?:www\.)?instagram\.com/reel/",
    r"(?:https?://)?(?:www\.)?instagram\.com/p/",

    # Facebook
    r"(?:https?://)?(?:www\.)?facebook\.com/reel/",
    r"(?:https?://)?(?:www\.)?facebook\.com/.+/videos/",
    r"(?:https?://)?(?:www\.)?fb\.watch/",

    # X / Twitter
    r"(?:https?://)?(?:www\.)?x\.com/[^/]+/status/",
    r"(?:https?://)?(?:www\.)?twitter\.com/[^/]+/status/",
)

URL_PATTERN = re.compile(
    r"https?://[^\s<>]+"
)


def clean_url(url):
    return url.rstrip(".,!?;:)]}")


def is_supported_video_url(url):
    url = url.lower()

    return any(
        re.search(pattern, url)
        for pattern in VIDEO_PATTERNS
    )


def download_video(url):

    print()
    print("========================================")
    print("DOWNLOAD")
    print("URL:", url)
    print("========================================")

    ydl_opts = {
        "outtmpl": str(
            DOWNLOAD_DIR / "%(title).100s.%(ext)s"
        ),
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        filename = ydl.prepare_filename(info)
        base = os.path.splitext(filename)[0]

        for ext in (
            ".mp4",
            ".mkv",
            ".webm",
            ".mov",
            ".avi",
        ):

            file_path = base + ext

            if os.path.exists(file_path):
                return file_path

        files = [
            str(path)
            for path in DOWNLOAD_DIR.iterdir()
            if path.is_file()
        ]

        if files:
            return max(
                files,
                key=os.path.getmtime
            )

        raise FileNotFoundError(
            "File video tidak ditemukan."
        )


@bot.event
async def on_ready():

    print()
    print("========================================")
    print("BOT ONLINE")
    print("========================================")
    print(f"Nama   : {bot.user}")
    print(f"ID     : {bot.user.id}")
    print(f"Server : {len(bot.guilds)}")
    print("========================================")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    await bot.process_commands(message)

    urls = URL_PATTERN.findall(
        message.content
    )

    if not urls:
        return

    url = clean_url(urls[0])

    if not is_supported_video_url(url):
        return

    # Simpan pesan tambahan sebelum pesan user dihapus
    user_message = message.content

    for detected_url in urls:
        user_message = user_message.replace(
            detected_url,
            ""
        )

    user_message = user_message.strip()

    print()
    print("VIDEO TERDETEKSI")
    print("Dari:", message.author)
    print("URL :", url)

    # Hapus pesan user agar embed hilang
    try:

        await message.delete()

        print("Pesan user dihapus.")

    except discord.Forbidden:

        print(
            "Tidak bisa menghapus pesan. "
            "Mencoba menghilangkan embed."
        )

        try:

            await message.edit(
                suppress=True
            )

            print("Embed berhasil dihilangkan.")

        except Exception as e:

            print(
                "Gagal menghilangkan embed:",
                repr(e)
            )

    except discord.NotFound:

        print("Pesan sudah tidak ditemukan.")

    except Exception as e:

        print(
            "Gagal menghapus pesan:",
            repr(e)
        )

    status_message = await message.channel.send(
        "Sedang mengambil video..."
    )

    try:

        file_path = await asyncio.to_thread(
            download_video,
            url
        )

        if not os.path.exists(file_path):

            raise FileNotFoundError(
                f"File tidak ditemukan: {file_path}"
            )

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        print(
            f"Download selesai: {file_path}"
        )

        print(
            f"Ukuran: {file_size_mb:.2f} MB"
        )

        await status_message.edit(
            content="Mengirim video ke Discord..."
        )

        # Pesan hasil dari bot
        result_message = (
            f"Video berhasil diambil dari "
            f"{message.author.mention}"
        )

        if user_message:
            result_message += (
                f"\nPesan: {user_message}"
            )

        await message.channel.send(
            content=result_message,
            file=discord.File(
                file_path,
                filename=os.path.basename(file_path)
            )
        )

        print("Upload Discord berhasil.")

        try:
            await status_message.delete()
        except Exception:
            pass

        try:

            os.remove(file_path)

            print("File sementara dihapus.")

        except Exception as e:

            print(
                "Gagal menghapus file:",
                repr(e)
            )

    except Exception as e:

        print()
        print("========================================")
        print("ERROR")
        print("========================================")

        print(
            type(e).__name__,
            repr(e)
        )

        traceback.print_exc()

        error_text = (
            f"{type(e).__name__}: "
            f"{str(e)}"
        )

        if not str(e).strip():

            error_text = (
                f"{type(e).__name__}: "
                "Lihat terminal untuk detail."
            )

        try:

            await status_message.edit(
                content=(
                    "Gagal mengambil video.\n"
                    "```text\n"
                    f"{error_text[:1500]}"
                    "\n```"
                )
            )

        except Exception:
            pass


if not TOKEN:

    raise ValueError(
        "DISCORD_TOKEN belum ditemukan di file .env"
    )


print("Menjalankan bot...")

bot.run(TOKEN)