from linebot import LineBotApi, WebhookHandler
from django.conf import settings

line_bot_api = LineBotApi(settings.LINE_BOT_API)
handler = WebhookHandler(settings.LINE_BOT_HANDLER)
