"""Checks the current status of homework and sends messages."""

import os
import sys
import requests
import time
from http import HTTPStatus

from dotenv import load_dotenv
from telegram import Bot

from exceptions import UndefinedHomeworkStatus, FailedToSendMessage, HTTPError
from logger import logger_setup


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Checked: everything is fine',
    'reviewing': 'Homework was taken for checking',
    'rejected': 'Checked: reviewer has comments'
}


logger = logger_setup(__name__)


def send_message(bot, message):
    """Sends messages to telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Message sent successfully')
    except Exception:
        raise FailedToSendMessage('Failed to send message')


def get_api_answer(timestamp: int) -> dict:
    """Return correct answers from Yandex.Practicum API."""
    logger.info('Send request to API')

    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise ConnectionError('Failded to get response from API') from error

    if not response.status_code == HTTPStatus.OK:
        message = ('Seems to be something wrong with API.\n'
                   f'Response status code: {response.status_code}.\n'
                   f'URL: {response.url}.')
        raise HTTPError(message)
    return response.json()


def check_response(response) -> list:
    """Check response for correctness."""
    logger.info('Check response for correctness')

    if not isinstance(response, dict):
        raise TypeError('Response is not a dict')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('Key homeworks or current_date have not found in response')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('homeworks is not a list')

    return response.get('homeworks')


def parse_status(homework) -> str:
    """Parse information about homework."""
    logger.info('Parse information about homework')

    if (
        'homework_name' not in homework
        or 'status' not in homework
    ):
        raise KeyError('Unexpected response from API')

    homework_name = homework.get('homework_name')
    verdict = homework.get('status')

    if verdict not in VERDICTS:
        message = 'Unexpected homework status'
        raise UndefinedHomeworkStatus(message)

    verdict = VERDICTS.get(verdict)

    return f'Homework checking status changed "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Checks that all enviroment variables are defined."""
    variables_exists = all([
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
        PRACTICUM_TOKEN
    ])
    return variables_exists


def main():
    """Main logic."""
    bot = Bot(token=TELEGRAM_TOKEN)

    prev_report = None

    if not check_tokens():
        message = 'One or several enviroment variables are not defined'
        logger.critical(message)
        sys.exit(message)

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
                    prev_report = str(current_report)
            else:
                logger.info('No updates found')

            current_timestamp = (
                response.get('current_date')
                or int(time.time())
            )

        except Exception as error:
            message = f'Application crashed: {error}'
            logger.error(message)
            current_report = message
            if not current_report == prev_report:
                send_message(bot, message)
                prev_report = str(current_report)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
