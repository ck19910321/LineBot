from linebot.models import TextSendMessage

from line_bot.celery_tasks import app
from webhooks.line_api import line_bot_api


@app.task
def reply_delay(reply_token, text):
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=text)
    )