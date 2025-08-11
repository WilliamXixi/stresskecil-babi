from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()

        api_token = data.get('api_token')
        phone_number_id = data.get('phone_number_id')
        template_id = data.get('template_id')
        phone_number = data.get('phone_number')
        quick_reply_values = data.get('template_quick_reply_button_values')

        if not all([api_token, phone_number_id, template_id, phone_number]):
            return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400

        # Encode quick reply kalau ada
        quick_reply_str = ""
        if quick_reply_values:
            if isinstance(quick_reply_values, str):
                quick_reply_values = [quick_reply_values]
            quick_reply_str = "&template_quick_reply_button_values=" + urllib.parse.quote(json.dumps(quick_reply_values))

        # Buat full URL persis format contoh
        full_url = (
            f"https://botsailor.com/api/v1/whatsapp/send/template?"
            f"apiToken={urllib.parse.quote(api_token)}"
            f"&phone_number_id={urllib.parse.quote(str(phone_number_id))}"
            f"&template_id={urllib.parse.quote(str(template_id))}"
            f"{quick_reply_str}"
            f"&phone_number={urllib.parse.quote(str(phone_number))}"
        )

        # Kirim GET request langsung ke URL
        response = requests.get(full_url)

        if not response.text.strip():
            return jsonify({'success': False, 'message': '❌ API tidak merespon'}), 500

        try:
            result = response.json()
        except ValueError:
            return jsonify({'success': False, 'message': f'❌ Respons tidak valid: {response.text[:200]}'}), 500

        if result.get("status") == "1":
            return jsonify({'success': True, 'message': f'✅ Terkirim ke {phone_number}'})
        else:
            return jsonify({'success': False, 'message': f'❌ Gagal kirim ke {phone_number}: {result.get("message", str(result))}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
