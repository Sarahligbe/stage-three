#!/bin/bash
USER="your_username"
PASSWORD="your_password"

sudo apt update

#install python dependencies
sudo apt install -y python3-pip build-essential libssl-dev libffi-dev python3-dev python3-venv

#install rabbit-mq
curl -fsSL https://packages.rabbitmq.com/gpg | sudo apt-key add -
sudo add-apt-repository 'deb https://dl.bintray.com/rabbitmq/debian focal main'
sudo apt update && sudo apt install rabbitmq-server -y

#install celery
pip3 install celery

#configure a rabbitmq user for celery
sudo rabbitmqctl add_user ${USER} ${PASSWORD}

#add virtual host
sudo rabbitmqctl add_vhost '${USER}_vhost'

#add user tag
sudo rabbitmqctl set_user_tags ${USER} '${USER}_tag'

#set permissions
sudo rabbitmqctl set_permissions -p '${USER}_vhost' ${USER} ".*" ".*" ".*"