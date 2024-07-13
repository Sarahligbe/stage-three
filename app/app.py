from flask import Flask, request, jsonify, Response
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# Celery configuration
app.config['CELERY_BROKER_URL'] = f"amqp://{os.getenv('CELERY_USERNAME')}:{os.getenv('CELERY_PASSWORD')}@localhost/{os.getenv('CELERY_VHOST')}"
app.config['CELERY_RESULT_BACKEND'] = 'rpc://'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def send_email(recipient):
    msg = EmailMessage()
    msg.set_content("You have reached the endpoint successfully")
    msg['Subject'] = "Welcome!"
    msg['From'] = os.getenv('SMTP_USERNAME')
    msg['To'] = recipient

    #SMTP server details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

# Define the log file path
log_file_path = '/var/log/messaging_system.log'

# Ensure the directory exists
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

try:
    # Try to create or open the file
    with open(log_file_path, 'a') as f:
        pass  # Just open and close the file to create it if it doesn't exist
    # Configure logging
    logging.basicConfig(filename=log_file_path, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    print(f"Log file created successfully at {log_file_path}")
    logging.info("Logging system initialized")

except PermissionError:
    print(f"Permission denied: Unable to create or write to {log_file_path}")
    print("You may need to run the script with sudo or adjust file permissions")
except Exception as e:
    print(f"An error occurred: {str(e)}")

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
