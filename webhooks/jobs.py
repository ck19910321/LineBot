from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from six import with_metaclass
import json

from django.core.cache import cache
from linebot.models import TemplateSendMessage, TextSendMessage
from linebot.models.actions import (
    PostbackAction,
    MessageAction,
    URIAction,
    DatetimePickerAction,
)
from linebot.models.template import ButtonsTemplate, CarouselTemplate, CarouselColumn

from .tasks import send


def get_readable_date_time(date_time):
    return date_time.strftime("%Y-%m-%d %I:%M %p")


def to_date_time_object(date_time):
    return datetime.strptime(date_time, "%Y-%m-%dT%H:%M")


class BaseDataWrapper(object):
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def new_from_dict(cls, data):
        return cls(**data)


class TimeConvertParamsWrapper(BaseDataWrapper):
    def __init__(
        self,
        from_country="",
        to_country="",
        from_hours=0,
        to_hours=0,
        target_datetime=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.target_datetime = target_datetime
        self.from_country = from_country
        self.to_country = to_country
        self.from_hours = from_hours
        self.to_hours = to_hours


class ReminderDataWrapper(BaseDataWrapper):
    def __init__(self, text="", tz=None, target_date_time=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.tz = int(tz)
        self.target_date_time = target_date_time


class BaseWoody(with_metaclass(ABCMeta, object)):
    WRAPPER_CLASS = None

    def __init__(self, data, key=None, type=None, *args, **kwargs):
        self.type = type
        self.key = key
        self.wrapper_data_instance = self._get_wrapper_instance(data)
        self.actions = self.get_actions()

    def get_actions(self):
        return set(
            [
                func
                for func in dir(self)
                if func.startswith("can_") and callable(getattr(self, func))
            ]
        )

    @classmethod
    def new_from_data(cls, **data):
        return cls(**data)

    def _get_wrapper_instance(self, data):
        return self.WRAPPER_CLASS(**data)


class WoodyTimeConverter(BaseWoody):
    WRAPPER_CLASS = TimeConvertParamsWrapper

    def __init__(self, type="date_convert", *args, **kwargs):
        super().__init__(type=type, *args, **kwargs)

    def can_choose(self):
        orig_date = to_date_time_object(self.wrapper_data_instance.target_datetime)
        utc_date = orig_date - timedelta(hours=self.wrapper_data_instance.from_hours)
        new_date = utc_date + timedelta(hours=self.wrapper_data_instance.to_hours)
        return TextSendMessage(
            text="{instance.from_country}時間: {orig_date}，轉換至{instance.to_country}時間:{new_date}".format(
                instance=self.wrapper_data_instance,
                orig_date=get_readable_date_time(orig_date),
                new_date=get_readable_date_time(new_date),
            )
        )


class WoodyReminder(BaseWoody):
    WRAPPER_CLASS = ReminderDataWrapper

    def __init__(self, type="reminder", *args, **kwargs):
        super().__init__(type=type, *args, **kwargs)

    def can_choose_date(self):
        return TemplateSendMessage(
            alt_text="提醒小幫手",
            template=ButtonsTemplate(
                title="提醒事項",
                text="請選擇想提醒的時間",
                actions=[
                    DatetimePickerAction(
                        label="請選擇想轉換的時間",
                        data="type={type}&action=add_to_reminder&tz={tz}&text={text}".format(
                            type=self.type,
                            tz=self.wrapper_data_instance.tz,
                            text=self.wrapper_data_instance.text,
                        ),
                        mode="datetime",
                    )
                ],
            ),
        )

    def can_add_to_reminder(self):
        time_to_send = to_date_time_object(
            self.wrapper_data_instance.target_datetime
        ) - timedelta(self.wrapper_data_instance.tz)

        user_id, room_id = self.key.split("_")
        target = room_id if room_id else user_id
        send.apply_async((target, self.wrapper_data_instance.text), eta=time_to_send)

        return TextSendMessage(
            text="設定完畢！將於 {} 提醒您。".format(
                get_readable_date_time(self.wrapper_data_instance.target_datetime)
            )
        )


JOB_API = {"reminder": WoodyReminder, "date_convert": WoodyTimeConverter}
