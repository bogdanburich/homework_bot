"""Проверяет актуальный статус домашней работы и отправляет сообщения."""

import os
import requests
import time
import logging  # строчка для теста

from dotenv import load_dotenv
from telegram import Bot

from exceptions import UndefinedHomeworkStatus, FailedToSendMessage
from logger import logger_setup
logging  # строчка для теста


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logger_setup(__name__)


def send_message(bot, message):
    """Отправляет сообщения в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except Exception:
        raise FailedToSendMessage('Не удалось отправить сообщение')


def get_api_answer(timestamp: int) -> dict:
    """Возвращает корректный результат ответа от API Я.Практикума."""
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    """
    Кажется, здесь правильнее использовать такую конструкцию:
    response.raise_for_status(...), но с ней не проходят тесты, т.к. там
    используется объект класса MockResponseGET, а не Response, ошибка в тестах:
    AttributeError: 'MockResponseGET' object has no attribute raise_for_status
    """
    if not response.status_code == 200:
        message = ('Кажется c API Я.Практикума что-то не так. '
                   f'Код ответа: {response.status_code}')
        raise requests.HTTPError(message)
    return response.json()


def check_response(response) -> list:
    """Проверяет ответ от API Я.Практикума на корректность."""
    if not (
        isinstance(response, dict)
        and 'homeworks' in response.keys()
        and isinstance(response['homeworks'], list)
    ):
        message = 'Неожиданный ответ от API Я.Практикума'
        raise TypeError(message)
    return response['homeworks']


def parse_status(homework) -> str:
    """Извлекает информацию о конкретной домашней работе."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        message = 'Неожиданный статус проверки работы'
        raise UndefinedHomeworkStatus(message)

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет, что необходимые переменные окружения определены."""
    variables_exists = (
        TELEGRAM_TOKEN is not None
        and TELEGRAM_CHAT_ID is not None
        and PRACTICUM_TOKEN is not None
    )
    return variables_exists


def main():
    """Основная логика работы бота."""
    error_message_sent = False

    bot = Bot(token=TELEGRAM_TOKEN)

    if not check_tokens():
        message = 'Одна или несколько переменных окружения не определены'
        try:
            send_message(bot, message)
            logger.critical(message)
        except Exception:
            logger.critical(message)

    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if len(homeworks) != 0:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)

            current_timestamp = (
                response.get('current_date')
                or int(time.time())
            )
            time.sleep(RETRY_TIME)
            logger.info('Новых работ не найдено')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if not error_message_sent:
                error_message_sent = True
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
