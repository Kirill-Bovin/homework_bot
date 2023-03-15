import logging
import os
import sys
import time
from http import HTTPStatus
from logging import FileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot, TelegramError

from exceptions import GetAPIException, UnavailableAPIException, err_msg

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

env_dict = {
    PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
    TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
    TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID'
}

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

RETRY_TIME = 600

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)
handler = FileHandler(filename='main.log', mode='w', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия переменных среды."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def err_msg_to_log(error):
    """Отправка сообщения об ошибке в лог."""
    logger.error(err_msg(error))


def send_message(bot, message):
    """Отправка сообщения в чат."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logger.info(f'Бот отправил сообщение \"{message}\"')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=payload)
        logger.info('Получен ответ API.')
        if response.status_code != HTTPStatus.OK:
            error = (
                f'Эндпоинт {ENDPOINT} недоступен. '
                f'Код ответа API: {response.status_code}'
            )
            raise UnavailableAPIException(error)
        return response.json()
    except Exception as error:
        raise GetAPIException(error)


def check_response(response_json):
    """Проверка ответа API на корректность."""
    logger.info('Ответ API проверяется на корректность.')
    if not isinstance(response_json, dict):
        raise TypeError('Ответ API приходит не в виде словаря.')
    homeworks = response_json.get('homeworks')
    if homeworks is None:
        raise KeyError('В ответе API отсутствует список домашних заданий.')
    if not isinstance(homeworks, list):
        raise TypeError('Домашнее задание приходит не в виде списка.')
    if response_json.get('current_date') is None:
        raise KeyError('В ответе API отсутствует метка времени.')
    return homeworks


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('В ответе API отсутствует имя работы.')
    status = homework.get('status')
    if status is None:
        raise KeyError('В ответе API отсутствует статус работы.')
    verdict = HOMEWORK_STATUSES.get(status)
    if verdict is None:
        raise KeyError('Неправильный статус работы.')
    answer = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return answer


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        msg = (
            'Отсутствует обязательная переменная окружения: '
            f'\'{env_dict[None]}\'\n'
            'Программа принудительно остановлена'
        )
        logger.critical(msg)
        sys.exit(msg)

    homework_status = None
    bot = Bot(token=TELEGRAM_TOKEN)

    api_error = False

    current_timestamp = int(time.time())

    while True:
        try:
            send_message(bot, 'Проверка сообщения')
            api_answer = get_api_answer(current_timestamp)
            homeworks = check_response(api_answer)
            current_timestamp = api_answer.get('current_date')
            if homeworks:
                old_status = homework_status
                homework_status = parse_status(homeworks[0])
                if (old_status != homework_status):
                    send_message(bot, homework_status)
                else:
                    logger.debug('Новых статусов нет.')
            else:
                old_status = None
                homework_status = None
        except GetAPIException as error:
            err_msg_to_log(error)
            if not api_error:
                send_message(bot, err_msg(error))
                api_error = True
        except TelegramError as error:
            err_msg_to_log(error)
        except Exception as error:
            err_msg_to_log(error)
            send_message(bot, err_msg(error))
        else:
            api_error = False
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
