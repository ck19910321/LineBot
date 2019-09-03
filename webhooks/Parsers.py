# coding=utf-8

from abc import ABCMeta, abstractmethod
import re
from six import with_metaclass
from linebot import WebhookHandler, LineBotApi
from linebot.models import TextSendMessage

from .jobs import WoodyReminder


class BaseController(with_metaclass(ABCMeta, object)):
    def __init__(self, message, default="對不起，我看不懂> <", user_id="", room_id=""):
        self.message = message
        self.default = default
        self.user_id = user_id
        self.room_id = room_id

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


class ReminderController(BaseController):

    @property
    def result(self):
        key = "{}_{}".format(self.user_id, self.room_id)
        reminder = WoodyReminder(key=key)
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
        ("提醒", ReminderController)
    ]


class BaseGenerator(with_metaclass(ABCMeta, object)):
    PARSER = None

    def __init__(self, message, user_id="", room_id=""):
        self.message = message
        self.user_id = user_id
        self.room_id = room_id
        assert self.PARSER

    def generate(self):
        parser = self.get_parser()
        return parser.parse()

    def get_parser(self):
        return self.PARSER(message=self.message, user_id=self.user_id, room_id=self.room_id)


class TextGenerator(BaseGenerator):
    PARSER = TextParser
