from linebot.models import TextSendMessage

from line_bot.celery_tasks import app
from webhooks.line_api import line_bot_api


@app.task
def reply(reply_token, text):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))


@app.task
def send(token, text):
    line_bot_api.push_message(token, TextSendMessage(text=text))
