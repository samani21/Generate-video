# 🎬 Auto Video Generator (Whisper Subtitle)

Script Python untuk:

* 🎥 Menggabungkan 2 video (atas & bawah)
* 🧠 Generate subtitle otomatis pakai Whisper
* ✨ Subtitle style TikTok (word-by-word / karaoke)
* 🔊 Menggunakan audio dari video bawah

---

## 🚀 Installation

Ikuti langkah berikut:

```bash
# 1. Buat virtual environment
python -m venv venv

# 2. Aktifkan venv
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install dependencies
pip install torch
pip install openai-whisper
```

---

## 📂 Struktur Folder

```
project/
│
├── folder-video-atas/
│   ├── atas_1.mp4
│   ├── atas_2.mp4
│
├── folder-video-bawah/
│   ├── bawah_1.mp4
│   ├── bawah_2.mp4
│
├── folder-output/
│
├── generate.py
└── README.md
```

---

## ▶️ Cara Menjalankan

```bash
python generate.py
```

---

## ⚙️ Fitur

* 🎬 Stack video atas & bawah (format konten viral)
* 🧠 Auto subtitle dari audio (Whisper AI)
* 📝 Subtitle per kata (karaoke style)
* 🎯 Posisi subtitle di tengah layar
* 🔊 Audio otomatis dari video bawah
* ⚡ Proses cepat dengan FFmpeg

---

## ⚠️ Requirements

Pastikan sudah install:

* Python 3.9+
* FFmpeg (harus ada di PATH)

Cek FFmpeg:

```bash
ffmpeg -version
```

---

## 💡 Tips

* Gunakan video resolusi tinggi biar hasil maksimal
* Audio harus jelas agar subtitle akurat
* Bisa ubah style subtitle langsung di `generate.py`

---


## 🧑‍💻 Author

Project ini dibuat untuk automasi konten video viral 🎯
