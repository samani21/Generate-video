import os
import random
import subprocess
import whisper

# ======================
# CONFIG
# ======================
FOLDER_ATAS = "folder-video-atas"
FOLDER_BAWAH = "folder-video-bawah"
FOLDER_OUTPUT = "folder-output"

HOOK_TEXT = "INI YANG TERJADI..."

FAKE_SUBS = [
    "ini yang terjadi",
    "lihat sampai habis",
    "ga nyangka banget",
    "endingnya bikin shock",
    "awas jangan skip",
    "detik detik menegangkan"
]

# ======================
# HELPER
# ======================
def random_filename():
    return ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8)) + ".mp4"

def get_paired_files():
    atas_files = sorted([f for f in os.listdir(FOLDER_ATAS) if f.endswith(".mp4")])
    bawah_files = sorted([f for f in os.listdir(FOLDER_BAWAH) if f.endswith(".mp4")])

    if not atas_files:
        raise Exception("Folder atas kosong!")
    if not bawah_files:
        raise Exception("Folder bawah kosong!")

    min_len = min(len(atas_files), len(bawah_files))

    return [
        (os.path.join(FOLDER_ATAS, atas_files[i]),
         os.path.join(FOLDER_BAWAH, bawah_files[i]))
        for i in range(min_len)
    ]

def clean_text(text):
    text = text.replace("'", "")
    text = text.replace(":", "")
    text = text.replace(",", "")
    text = text.replace('"', '')
    text = text.strip()
    text = text.replace(" ", "\\ ")
    return text

# 🔥 SPLIT JADI 2 BARIS (TANPA \n)
def split_text(text, max_chars=40):
    words = text.strip().split()

    lines = []
    current = ""

    for w in words:
        if len(current + " " + w) <= max_chars:
            current = (current + " " + w).strip()
        else:
            lines.append(current)
            current = w

    if current:
        lines.append(current)

    return lines[:2]  # maksimal 2 baris

# ======================
# AUDIO EXTRACTION
# ======================
def extract_audio(video_path):
    audio_path = "temp_audio.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    subprocess.run(cmd, capture_output=True)
    return audio_path

# ======================
# SUBTITLE (WHISPER)
# ======================
def generate_subtitle(video_path):
    print("🧠 Generate subtitle dari:", video_path)

    audio_path = extract_audio(video_path)

    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    subtitles = []
    for seg in result["segments"]:
        raw_lines = split_text(seg["text"])
        clean_lines = [clean_text(line) for line in raw_lines]

        start = round(seg["start"], 2)
        end = round(seg["end"], 2)

        if clean_lines:
            subtitles.append({
                "lines": clean_lines,
                "start": start,
                "end": end
            })

    print("Total subtitle:", len(subtitles))
    return subtitles

# ======================
# BUILD FILTER (FIX UTAMA)
# ======================
def build_subtitle_filter(subs):
    filters = []

    for s in subs:
        for i, line in enumerate(s["lines"]):
            # 🔥 posisi tengah (2 baris seimbang)
            if len(s["lines"]) == 1:
                y_pos = "(h-text_h)/2"
            else:
                y_pos = "(h/2-50)" if i == 0 else "(h/2+20)"

            filters.append(
                f"drawtext=text='{line}':"
                f"fontcolor=white:"
                f"fontsize=42:"
                f"borderw=3:bordercolor=black:"
                f"shadowcolor=black:shadowx=2:shadowy=2:"
                f"box=1:boxcolor=black@0.4:"
                f"x=(w-text_w)/2:"
                f"y={y_pos}:"
                f"enable=between(t\\,{s['start']}\\,{s['end']})"
            )

    return ",".join(filters)

# ======================
# MAIN
# ======================
def main():
    os.makedirs(FOLDER_OUTPUT, exist_ok=True)

    pairs = get_paired_files()
    print(f"\nTotal pasangan diproses: {len(pairs)}\n")

    for idx, (video_atas, video_bawah) in enumerate(pairs, start=1):

        output_file = os.path.abspath(os.path.join(FOLDER_OUTPUT, random_filename()))

        print(f"\n=== PROCESS {idx} ===")
        print("Atas :", video_atas)
        print("Bawah:", video_bawah)

        subs = generate_subtitle(video_bawah)

        if not subs:
            print("⚠ Subtitle kosong → pakai FAKE")
            subs = [{
                "lines": [clean_text(random.choice(FAKE_SUBS))],
                "start": 1,
                "end": 5
            }]

        subtitle_filter = build_subtitle_filter(subs)

        filter_complex = (
            "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bottom];"
            "[top][bottom]vstack=inputs=2[stacked];"
            "[stacked]drawtext=text=INI\\ YANG\\ TERJADI...:"
            "fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:"
            "x=(w-text_w)/2:y=50:enable=between(t\\,0\\,3),"
            + subtitle_filter +
            "[v]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_atas,
            "-i", video_bawah,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "1:a?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-shortest",
            output_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_file):
            print("✅ DONE")
        else:
            print("❌ ERROR")
            print(result.stderr)

    print("\n🎉 SELESAI SEMUA!")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    main()