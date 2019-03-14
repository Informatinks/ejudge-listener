import codecs
import gzip
import os

from flask import current_app


def read_file_unknown_encoding(file_name, size=255):
    try:
        f = codecs.open(file_name, 'r', encoding='utf-8')
        res = f.read(size)
    except UnicodeDecodeError:
        f = codecs.open(file_name, 'r', encoding='koi8-r')
        res = f.read(size)
    return res


def get_protocol_from_file(filename):
    if os.path.isfile(filename):
        myopen = open
    else:
        filename += '.gz'
        myopen = gzip.open
    try:
        xml_file = myopen(filename, 'r')
        try:
            xml_file.readline()
            xml_file.readline()
            res = xml_file.read()
            try:
                return str(res, encoding='UTF-8')
            except TypeError:
                return res
        except:
            return ''
    except IOError:
        return ''


"""Статусы посылок задач.

0  => 'OK'
99 => 'Перетестировать'
8  => 'Зачтено/Принято'
14 => 'Ошибка оформлени кода'
9  => 'Проигнорировано'
1  => 'Ошибка компиляции'
10 => 'Дисквалифицировано
7  => 'Частичное решение
11 => 'Ожидает проверки'
2  => 'Ошибка во время выполнения программы
3  => 'Превышено максимальное врем работы'
4  => 'Неправильный формат вывода'
5  => 'Неправильный ответ'
6  => 'Ошибка проверки, обратитесь к администраторам'
12 => 'Превышение лимиа памяти'
13 => 'Security error'
96 => 'Тестирование...'
98 => 'Компилирование...'
"""
TERMINAL_STATUSES = {0, 99, 8, 14, 9, 1, 10, 7, 11, 2, 3, 4, 5, 6, 12, 13}
NON_TERMINAL_STATUSES = {96, 98}


def get_string_status(s):
    return {
        "OK": "OK",
        "WA": "Неправильный ответ",
        "ML": "Превышение лимита памяти",
        "SE": "Security error",
        "CF": "Ошибка проверки,<br/>обратитесь к администраторам",
        "PE": "Неправильный формат вывода",
        "RT": "Ошибка во время выполнения программы",
        "TL": "Превышено максимальное время работы",
        "WT": "Превышено максимальное общее время работы",
        "SK": "Пропущено",
    }[s]


def submit_path(tp, contest_id, submit_id):
    # path to archive file with path to archive directory = tp,
    # look up AUDIT_PATH etc constants
    return os.path.join(
        current_app.config['CONTEST_PATH'],
        '0' * (6 - len(str(contest_id))) + str(contest_id),
        tp,
        to32(submit_id // 32 // 32 // 32 % 32),
        to32(submit_id // 32 // 32 % 32),
        to32(submit_id // 32 % 32),
        '0' * (6 - len(str(submit_id))) + str(submit_id),
    )


# TODO: enum вместо пути и на значении будет соотвествующий ProtocolNotFoundError
def safe_open(path, tp, encoding=None):
    """
    Function to open file with path is equal to parameter path. It tries to open as plain file,
    then as gz archive. Returnes a filelike object.
    """
    try:
        file = open(path, tp, encoding=encoding)
    except FileNotFoundError as e:
        file = gzip.open(path + '.gz', tp, encoding=encoding)
    return file


def to32(num):
    if num < 10:
        return str(num)
    else:
        return chr(ord('A') + num - 10)
