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

# <-- [1] IZINKAN KEDUA METODE: GET DAN POST
@app.route('/send', methods=['GET', 'POST'])
def send_message():
    try:
        response = None
        url = 'https://botsailor.com/api/v1/whatsapp/send/template'

        # <-- [2] LOGIKA UNTUK METODE POST (Opsi Lengkap ✉️)
        if request.method == 'POST':
            data = request.get_json()
            api_token = data.get('api_token')
            phone_number_id = data.get('phone_number_id')
            template_id = data.get('template_id')
            phone_number = data.get('phone_number')
            quick_reply_values = data.get('template_quick_reply_button_values')

            if not all([api_token, phone_number_id, template_id, phone_number]):
                return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400
            
            payload = {
                'apiToken': api_token,
                'phone_number_id': phone_number_id,
                'template_id': template_id,
                'phone_number': phone_number
            }

            if quick_reply_values:
                payload['template_quick_reply_button_values'] = json.dumps(quick_reply_values)

            response = requests.post(url, data=payload)

        # <-- [3] LOGIKA UNTUK METODE GET (Opsi Sederhana 📮)
        elif request.method == 'GET':
            api_token = request.args.get('api_token')
            phone_number_id = request.args.get('phone_number_id')
            template_id = request.args.get('template_id')
            phone_number = request.args.get('phone_number')

            if not all([api_token, phone_number_id, template_id, phone_number]):
                return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400
            
            params = {
                'apiToken': api_token,
                'phone_number_id': phone_number_id,
                'template_id': template_id,
                'phone_number': phone_number
            }
            # Catatan: Metode GET tidak bisa mengirim 'template_quick_reply_button_values'
            response = requests.get(url, params=params)
        
        # <-- [4] PROSES RESPON YANG SAMA UNTUK KEDUA METODE
        if not response.text.strip():
            return jsonify({'success': False, 'message': '❌ API tidak merespon'}), 500
        
        try:
            result = response.json()
        except ValueError:
            return jsonify({'success': False, 'message': f'❌ Invalid JSON response: {response.text[:100]}'}), 500

        if result.get("status") == "1":
            return jsonify({'success': True, 'message': f'✅ Terkirim ke {phone_number}'})
        else:
            return jsonify({'success': False, 'message': f'❌ Gagal kirim ke {phone_number}: {result.get("message", str(result))}'})
            
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'❌ Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Server error: {str(e)}'}), 500

# Untuk Vercel
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
