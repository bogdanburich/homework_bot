"""Проверяет актуальный статус домашней работы и отправляет сообщения."""

import os
import sys
import requests
import time
import logging  # строчка для теста
from http import HTTPStatus

from dotenv import load_dotenv
from telegram import Bot

from exceptions import UndefinedHomeworkStatus, FailedToSendMessage, HTTPError
from logger import logger_setup
logging  # строчка для теста


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
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
    logging.info('Отправляем запрос к API')

    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise ConnectionError('Не удалось получить ответ от API') from error

    if not response.status_code == HTTPStatus.OK:
        message = ('Кажется c API Я.Практикума что-то не так.\n'
                   f'Код ответа: {response.status_code}.\n'
                   f'URL: {response.url}.')
        raise HTTPError(message)
    return response.json()


def check_response(response) -> list:
    """Проверяет ответ от API Я.Практикума на корректность."""
    logging.info('Проверяем запрос на корректность')

    message = 'Неожиданный ответ от API Я.Практикума'

    try:
        response_is_dict = isinstance(response, dict)
        homeworks_in_reponse = 'homeworks' in response
        homeworks_is_list = isinstance(response.get('homeworks'), list)
        current_date_in_response = 'current_date' in response
    except Exception:
        raise TypeError(message)

    if not all([
        response_is_dict,
        homeworks_in_reponse,
        homeworks_is_list,
        current_date_in_response
    ]):
        raise TypeError(message)

    return response.get('homeworks')


def parse_status(homework) -> str:
    """Извлекает информацию о конкретной домашней работе."""
    logging.info('Извлекаем информацию о домашней работе')

    if (
        'homework_name' not in homework
        or 'status' not in homework
    ):
        raise KeyError('Неожиданный ответ от API Я.Практикума')

    homework_name = homework.get('homework_name')
    verdict = homework.get('status')

    if verdict not in VERDICTS:
        message = 'Неожиданный статус проверки работы'
        raise UndefinedHomeworkStatus(message)

    verdict = VERDICTS.get(verdict)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет, что необходимые переменные окружения определены."""
    variables_exists = all([
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
        PRACTICUM_TOKEN
    ])
    return variables_exists


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)

    prev_report = None

    if not check_tokens():
        message = 'Одна или несколько переменных окружения не определены'
        try:
            logger.critical(message)
            sys.exit(message)
        except Exception:
            logger.critical(message)

    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                current_report = message
                if not current_report == prev_report:
                    send_message(bot, message)
                    prev_report = current_report.copy()
            else:
                logger.info('Обновлений не найдено')

            current_timestamp = (
                response.get('current_date')
                or int(time.time())
            )

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            current_report = message
            if not current_report == prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
