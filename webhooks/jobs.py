from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from six import with_metaclass
import json

from django.core.cache import cache
from linebot.models import TemplateSendMessage, TextSendMessage
from linebot.models.actions import PostbackAction, MessageAction, URIAction, DatetimePickerAction
from linebot.models.template import ButtonsTemplate, CarouselTemplate, CarouselColumn

from .tasks import send

class CacheReminder(object):
    def __init__(self, events=None, date_time=None, status=False, shift_hours=0):
        if events:
            if isinstance(events, list):
                self.events = events
            else:
                self.events = [events]
        else:
            self.events = []

        self.date_time = date_time
        self.status = status
        self.shift_hours = shift_hours

    def get_datetime_by_timezone(self):
        return datetime.strptime(self.date_time, "%Y-%m-%dT%H:%M") + timedelta(hours=self.shift_hours)

    def get_datetime_wo_tiemzone_aware(self):
        return datetime.strptime(self.date_time, "%Y-%m-%dT%H:%M")

    def set_timezone(self, hours):
        self.shift_hours = hours

    def get_events(self):
        reminder_template = "來自專屬小幫手的貼心小叮嚀:\n"
        event_str = "\n".join(event for event in self.events)
        return "{}{}".format(reminder_template, event_str)

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
            "status": self.status,
            "shift_hours": self.shift_hours
        }


class BaseWoody(with_metaclass(ABCMeta, object)):

    def __init__(self, type=None):
        self.type = type
        self.actions = self.get_actions()

    def get_actions(self):
        return set([func for func in dir(self) if func.startswith("can_") and callable(getattr(self, func))])

    @classmethod
    def new_from_data(cls, **data):
        return cls(**data)

    def _get_cache(self):
        pass


class WoodyTimeConverter(BaseWoody):
    def __init__(self, type="date_convert", key=None, *args, **kwargs):
        super().__init__(type=type)
        print(key)
        assert key is not None
        self.key = key

    def _get_cache(self):
        cache_value = cache.get(self.key, '{"from_hours": 0, "to_hours": 0, "from_country": "", "to_country": ""}')
        return json.loads(cache_value)

    def set_cache(self, shift_hours):
        cache.set(self.key, shift_hours, 5 * 60)
        print("key set", self.key)
        print(cache.get(self.key))

    def can_choose(self, date_time):
        value = self._get_cache()
        utc_date = datetime.strptime(date_time, "%Y-%m-%dT%H:%M") + timedelta(hours=value.get("from_hours", 0))
        return_date = utc_date + timedelta(hours=value.get("to_hours", 0))
        return TextSendMessage(text="{}時間為: {}".format(value.get("country"), return_date.strftime("%Y-%m-%d %I:%M %p")))


class WoodyReminder(BaseWoody):
    def __init__(self, type="reminder", key=None, *args, **kwargs):
        super().__init__(type=type)
        assert key is not None
        self.key = key
        self.cache_reminder = self._get_cache()

    def _get_cache(self):
        cache_reminder_dict = cache.get(self.key)
        if cache_reminder_dict:
            cache_reminder = CacheReminder().new_from_dict(**cache_reminder_dict)
        else:
            cache_reminder = CacheReminder()

        return cache_reminder

    def can_add_reminder(self, text):
        self.cache_reminder.add_event(text)
        cache.set(self.key, self.cache_reminder.to_dict(), 60*60*2)

        return TemplateSendMessage(
            alt_text='提醒小幫手',
            template=ButtonsTemplate(
                title='提醒事項',
                text=self.cache_reminder.get_events(),
                actions=[
                    PostbackAction(
                        label='台灣時區',
                        data='type=remind&action=adjust_timezone&tz=taiwan'
                    ),
                    PostbackAction(
                        label='美國時區',
                        data='type=remind&action=adjust_timezone&tz=us'
                    ),
                    PostbackAction(
                        label='日本時區',
                        data='type=remind&action=adjust_timezone&tz=japan'
                    ),
                ]
            )

        )

    def can_adjust_timezone(self, timezone):
        time_zone_dict = {
            "taiwan": -8,
            "us": 7,
            "japan": -9,
        }
        self.cache_reminder.set_timezone(time_zone_dict[timezone])
        cache.set(self.key, self.cache_reminder.to_dict(), 60 * 60 * 2)
        return TemplateSendMessage(
            alt_text='提醒小幫手',
            template=ButtonsTemplate(
                title='提醒事項',
                text=self.cache_reminder.get_events(),
                actions=[
                    PostbackAction(
                        label='移除',
                        data='type=remind&action=cancel'
                    ),
                    DatetimePickerAction(
                        label="選擇需要提醒的時間",
                        data="type=remind&action=confirm",
                        mode="datetime",
                    )
                ]
            )

        )


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
        time_to_send = self.cache_reminder.get_datetime_by_timezone()
        # set status to true
        secs_to_expire = (time_to_send - datetime.utcnow()).total_seconds()
        if secs_to_expire > 0:
            cache.set(self.key, self.cache_reminder.to_dict(), secs_to_expire)
        else:
            cache.delete(self.key)

        user_id, room_id = self.key.split("_")
        target = room_id if room_id else user_id
        send.apply_async((target, self.cache_reminder.get_events()), eta=time_to_send)
        return TextSendMessage(text="設定完畢！將於 {} 提醒您。".format(self.cache_reminder.get_datetime_wo_tiemzone_aware().strftime("%Y-%m-%d %I:%M %p")))

    def can_ask(self, value=None):
        cache_reminder = CacheReminder()
        cache.set(self.key, cache_reminder.to_dict(), 60*60*2)
        return TextSendMessage(text="請回覆想被提醒的事項")

    def can_cancel(self, value=None):
        cache.delete(self.key)
        return TextSendMessage(text="已移除所有提醒")


JOB_API = {
    "remind": WoodyReminder,
    "date_convert": WoodyTimeConverter,
}