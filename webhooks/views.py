from linebot.exceptions import InvalidSignatureError, LineBotApiError

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from webhooks.line_api import handler


@csrf_exempt
@require_POST
def callback(request):
    signature = request.META["HTTP_X_LINE_SIGNATURE"]
    body = request.body.decode("utf-8")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print(e.__class__, e.message)
        return HttpResponseForbidden()
    except LineBotApiError as e:
        print(e.__class__, e.message)
        return HttpResponseBadRequest()

    return HttpResponse("Ok")
