from urllib.parse import parse_qs

from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, LocationMessage, TextMessage, TextSendMessage

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
    # print(vars(request))
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print (e.__class__, e.message)
        return HttpResponseForbidden()
    except LineBotApiError as e:
        print (e.__class__, e.message)
        return HttpResponseBadRequest()

    return HttpResponse("Ok")


# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     print(vars(event))
#     text_parser = TextParser(event.message.text)
#     answer = text_parser.parse()
#     reply.apply_async((event.reply_token, answer), countdown=15)

@handler.add(PostbackEvent)
def handle_post_text_message(event):
    # {'type': 'postback', 'timestamp': 1567472954376,
    # 'source': {"type": "user", "userId": "Ua6a3fc44878a49a3a9c4fbfc699ec9e0"},
    # 'reply_token': 'bc98bf22fa2f4ad7afdf5cdf98ae3f74',
    # 'postback': {"data": "action=buy&itemid=1"}}
    data = event.postback.data
    print(parse_qs(data))



# {'type': 'message', 'timestamp': 1567463126728, 'source': {"roomId": "Rcc819f2974fa9773ecfdfd08e97f03e5", "type": "room", "userId": "Ua6a3fc44878a49a3a9c4fbfc699ec9e0"}, 'reply_token': '4f30b88717224439982575ba48b96a50', 'message': {"id": "10502121096301", "text": "Hi", "type": "text"}}

# {'type': 'message', 'timestamp': 1567463229032, 'source': {"roomId": "Rcc819f2974fa9773ecfdfd08e97f03e5", "type": "room", "userId": "U3f761aaa0c7a2f60a1e9aa9260966c23"}, 'reply_token': '36d0b8520da04ac29a247cfb5a53552e', 'message': {"id": "10502126225980", "text": "\u8001\u516c\u5f88\u7b28", "type": "text"}}

# {'type': 'message', 'timestamp': 1567463392890, 'source': {"type": "user", "userId": "Ua6a3fc44878a49a3a9c4fbfc699ec9e0"}, 'reply_token': '04fea381efa849f385c169efe0ea6bef', 'message': {"id": "10502134513753", "text": "\uff1f\u7528", "type": "text"}}