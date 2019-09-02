from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, LocationMessage, TextMessage, TextSendMessage

from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from webhooks.Parsers import TextParser
from webhooks.line_api import handler
from webhooks.tasks import reply, send


@csrf_exempt
@require_POST
def callback(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        return HttpResponseForbidden()
    except LineBotApiError as e:
        print (e.__class__, e.message)
        return HttpResponseBadRequest()

    return HttpResponse("Ok")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text_parser = TextParser(event.message.text)
    answer = text_parser.parse()
    reply.apply_async((event.reply_token, answer), countdown=15)
    # print("all good?")
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text=answer))
