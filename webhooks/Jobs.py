from abc import ABCMeta, abstractmethod
from six import with_metaclass

from django.core.cache import cache
from linebot.models import LocationMessage, StickerMessage, TemplateSendMessage
from linebot.models.actions import PostbackAction, MessageAction, URIAction, DatetimePickerAction
from linebot.models.template import ButtonsTemplate, CarouselTemplate, CarouselColumn


class CacheTemplate(object):
    def __init__(self, data, timestamp):
        pass

class BaseWoody(with_metaclass(ABCMeta, object)):

    def __init__(self, type=None):
        self.type = type
        self.actions = self.get_actions()

    def get_actions(self):
        return {func for func in dir(self) if func.startswith("can_" and callable(getattr(self, func)))}

    def _build_template(self, *args, **kwargs):
        return TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://example.com/image.jpg',
                title='Menu',
                text='Please select',
                actions=[
                    PostbackAction(
                        label='postback',
                        # display_text='postback text',
                        data='action=buy&itemid=1'
                    ),
                ]
            )
        )

    @classmethod
    def new_from_data(cls, **data):
        return cls(**data)


class WoodyReminder(BaseWoody):
    def __init__(self, type="reminder", *args, **kwargs):
        super().__init__(type=type)

    def can_add_reminder(self, key, text):
        cache.set(key, text)
        pass

    def can_fetch_reminder_list(self, key):
        pass

    def can_confirm(self, key):
        pass

    def can_ask(self, key):
        pass

    def can_cancel(self, key):
        pass
