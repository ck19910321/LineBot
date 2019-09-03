from abc import ABCMeta, abstractmethod
from datetime import datetime
from six import with_metaclass

from django.core.cache import cache
from linebot.models import TemplateSendMessage, TextSendMessage
from linebot.models.actions import PostbackAction, MessageAction, URIAction, DatetimePickerAction
from linebot.models.template import ButtonsTemplate, CarouselTemplate, CarouselColumn

from .tasks import send

class CacheReminder(object):
    def __init__(self, events=None, date_time=None, status=False):
        if events:
            if isinstance(list, events):
                self.events = events
            else:
                self.events = [events]
        else:
            self.events = []

        self.date_time = date_time
        self.status = status

    def get_datetime(self):
        return datetime.strptime(self.date_time, "%Y-%m-%dT%H:%M")

    def get_events(self):
        return "\n - ".join(event for event in self.events)

    def add_event(self, text):
        self.events.append(text)

    def set_datetime(self, date_time):
        self.date_time = date_time

    def set_status(self, status):
        self.status = status

    def is_set(self):
        return self.status

    @classmethod
    def new_from_dict(cls, **data):
        return cls(**data)

    def to_dict(self):
        return {
            "events": [event for event in self.events],
            "date_time": self.date_time,
            "status": self.status
        }


class BaseWoody(with_metaclass(ABCMeta, object)):

    def __init__(self, type=None):
        self.type = type
        self.actions = self.get_actions()

    def get_actions(self):
        return {func for func in dir(self) if func.startswith("can_" and callable(getattr(self, func)))}

    @classmethod
    def new_from_data(cls, **data):
        return cls(**data)


class WoodyReminder(BaseWoody):
    def __init__(self, type="reminder", key=None, *args, **kwargs):
        super().__init__(type=type)
        assert key is not None
        self.key = key
        self.cache_reminder = self._get_cache_reminder()

    def _get_cache_reminder(self):
        cache_reminder_dict = cache.get(self.key)
        if cache_reminder_dict:
            cache_reminder = CacheReminder().new_from_dict(**cache_reminder_dict)
        else:
            cache_reminder = CacheReminder()

        return cache_reminder

    def can_add_reminder(self, text):
        self.cache_reminder.add_event(text)
        cache.set(self.key, self.cache_reminder.to_dict(), 60*60*2)
        return self._build_template(text=self.cache_reminder.get_events())
        # return self._confirm(cache_reminder.get_events())

    # def can_fetch_reminder_list(self, key):
    #     cache_reminder_dict = cache.get(key)
    #     if cache_reminder_dict:
    #         cache_reminder = CacheReminder().new_from_dict(**cache_reminder_dict)
    #         return TextSendMessage(text=cache_reminder.get_events())
    #
    #     return TextSendMessage(text="不好意思，你並沒有任何提醒事項")

    def can_confirm(self, date_time):
        self.cache_reminder.set_datetime(date_time)
        self.cache_reminder.set_status(True)
        time_to_send = self.cache_reminder.get_datetime()
        # set status to true
        secs_to_expire = (time_to_send - datetime.now()).total_seconds()
        cache.set(self.key, self.cache_reminder.to_dict(), secs_to_expire)
        user_id, room_id = self.key.split("_")
        target = room_id if room_id else user_id
        send.apply_async((target, self.cache_reminder.get_events()), eta=time_to_send)
        return TextSendMessage(text="設定完畢！")

    def can_ask(self):
        cache_reminder = CacheReminder()
        cache.set(self.key, cache_reminder.to_dict(), 60*60*2)
        return TextSendMessage(text="請回覆想被提醒的事項")

    def can_cancel(self):
        cache.remove(self.key)
        return TextSendMessage(text="已移除所有提醒")

    # def can_choose_date(self, key):

    def _build_template(self, text):
        return TemplateSendMessage(
            alt_text='提醒小幫手',
            template=ButtonsTemplate(
                title='提醒事項',
                text='{text}'.format(text=text),
                actions=[
                    PostbackAction(
                        label='移除',
                        data='type=reminder&action=cancel'
                    ),
                    DatetimePickerAction(
                        label="選擇需要提醒的時間",
                        data="type=remind&action=confirm",
                        mode="datetime",
                    )
                ]
            )

        )

JOB_API = {
    "remind": WoodyReminder,
}