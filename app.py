from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

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

        if not all([api_token, phone_number_id, template_id, phone_number]):
            return jsonify({'success': False, 'message': '❌ Semua field wajib diisi!'}), 400

        url = 'https://botsailor.com/api/v1/whatsapp/send/template'
        params = {
            'apiToken': api_token,
            'phone_number_id': phone_number_id,
            'template_id': template_id,
            'phone_number': phone_number
        }

        response = requests.get(url, params=params)
        
        # Cek jika response kosong
        if not response.text.strip():
            return jsonify({'success': False, 'message': '❌ API tidak merespon'}), 500
        
        # Coba parse JSON
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
