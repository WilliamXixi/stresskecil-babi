from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json
import urllib.parse
import re
import time

app = Flask(__name__)
CORS(app)

# Helper: parse "Menunggu 8.89 detik" atau "waiting 8.89 seconds"
def parse_wait_seconds(text):
    if not text:
        return None
    # cari format indonesia "detik"
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*detik', text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # cari english "second(s)"
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*second', text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()

        # Ambil input (tambahkan user_id opsional untuk log)
        user_id = data.get('user_id', 1)
        api_token = data.get('api_token')
        phone_number_id = data.get('phone_number_id')
        template_id = data.get('template_id')
        phone_number = data.get('phone_number')
        quick_reply_values = data.get('template_quick_reply_button_values')

        if not all([api_token, phone_number_id, template_id, phone_number]):
            return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400

        # konfigurasi retry
        max_retries = int(data.get('max_retries', 2))         # default 2 percobaan
        max_wait_seconds = float(data.get('max_wait_seconds', 30.0))  # batas sleep agar gak lama banget

        # encode quick reply kalau ada
        quick_reply_str = ""
        if quick_reply_values:
            if isinstance(quick_reply_values, str):
                quick_reply_values = [quick_reply_values]
            quick_reply_str = "&template_quick_reply_button_values=" + urllib.parse.quote(json.dumps(quick_reply_values))

        # buat full URL persis format contoh
        full_url = (
            f"https://botsailor.com/api/v1/whatsapp/send/template?"
            f"apiToken={urllib.parse.quote(api_token)}"
            f"&phone_number_id={urllib.parse.quote(str(phone_number_id))}"
            f"&template_id={urllib.parse.quote(str(template_id))}"
            f"{quick_reply_str}"
            f"&phone_number={urllib.parse.quote(str(phone_number))}"
        )

        # Siapkan logs
        logs = []
        logs.append("📋 Log Pengiriman:")
        logs.append(f"🔢 User ID: {user_id} | Nomor: {phone_number} | Template: {template_id} ➡️ Mengirim...")

        # Loop retry: jika respons teks dan berisi instruksi tunggu -> sleep lalu retry
        attempt = 0
        last_text_response = None
        json_result = None
        is_json = False

        while attempt < max_retries:
            attempt += 1
            try:
                response = requests.get(full_url, timeout=30)
            except Exception as e:
                logs.append(f"❌ User ID: {user_id} | {phone_number} - ❌ Error koneksi: {str(e)}")
                break

            text = response.text.strip() if response.text is not None else ""
            # coba parse json
            try:
                json_result = response.json()
                is_json = True
                break
            except ValueError:
                # bukan json
                last_text_response = text
                # catat pesan tekstual dari API
                # contoh: "⏳ Menunggu 8.89 detik sebelum pesan berikutnya..."
                logs.append(f"❌ User ID: {user_id} | {phone_number} - ❌ Respons tidak valid: {text}")

                # cek apakah ada instruksi menunggu
                wait_seconds = parse_wait_seconds(text)
                if wait_seconds is not None and attempt < max_retries:
                    # batasi sleep agar tidak berlama-lama
                    wait_to_sleep = min(wait_seconds, max_wait_seconds)
                    logs.append(f"🔁 Ditemukan instruksi tunggu: menunggu {wait_seconds} detik. Sleep {wait_to_sleep} detik lalu coba ulang ({attempt}/{max_retries})...")
                    time.sleep(wait_to_sleep)
                    continue
                else:
                    # tidak ada instruksi tunggu atau sudah attempt terakhir -> stop retry
                    break

        # Setelah loop: cek hasil
        if is_json and isinstance(json_result, dict):
            # proses hasil JSON
            status = str(json_result.get("status", "")).strip()
            if status == "1" or status == "success" or json_result.get("success") is True:
                logs.append(f"✅ User ID: {user_id} | {phone_number} - ✅ Terkirim.")
                return jsonify({'success': True, 'message': f'✅ Terkirim ke {phone_number}', 'logs': logs, 'result': json_result})
            else:
                # JSON tapi gagal (tampilkan message dari API bila ada)
                api_msg = json_result.get('message', str(json_result))
                logs.append(f"❌ User ID: {user_id} | {phone_number} - ❌ Gagal kirim: {api_msg}")
                return jsonify({'success': False, 'message': f'❌ Gagal kirim ke {phone_number}: {api_msg}', 'logs': logs, 'result': json_result})
        else:
            # Tidak dapat JSON — kembalikan teks terakhir sebagai log/penjelasan
            if last_text_response:
                logs.append("🛑 Pengiriman dihentikan.")
                return jsonify({'success': False, 'message': f'❌ Respons tidak valid: {last_text_response}', 'logs': logs})
            else:
                logs.append("🛑 Pengiriman dihentikan: tidak ada respons dari server.")
                return jsonify({'success': False, 'message': '❌ API tidak merespon', 'logs': logs}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
