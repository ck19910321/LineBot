from urllib.parse import parse_qsl

from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from webhooks.Parsers import TextGenerator
from webhooks.line_api import handler, line_bot_api
from webhooks.jobs import JOB_API

@csrf_exempt
@require_POST
def callback(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print (e.__class__, e.message)
        return HttpResponseForbidden()
    except LineBotApiError as e:
        print (e.__class__, e.message)
        return HttpResponseBadRequest()

    return HttpResponse("Ok")


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.source.type == "user":
        text_generator = TextGenerator(event.message.text, user_id=event.source.user_id)
    else:
        text_generator = TextGenerator(event.message.text, user_id=event.source.user_id, room_id=event.source.room_id)

    message = text_generator.generate()
    line_bot_api.reply_message(
        event.reply_token,
        message
    )


@handler.add(PostbackEvent)
def handle_post_text_message(event):
    key = "{}_{}".format(event.source.user_id, getattr(event.source, "room_id", ""))
    data, param = _handle_postback_data(event.postback)
    api = JOB_API[data["type"]](key=key)
    func = "can_{}".format(data["action"])
    try:
        message = getattr(api, func)(param)

    except AttributeError:
        message = TextSendMessage(text="錯誤的訊息")

    finally:
        line_bot_api.reply_message(
            event.reply_token,
            message
        )


def _handle_postback_data(postback):
    data = {}
    for pair in parse_qsl(postback.data):
        data[pair[0]] = pair[1]

    if getattr(postback, "params"):
        required_param = postback.params["datetime"]
    else:
        required_param = data.get("tz")

    return data, required_param