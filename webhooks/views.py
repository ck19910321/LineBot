from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from webhooks.Parsers import TextParser
line_bot_api = LineBotApi('3fJbjOb+F4yeTpU1Kut6D7DfgZdjEwRabGqBkrTwT+5MFYBrFPWr7Tgs+jWcC9CdpgZmuYNmaUi/ML1X4ncwLq5pV1zD1UxAzkfhX1xdCt2rSpQYE+xR+aQyqWFIObFRR+/E8Yab/2b9IdN9GcNlogdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('d6dd24a1b7cc59462411284e955acd77')


@csrf_exempt
@require_POST
def callback(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print (e.message)
        return HttpResponseForbidden()
    except LineBotApiError as e:
        print (e.message)
        return HttpResponseBadRequest()

    return HttpResponse("Ok")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text_parser = TextParser(event.message.text)
    answer = text_parser.parse()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=answer))
