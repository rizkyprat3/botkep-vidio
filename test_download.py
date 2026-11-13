import os
import yt_dlp


DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


url = input("Masukkan URL video: ")


ydl_opts = {
    "outtmpl": os.path.join(
        DOWNLOAD_DIR,
        "%(title).100s.%(ext)s"
    ),
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "noplaylist": True,
}


with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=True)

    filename = ydl.prepare_filename(info)

    base, _ = os.path.splitext(filename)
    mp4_filename = base + ".mp4"

    if os.path.exists(mp4_filename):
        filename = mp4_filename

    print()
    print("DOWNLOAD BERHASIL")
    print(f"File: {filename}")