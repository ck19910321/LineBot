# coding=utf-8
import re


class TemperatureCalculator(object):
    TEMP_PATTERN = r"\d+"
    CEL_PATTERN = r"[cC攝]"
    FAH_PATTERN = r"[fF華]"

    def __init__(self, question):
        self.question = question

    @classmethod
    def get_temp(self, value):
        return re.search(self.TEMP_PATTERN, value).group(0)

    @classmethod
    def get_cel_type(self, value):
        return re.search(self.CEL_PATTERN, value)

    @classmethod
    def get_fah_type(self, value):
        return re.search(self.FAH_PATTERN, value)

    def calculate(self):
        temp = int(self.get_temp(self.question))
        if self.get_cel_type(self.question):
            return round((temp * 9.0 / 5) + 32, 2)

        return round((temp - 32.0) * 5 / 9, 2)


class Parser(object):
    def __init__(self, message, user_id=None):
        self.message = message
        self.user_id = user_id

    def parse(self):
        pass


class TextParser(Parser):
    TYPES = {
        "溫度": TemperatureCalculator
    }

    def parse(self):
        for type in self.TYPES:
            if re.search(type, self.message):
                type_to_answer = self.TYPES[type]
                return type_to_answer(self.message.replace(type, "")).calculate()
        return
