from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    try:
        # 1. Ambil semua data dari frontend
        data = request.get_json()

        api_token = data.get('api_token')
        phone_number_id = data.get('phone_number_id')
        template_id = data.get('template_id')
        phone_number = data.get('phone_number')
        quick_reply_values = data.get('template_quick_reply_button_values') # Ambil tombol quick reply

        if not all([api_token, phone_number_id, template_id, phone_number]):
            return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400

        url = 'https://botsailor.com/api/v1/whatsapp/send/template'

        # 2. Siapkan semua parameter untuk dikirim di URL
        params = {
            'apiToken': api_token,
            'phone_number_id': phone_number_id,
            'template_id': template_id,
            'phone_number': phone_number
        }

        # Jika ada data quick reply, tambahkan ke parameter
        if quick_reply_values:
            params['template_quick_reply_button_values'] = json.dumps(quick_reply_values)

        # 3. Gunakan metode GET dengan 'params' yang sudah terbukti berhasil
        response = requests.get(url, params=params)

        # Bagian ini tetap sama untuk memproses jawaban dari BotSailor
        if not response.text.strip():
            return jsonify({'success': False, 'message': '❌ API tidak merespon'}), 500

        try:
            result = response.json()
        except ValueError:
            # Jika respons bukan JSON, tampilkan sebagai teks biasa (karena bisa jadi error HTML)
            return jsonify({'success': False, 'message': f'❌ Respons tidak valid: {response.text[:200]}'}), 500

        if result.get("status") == "1":
            return jsonify({'success': True, 'message': f'✅ Terkirim ke {phone_number}'})
        else:
            return jsonify({'success': False, 'message': f'❌ Gagal kirim ke {phone_number}: {result.get("message", str(result))}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Server error: {str(e)}'}), 500

# Untuk Vercel
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
