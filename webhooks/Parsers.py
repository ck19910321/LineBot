# coding=utf-8

from abc import ABCMeta
import json
import re
from six import with_metaclass
from linebot.models import (
    TextSendMessage,
    TemplateSendMessage,
    DatetimePickerAction,
    ButtonsTemplate,
    PostbackAction,
)

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
                return TextSendMessage(
                    text="華氏溫度: {}".format(round((temp * 9.0 / 5) + 32, 2))
                )

            elif re.search(self.FAH_PATTERN, self.message):
                return TextSendMessage(
                    text="攝氏溫度: {}".format(round((temp - 32.0) / 9 * 5, 2))
                )

        except (ValueError, TypeError):
            pass

        return TextSendMessage(text=self.default)


class DateTimeConvertController(BaseController):
    TIME_ZONE_CONVERT = [
        ("(?:台灣)+|(?:Tai)+|(?:tai)+", 8),
        ("(?:美國)+|(?:洛杉磯)+|(?:LA)+", -7),
        ("(?:日本)+|(?:大阪)+", 9),
    ]

    def _split_country(self, message):
        countries = message.split("時間轉換")
        return countries[0], countries[1]

    @property
    def result(self):
        from_country, to_country = self._split_country(self.message)
        from_hours = 0
        to_hours = 0
        for zone, shift_hours in self.TIME_ZONE_CONVERT:
            from_country_match = re.search(zone, from_country)
            if not from_hours and from_country_match:
                from_hours = shift_hours
                from_country = from_country_match.group(0)

            to_country_match = re.search(zone, to_country)
            if not to_hours and to_country_match:
                to_hours = shift_hours
                to_country = to_country_match.group(0)

        if from_hours and to_hours:
            return TemplateSendMessage(
                alt_text="時間轉換",
                template=ButtonsTemplate(
                    title="時間轉換",
                    text="{} 轉換至 {}".format(from_country, to_country),
                    actions=[
                        DatetimePickerAction(
                            label="請選擇想轉換的時間",
                            data="type=date_convert&action=choose&from_country={from_country}&to_country={to_country}&from_hours={from_hours}&to_hours={to_hours}".format(
                                from_country=from_country,
                                to_country=to_country,
                                from_hours=from_hours,
                                to_hours=to_hours,
                            ),
                            mode="datetime",
                        )
                    ],
                ),
            )
        return TextSendMessage(text="對不起 請輸入 <地區> 時間轉換 <地區>")


class ReminderController(BaseController):
    @property
    def result(self):
        return TemplateSendMessage(
            alt_text="提醒小幫手",
            template=ButtonsTemplate(
                title="提醒事項",
                text="請選擇時區",
                actions=[
                    PostbackAction(
                        label="台灣時區",
                        data="type=reminder&action=choose_date&tz=8&text={}".format(
                            self.message
                        ),
                    ),
                    PostbackAction(
                        label="美國時區",
                        data="type=reminder&action=choose_date&tz=-7&text={}".format(
                            self.message
                        ),
                    ),
                    PostbackAction(
                        label="日本時區",
                        data="type=reminder&action=choose_date&tz=9&text={}".format(
                            self.message
                        ),
                    ),
                ],
            ),
        )


class BaseParser(with_metaclass(ABCMeta, object)):
    CONVERT_CLASSES = []  # should be a tuple ("key", converter class)

    def __init__(self, message, user_id=None, room_id=None):
        self.value = message
        self.user_id = user_id
        self.room_id = room_id
        assert self.CONVERT_CLASSES, "You should provide CONVERT_CLASSES when using"

    def parse(self):
        converter = self.from_key_to_class()
        return converter(
            message=self.value, user_id=self.user_id, room_id=self.room_id
        ).result

    def from_key_to_class(self):
        for type, converter in self.CONVERT_CLASSES:
            if re.search(type, self.value):
                return converter

        raise KeyError


class TextParser(BaseParser):
    CONVERT_CLASSES = [
        ("溫度", TemperatureController),
        ("提醒", ReminderController),
        ("時間轉換", DateTimeConvertController),
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
        return self.PARSER(
            message=self.message, user_id=self.user_id, room_id=self.room_id
        )


class TextGenerator(BaseGenerator):
    PARSER = TextParser
