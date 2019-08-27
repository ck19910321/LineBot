# coding=utf-8
import re


class TemperatureCalculator(object):
    TEMP_PATTERN = "\d+"
    # CEL_PATTERN = u"[c|C|\u651d\u6c0f]"
    # FAH_PATTERN = u"[f|F|\u83ef\u6c0f]"
    CEL_PATTERN = u"[c|C|攝氏]"
    FAH_PATTERN = u"[f|F|華氏]"

    def __init__(self, question):
        self.question = question

    def get_temp(self, value):
        return re.search(self.TEMP_PATTERN, value).group(0)

    def get_cel_type(self, value):
        return re.match(self.CEL_PATTERN, value)

    def get_fah_type(self, value):
        return re.match(self.CEL_PATTERN, value)

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

    def responde(self):
        pass


class TextParser(Parser):
    TYPE = {
        "溫度": TemperatureCalculator
    }

    def parse(self):
        question = self.message.split(" ")

        try:
            return self._answer(question[0], question[1])
        except IndexError:
            return "????"

    def _answer(self, type, question):
        type_to_answer = self.TYPE[type]
        return type_to_answer(question).calculate()
