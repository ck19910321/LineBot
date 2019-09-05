from urllib.parse import parse_qsl
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage

from django.conf import settings

from webhooks.Parsers import TextGenerator
from webhooks.jobs import JOB_API


line_bot_api = LineBotApi(settings.LINE_BOT_API)
handler = WebhookHandler(settings.LINE_BOT_HANDLER)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.source.type == "user":
        text_generator = TextGenerator(event.message.text, user_id=event.source.user_id)
    else:
        text_generator = TextGenerator(
            event.message.text,
            user_id=event.source.user_id,
            room_id=event.source.room_id,
        )

    message = text_generator.generate()
    line_bot_api.reply_message(event.reply_token, message)


@handler.add(PostbackEvent)
def handle_post_text_message(event):
    key = "{}_{}".format(event.source.user_id, getattr(event.source, "room_id", ""))
    data, func_name, woody_type = _handle_postback_data(event.postback)
    api = JOB_API[woody_type](data=data, key=key)
    func = "can_{}".format(func_name)
    try:
        message = getattr(api, func)()

    except AttributeError:
        message = TextSendMessage(text="錯誤的訊息")

    finally:
        line_bot_api.reply_message(event.reply_token, message)


def _handle_postback_data(postback):
    data = {}
    for pair in parse_qsl(postback.data):
        data[pair[0]] = pair[1]

    if getattr(postback, "params"):
        data["target_datetime"] = postback.params["datetime"]
    return data, data.pop("action"), data.pop("type")
