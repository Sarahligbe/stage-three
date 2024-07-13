from flask import Flask, request, jsonify, Response
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'amqp://your_username:your_password@localhost/your_vhost'
app.config['CELERY_RESULT_BACKEND'] = 'rpc://'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def send_email(recipient):
    msg = EmailMessage()
    msg.set_content("You have reached the endpoint successfully")
    msg['Subject'] = "Welcome!"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = recipient

    #SMTP server details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "your_email@gmail.com"
    smtp_password = "16_character_app_password"

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

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
        logging.info(f"Request logged at {current_time}")
        return jsonify({"message": f"Request logged at {current_time}"})
    else:
        return jsonify({"error": "Invalid request. Use ?sendmail=email@example.com or ?talktome parameter"}), 400

@app.route('/logs')
def view_log():
    log_path = '/var/log/messaging_system.log'
    try:
        if not os.path.exists(log_path):
            return jsonify({"error": "Log file not found"}), 404

        def generate():
            with open(log_path, 'r') as log_file:
                for line in log_file:
                    yield line

        return Response(generate(), mimetype='text/plain')
    except PermissionError:
        return jsonify({"error": "Permission denied to access log file"}), 403
    except Exception as e:
        app.logger.error(f"Error accessing log file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
