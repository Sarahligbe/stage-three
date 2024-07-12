from flask import Flask, request, jsonify, Response
from celery_tasks import send_email
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def handle_request():
    if 'sendmail' in request.args:
        recipient = request.args.get('sendmail')
        send_email.delay(recipient)
        return jsonify({"message": f"Email queued for sending to {recipient}"})
    elif 'talktome' in request.args:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Request logged at {current_time}")
        return jsonify({"message": f"Request logged at {current_time}"})
    else:
        return jsonify({"error": "Invalid request. Use ?sendmail=email@example.com or ?talktome parameter"}), 400

@app.route('/log')
def view_log():
    try:
        with open('/var/log/messaging_system.log', 'r') as log_file:
            return Response(log_file.read(), mimetype='text/plain')
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)