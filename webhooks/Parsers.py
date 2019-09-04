# coding=utf-8

from abc import ABCMeta
from datetime import datetime, timedelta
import re
from six import with_metaclass
from linebot.models import TextSendMessage, TemplateSendMessage, DatetimePickerAction, ButtonsTemplate

from .jobs import WoodyReminder, WoodyTimeConverter


class BaseController(with_metaclass(ABCMeta, object)):
    def __init__(self, message, default="對不起，我看不懂> <", user_id="", room_id=""):
        self.message = message
        self.default = default
        self.key = "{}_{}".format(user_id, room_id)

    @property
    def result(self):
        raise NotImplementedError


class TemperatureController(BaseController):
    # a tool to calculator tempature and return result
    TEMP_PATTERN = "\d+"
    CEL_PATTERN = "(?:[cC])+|(?:攝)+"
    FAH_PATTERN = "(?:[fF])+|(?:華)+"

    def get_temp(self, value):
        find_match = re.search(self.TEMP_PATTERN, value)
        if find_match:
            return find_match.group(0)

    @property
    def result(self):
        try:
            temp = int(self.get_temp(self.message))
            if re.search(self.CEL_PATTERN, self.message):
                return TextSendMessage(text="華氏溫度: {}".format(round((temp * 9.0 / 5) + 32, 2)))

            elif re.search(self.FAH_PATTERN, self.message):
                return TextSendMessage(text="攝氏溫度: {}".format(round((temp - 32.0) / 9 * 5, 2)))

        except (ValueError, TypeError):
            pass

        return TextSendMessage(text=self.default)


class DateTimeConvertController(BaseController):
    TIME_ZONE_CONVERT = [
        ("(?:台灣)+|(?:Tai])+|(?:tai])+", 8 * -1,),
        ("(?:美國)+|(?:洛杉磯])+|(?:LA])+", 7),
        ("(?:日本)+|(?:大阪])+", 9 * -1),
    ]


    @property
    def result(self):
        _to_new_date = datetime.utcnow()
        for zone, shift_hours in self.TIME_ZONE_CONVERT:
            match = re.search(zone, self.message)
            if match:
                time_converter = WoodyTimeConverter(key=self.key)
                time_converter.set_cache(shift_hours)

                country = match.group(0)
                return TemplateSendMessage(
                    alt_text='時間轉換',
                    template=ButtonsTemplate(
                        title='時間轉換',
                        text="轉換至{}".format(country),
                        actions=[
                            DatetimePickerAction(
                                label="請選擇想轉換的時間",
                                data="type=date_convert&action=choose",
                                mode="datetime",
                            )
                        ]
                    )
                )
        return TextSendMessage(text=self.default)


class ReminderController(BaseController):
    @property
    def result(self):
        reminder = WoodyReminder(key=self.key)
        return reminder.can_add_reminder(self.message)



class BaseParser(with_metaclass(ABCMeta, object)):
    CONVERT_CLASSES = [] # should be a tuple ("key", converter class)

    def __init__(self, message, user_id=None, room_id=None):
        self.value = message
        self.user_id = user_id
        self.room_id = room_id
        assert self.CONVERT_CLASSES, "You should provide CONVERT_CLASSES when using"

    def parse(self):
        converter = self.from_key_to_class()
        return converter(message=self.value, user_id=self.user_id, room_id=self.room_id).result

    def from_key_to_class(self):
        for type, converter in self.CONVERT_CLASSES:
            if re.search(type, self.value):
                return converter

        raise KeyError


class TextParser(BaseParser):
    CONVERT_CLASSES = [
        ("溫度", TemperatureController),
        ("提醒", ReminderController),
        ("時間轉換", DateTimeConvertController)
    ]


class BaseGenerator(with_metaclass(ABCMeta, object)):
    PARSER = None

    def __init__(self, message, user_id="", room_id=""):
        self.message = message
        self.user_id = user_id
        self.room_id = room_id

    def generate(self):
        parser = self.get_parser()
        return parser.parse()

    def get_parser(self):
        return self.PARSER(message=self.message, user_id=self.user_id, room_id=self.room_id)


class TextGenerator(BaseGenerator):
    PARSER = TextParser
