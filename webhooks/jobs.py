import attr
from abc import ABCMeta
from datetime import datetime, timedelta
from six import with_metaclass

from linebot.models import TemplateSendMessage, TextSendMessage
from linebot.models.actions import DatetimePickerAction
from linebot.models.template import ButtonsTemplate

from .tasks import send


def get_readable_date_time(date_time):
    return date_time.strftime("%Y-%m-%d %I:%M %p")


class DateTimeConvert(object):
    @classmethod
    def to_datetime(self, datetime_str):
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")


@attr.s
class TimeConvertParamsWrapper(object):
    target_datetime = attr.ib(converter=DateTimeConvert.to_datetime)
    from_country = attr.ib(default="")
    to_country = attr.ib(default="")
    from_hours = attr.ib(converter=int, default=0)
    to_hours = attr.ib(converter=int, default=0)



@attr.s
class ReminderDataWrapper(object):
    target_datetime = attr.ib(converter=DateTimeConvert.to_datetime, init=False)
    text = attr.ib(default="")
    tz = attr.ib(converter=int, default=0)


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

    def _get_wrapper_instance(self, data):
        return self.WRAPPER_CLASS(**data)


class WoodyTimeConverter(BaseWoody):
    WRAPPER_CLASS = TimeConvertParamsWrapper

    def __init__(self, type="date_convert", *args, **kwargs):
        super().__init__(type=type, *args, **kwargs)

    def can_choose(self):
        utc_date = self.wrapper_data_instance.target_datetime - timedelta(hours=self.wrapper_data_instance.from_hours)
        new_date = utc_date + timedelta(hours=self.wrapper_data_instance.to_hours)
        return TextSendMessage(
            text="{instance.from_country}時間: {orig_date}，轉換至{instance.to_country}時間:{new_date}".format(
                instance=self.wrapper_data_instance,
                orig_date=get_readable_date_time(self.wrapper_data_instance.target_datetime),
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
                        label="選擇時間",
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
        time_to_send = self.wrapper_data_instance.target_datetime - timedelta(hours=self.wrapper_data_instance.tz)
        user_id, room_id = self.key.split("_")
        target = room_id if room_id else user_id
        reminder_text = "來自專屬秘書的叮嚀: \n {}".format(self.wrapper_data_instance.text)
        send.apply_async((target, reminder_text), eta=time_to_send)

        return TextSendMessage(
            text="設定完畢！將於 {} 提醒您。".format(get_readable_date_time(self.wrapper_data_instance.target_datetime))
        )


JOB_API = {"reminder": WoodyReminder, "date_convert": WoodyTimeConverter}
