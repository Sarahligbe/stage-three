# stage-three

Deploy a Python application behind Nginx that interacts with RabbitMQ/Celery for email sending and logging functionality.  

## Pre-requisites
1. Python3 installed
2. An Ubuntu 22.04 server
3. Ngrok account with a static domain set up

## Steps
1. Create the log file and set user permissions
```bash
  sudo touch /var/log/messaging_system.log && sudo chmod 666 /var/log/messaging_system.log
```
2. Edit the .env file with your SMTP username and password, and the username, password, and vhost name you would use to set up rabbitmq
3.  Install python dependencies
```bash
   sudo apt update
   sudo apt install -y python3-pip build-essential libssl-dev libffi-dev python3-dev python3-venv python3-flask python3-dotenv
```
4. Install rabbitmq and set up a user with permissions
```bash
  sudo rabbitmqctl add_user ${USER} ${PASSWORD}

  #add virtual host
  sudo rabbitmqctl add_vhost '${USER}_vhost'
  
  #add user tag
  sudo rabbitmqctl set_user_tags ${USER} '${USER}_tag'
  
  #set permissions
  sudo rabbitmqctl set_permissions -p '${USER}_vhost' ${USER} ".*" ".*" ".*"
```
5. Install celery
```bash
   sudo apt update
   sudo apt install celery
```
6. Set up celery systemd service
- Create a celery config file `/etc/default/celeryd`
```bash
  # Name of nodes to start
# here we have a single node
CELERYD_NODES="w1"
# or we could have three nodes:
#CELERYD_NODES="w1 w2 w3"

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/home/ubuntu/stage-three/app/celeryenv/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="app.celery"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Celery working directory
CELERYD_WORKDIR="/home/ubuntu/stage-three/app"

# celery worker user
CELERYD_USER=“ubuntu”
CELERYD_GROUP=“ubuntu”

# How to call manage.py
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYD_STATE_DIR=“/var/run/celery”
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_LOG_LEVEL="INFO"

# you may wish to add these options for Celery Beat
CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"
```
- Create the PID and log files and ensure your user owns the files or has appropriate permissions
```bash
  sudo mkdir -p /var/run/celery && sudo chown ubuntu:ubuntu /var/run/celery

  sudo mkdir /var/log/celery && sudo chown ubuntu:ubuntu /var/log/celery
```
- Set up the celery service file in `/etc/systemd/system/celery.service`
```bash
  [Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
EnvironmentFile=/etc/default/celeryd
WorkingDirectory=/home/ubuntu/stage-three/app
ExecStartPre=+/bin/bash -c 'mkdir -p /var/run/celery'
ExecStartPre=+/bin/bash -c 'chown ubuntu:ubuntu /var/run/celery'
ExecStart=/bin/bash -c '${CELERY_BIN} -A $CELERY_APP multi start $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
ExecStop=/bin/bash -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}"'
ExecReload=/bin/bash -c '${CELERY_BIN} -A $CELERY_APP multi restart $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
Restart=always

[Install]
WantedBy=multi-user.target
```
- Run the systemctl commands to start the service
```bash
  #reload the daemon and start and enable the service
  sudo systemctl daemon-reload
  sudo systemctl start celery
  sudo systemctl enable celery
```
7. Set up gunicorn as a systemd service in `/etc/systemd/system/gunicorn.service`
```bash
  [Unit]
  Description=Gunicorn instance to serve the stagethree app
  After=network.target
  
  [Service]
  User=ubuntu
  Group=www-data
  WorkingDirectory=/home/ubuntu/stage-three/app
  Environment="PATH=/home/ubuntu/stage-three/app/celeryenv/bin"
  ExecStart=/home/ubuntu/stage-three/app/celeryenv/bin/gunicorn --workers 3 --bind unix:stagethree.sock app:app
  
  [Install]
  WantedBy=multi-user.target
```
- Run the systemctl commands to start the service
```bash
  #reload the daemon and start and enable the service
  sudo systemctl daemon-reload
  sudo systemctl start gunicorn
  sudo systemctl enable gunicorn
```
8. Install nginx
```bash
   sudo apt update
   sudo apt install nginx
```
- Change the owner of the nginx config file to your user and edit the file to include your user instead of `www-data`
```bash
   sudo chown ubuntu:ubuntu /etc/nginx/nginx.conf
   sudo nano /etc/nginx/nginx.conf
```
- Create the nginx config file in `/etc/nginx/sites-available/stagethree`
```bash
  server {
  listen 80;
  server_name localhost;
  
  location / {
  include proxy_params;
  proxy_pass http://unix:/home/ubuntu/stage-three/app/stagethree.sock;
  }
  }
```
- Create a symlink to sites-enabled, delete default config files, and reload nginx
```bash
  sudo ln -s /etc/nginx/sites-available/stagethree /etc/nginx/sites-enabled
  sudo rm /etc/nginx/sites-available/default && sudo rm /etc/nginx/sites-enabled/default
  sudo systemctl reload nginx
```
9. Install ngrok
- Create the ngrok config file if it does not exists in `/home/ubuntu/.config/ngrok/ngrok.yml`
```bash
  version: "2"
  authtoken: <your-token>
  tunnels:
    stagethree: 
      proto: http
      addr: 80
      domain: <your-domain>
```
- Create the ngrok systemd service file in `/etc/systemd/system/ngrok.service`
  ```bash
    [Unit]
    Description=Start ngrok tunnel on startup
    After=network-online.target
    Wants=network-online.target systemd-networkd-wait-online.service
    
    [Service]
    ExecStart=/usr/local/bin/ngrok start --all --config /home/ubuntu/.config/ngrok/ngrok.yml
    ExecReload=/bin/kill -HUP $MAINPID
    KillMode=process
    IgnoreSIGPIPE=true
    Restart=always
    RestartSec=3
    Type=simple
    
    [Install]
    WantedBy=multi-user.target
  ```
- Run the systemctl commands to start the service
```bash
  #reload the daemon and start and enable the service
  sudo systemctl daemon-reload
  sudo systemctl start ngrok
  sudo systemctl enable ngrok
```
