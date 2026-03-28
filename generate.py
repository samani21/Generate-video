import os
import random
import subprocess
import whisper
import numpy as np
import wave

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

    return lines[:2]

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
# 🔥 DETEKSI SUARA
# ======================
def is_speech(audio_path, start, end, threshold=500):
    with wave.open(audio_path, 'rb') as wf:
        framerate = wf.getframerate()
        start_frame = int(start * framerate)
        end_frame = int(end * framerate)

        wf.setpos(start_frame)
        frames = wf.readframes(end_frame - start_frame)

        audio = np.frombuffer(frames, dtype=np.int16)

        if len(audio) == 0:
            return False

        volume = np.abs(audio).mean()
        return volume > threshold

# ======================
# 🔥 CARI AWAL SUARA MANUSIA
# ======================
def get_first_speech_time(audio_path, step=0.2, threshold=700, min_hits=3):
    import wave
    import numpy as np

    with wave.open(audio_path, 'rb') as wf:
        framerate = wf.getframerate()
        total_frames = wf.getnframes()

        chunk_size = int(step * framerate)

        hit_count = 0

        for i in range(0, total_frames, chunk_size):
            wf.setpos(i)
            frames = wf.readframes(chunk_size)

            audio = np.frombuffer(frames, dtype=np.int16)

            if len(audio) == 0:
                continue

            volume = np.abs(audio).mean()

            if volume > threshold:
                hit_count += 1

                # 🔥 harus kena beberapa kali (bukan noise sekali)
                if hit_count >= min_hits:
                    return round(i / framerate, 2)
            else:
                hit_count = 0

    return 0

# ======================
# SUBTITLE (WHISPER)
# ======================
def generate_subtitle(video_path):
    print("🧠 Generate subtitle dari:", video_path)

    audio_path = extract_audio(video_path)

    # 🔥 DETEKSI AWAL SUARA
    first_speech = get_first_speech_time(audio_path)
    print("🎤 First speech at:", first_speech)

    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    subtitles = []

    for seg in result["segments"]:
        start = round(seg["start"], 2)
        end = round(seg["end"], 2)

        # 🔥 FIX UTAMA: paksa subtitle pertama tidak sebelum suara
        if start < first_speech:
            start = first_speech

        # 🔥 skip kalau setelah dipaksa jadi aneh
        if end <= start:
            continue

        # 🔥 FILTER noise
        if not is_speech(audio_path, start, end):
            continue

        # 🔥 OPTIONAL DELAY (biar natural)
        start = round(start + 0.2, 2)
        end = round(end + 0.2, 2)

        raw_lines = split_text(seg["text"])
        clean_lines = [clean_text(line) for line in raw_lines]

        if clean_lines:
            subtitles.append({
                "lines": clean_lines,
                "start": start,
                "end": end
            })

    print("Total subtitle:", len(subtitles))
    return subtitles

# ======================
# BUILD FILTER
# ======================
def build_subtitle_filter(subs):
    filters = []

    for s in subs:
        for i, line in enumerate(s["lines"]):
            if len(s["lines"]) == 1:
                y_pos = "(h-text_h)/2"
            else:
                y_pos = "(h/2-50)" if i == 0 else "(h/2+20)"

            filters.append(
                f"drawtext=text='{line}':"
                f"fontcolor=white:"
                f"fontsize=48:"
                f"fontfile=/Windows/Fonts/arialbd.ttf:"
                f"borderw=4:bordercolor=black:"
                f"shadowcolor=black:shadowx=3:shadowy=3:"
                f"box=1:boxcolor=black@0.5:boxborderw=10:"
                f"x=(w-text_w)/2:"
                f"y={y_pos}:"
                f"alpha='if(lt(t,{s['start']}),0, if(lt(t,{s['start']}+0.2),(t-{s['start']})/0.2,1))':"
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