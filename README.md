# Homework bot
> This bot I've created as on of homeworks during the course to get updates about homework checking statuses to telegram using Yandex.Practicum and Telegram API.

## Local setup
First you need to define local varialbes or get it using variables manager. Required variables:
PRACTICUM_TOKEN - Yandex.Practicum API Token
TELEGRAM_TOKEN - Telegram Bot API Token
TELEGRAM_CHAT_ID - Chat ID where you'll get messages from bot

Create python virtual enviroment, then run commands in root:
```
pip install -r requirements.txt
python homework.py
```

## Deploy to Heroku
Deploying to Heroku goes automatically as soon as you pushed new updates to master. You can push updates using Heroku CLI utilite in Bash terminal:
```
heroku login
git:remote -a project_name, heroku
git push heroku master
```
Then you need to turn on app using worker on Resourses tab.

To run deployment without Heroku CLI, follow documentation, integrations with Github is possible.
You can manage workers using Procfile, follow Heroku documentation.