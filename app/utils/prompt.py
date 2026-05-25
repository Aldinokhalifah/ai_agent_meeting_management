from datetime import datetime

def build_meeting_summary_prompt(
    title,
    scheduled_at,
    location,
    description,
    note_text,
    participant_names,
    action_item_text
):

    formatted_date = datetime.fromisoformat(
        str(scheduled_at)
    ).strftime("%A, %d %B %Y")

    return f"""
Kamu adalah asisten profesional yang efisien dalam merangkum pertemuan.
Tugasmu adalah menyusun ringkasan formal, jelas, singkat, dan langsung ke inti dalam Bahasa Indonesia.

Berikut adalah informasi meeting:
- Judul: {title}
- Tanggal: {formatted_date}
- Lokasi: {location or 'Tidak disebutkan'}
- Peserta: {participant_names}
{"- Deskripsi Konteks: " + description if description else ""}

Data Input:

1. Catatan Diskusi:
"{note_text or ''}"

2. Daftar Tugas (Action Items) Referensi:
"{action_item_text or ''}"

---
INSTRUKSI PENGOLAHAN DATA & ADAPTASI OUTPUT:

1. ADAPTASI KEPADATAN:
Jika Catatan Diskusi dan Action Items sangat minim atau kosong, buat output yang singkat dan efisien.

2. SINKRONISASI TUGAS:
Gabungkan tugas dari referensi dengan temuan baru dari catatan diskusi.

3. KOLABORASI KONTEKS:
Gunakan Judul dan Deskripsi untuk melengkapi Ringkasan Umum jika catatan minim.

4. NO HALLUCINATION:
Jangan mengarang detail yang tidak tersedia di data input.

5. GUNAKAN BAHASA EFISIEN:
Hindari pengulangan informasi dan paragraf terlalu panjang.

6. PRIORITAS FAKTA:
Prioritaskan informasi dari Catatan Diskusi dibanding deskripsi meeting.

7. FORMAT KONSISTEN:
Gunakan heading persis seperti struktur berikut.

---

### 1. Ringkasan Umum
Jelaskan tujuan dan hasil utama meeting dalam 1-3 kalimat.

### 2. Keputusan Utama
Daftarkan keputusan yang disepakati.

Jika tidak ada keputusan:
"Tidak ada keputusan spesifik yang dicatat."

### 3. Langkah Selanjutnya (Action Items)

Jika ada tugas, tampilkan dalam tabel markdown berikut:

| Tugas | PIC | Deadline |
|---|---|---|

Jika tidak ada:
"Tidak ada tindak lanjut yang dicatat."

### 4. Highlight & Catatan Penting
Tuliskan poin penting, kendala, risiko, atau insight utama secara ringkas.

---

Catatan:
Ringkasan ini dibuat secara otomatis oleh AI dan digunakan sebagai referensi awal. Mohon lakukan verifikasi ulang untuk keputusan penting.
""".strip()