# coding=utf-8

from abc import ABCMeta, abstractmethod
import re
from six import with_metaclass


class TemperatureCalculator(object):
    TEMP_PATTERN = "\d+"
    CEL_PATTERN = "(?:[cC])+|(?:攝)+"
    FAH_PATTERN = "(?:[fF])+|(?:華)+"

    def __init__(self, question):
        self.question = question

    def get_temp(self, value):
        return re.search(self.TEMP_PATTERN, value).group(0)

    def calculate(self):
        temp = int(self.get_temp(self.question))
        if re.search(self.CEL_PATTERN, self.question):
            return "華氏溫度: {}".format(round((temp * 9.0 / 5) + 32, 2))

        elif re.search(self.FAH_PATTERN, self.question):
            return "攝氏溫度: {}".format(round((temp - 32.0) / 9 * 5, 2))

        return "對不起，我看不懂> <"

    @property
    def result(self):
        return self.calculate()


class BaseConverter(with_metaclass(ABCMeta, object)):
    CONVERT_CLASSES = [] # should be a tuple ("key", converter class)

    def __init__(self, value):
        self.value = value
        assert self.CONVERT_CLASSES, "You should provide CONVERT_CLASSES when using"

    def convert(self):
        converter = self.from_key_to_class()
        return converter(self.value).result

    def from_key_to_class(self):
        for type, converter in self.CONVERT_CLASSES:
            if re.search(type, self.value):
                return converter

        raise KeyError


class TextConverter(BaseConverter):
    CONVERT_CLASSES = [
        ("溫度", TemperatureCalculator),
    ]


class BaseParser(with_metaclass(ABCMeta, object)):
    CONVERTER = None

    def __init__(self, message, user_id=None):
        self.message = message
        self.user_id = user_id
        assert self.CONVERTER

    def parse(self):
        converter = self.get_converter()
        return converter.convert()

    def get_converter(self):
        return self.CONVERTER(self.message)

    def extra_params_converter(self):
        pass


class TextParser(BaseParser):
    CONVERTER = TextConverter