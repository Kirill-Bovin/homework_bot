import os

from dotenv import load_dotenv

import time

import logging

from http import HTTPStatus

import requests

from logging.handlers

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    logging.info('Проверка переменных окружения')
    tokens = (
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
    )
    for token_name, token_value in tokens:
        if not token_value:
            logging.critical(
                f'Отсутствует переменная окружения: {token_name}')
            return False
    logging.info('Проверка успешна')
    return True


def send_message(bot, message):
    """Проверка отправки сообщения."""
    logging.info('Отправка сообщения пользователю')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Отправлено сообщение "{message}"')
    except Exception:
        raise exceptions.SendMessageError


def get_api_answer(timestamp):
    logging.info('Отправка запроса к API')
    timestamp = timestamp or int(time.time())
    params = {'from_date': timestamp}
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    try:
        response = requests.get(**request_params)
    except Exception:
        raise exceptions.EndPointError

    if response.status_code != HTTPStatus.OK:
        raise exceptions.EndPointError('Сервер не получил ожидаемый ответ')

    try:
        response_json = response.json()
    except Exception:
        raise exceptions.ResponseJsonError
    else:
        logging.info('Сервер получил правильный ответ')
        return response_json


def check_response(response):
    logging.info('Проверка ответа API на валидность')
    api_keys = ('homeworks', 'current_date')
    if not isinstance(response, dict):
        raise TypeError(
            'Тип данных ответа сервера не соответствует ожидаемому (dict)')

    for key in api_keys:
        if key not in response:
            raise exceptions.APIKeyError

    homework = response.get('homeworks')
    if not isinstance(homework, list):
        raise TypeError(
            'Тип данных списка работ не соответствует ожидаемому (list)')

    logging.info('Ответ API валиден')
    return homework


def parse_status(homework):
    logging.info('Проверка статуса домашней работы')
    keys = ('homework_name', 'status')
    for key in keys:
        if key not in homework:
            raise KeyError(f'Ключ {key} отсутствует в домашней работе')

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.HomeWorkStatusError
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
