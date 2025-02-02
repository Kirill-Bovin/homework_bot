import logging
import os
import sys
import time
import copy
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from exceptions import KirillTeleBotError, HttpResponseNotOkError, WrongKeyHw

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
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
    """Проверка токеннов."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправка сообщений."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'send_message: Бот отправил сообщение: {message}')
    except telegram.error.TelegramError:
        logging.error('send_message: Сообщение с текстом'
                      f'{message} не отправленно')


def get_api_answer(timestamp: int = int(time.time())):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise KirillTeleBotError(error)
    if response.status_code != HTTPStatus.OK:
        logging.error(f'{ENDPOINT}, не передает данные')
        raise HttpResponseNotOkError(
            f'Код ошибки: {response.status_code}')
    return response.json()


def check_response(response):
    """Функция проверки ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком')
    return homeworks


def parse_status(homework):
    """Функция извлечения статуса конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        error_message = 'В ответе API нет ключа "homework_name"'
        logging.error(error_message)
        raise WrongKeyHw(error_message)
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        logging.error(f'Неожиданный статус {status} домашней работы'
                      f'{homework_name}, обнаруженный в ответе API')
        raise WrongKeyHw('Неожиданный статус домашней работы'
                         'обнаруженный в ответе API')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствуют обязательные переменные окружения'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    cur_status = {"hw_name": "", "message": ""}
    prev_status = {"hw_name": "", "message": ""}
    timestamp = int(time.time())
    old_error_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                cur_status["hw_name"] = homeworks[0]["homework_name"]
                cur_status["message"] = parse_status(homeworks[0])
            else:
                cur_status["message"] = "Не принята ревьюером"
            if cur_status != prev_status:
                send_message(bot, cur_status["message"])
                prev_status = copy.deepcopy(cur_status)
            else:
                logging.debug('нет новых статусов')
                timestamp = response.get('current_date')
        except Exception as error:
            logging.exception('Сбой в работе программы:', error)
            if message != old_error_message:
                send_message(bot, message)
                old_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
    main()
