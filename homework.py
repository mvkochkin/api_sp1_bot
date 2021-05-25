import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='homework.log',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'homework.log',
    maxBytes=5000000,
    backupCount=1
)
logger.addHandler(handler)


class APIResponseDataError(Exception):
    '''Исключение, вызывающееся при некоректных
    данных, содержащихся в ответе от API
    '''

    def __init__(self, message='В ответе содержатся некорректные данные'):
        self.message = message
        super().__init__(self.message)


def parse_homework_status(homework):
    correct_status_list = ['rejected', 'approved', 'reviewing']
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name == '' or homework_status not in correct_status_list:
        raise APIResponseDataError
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'reviewing':
        verdict = 'Работа взята на ревью'
    else:
        verdict = (
            'Ревьюеру всё понравилось, '
            'можно приступать к следующему уроку.'
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    data = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            API_URL,
            params=data,
            headers=headers)
        return homework_statuses.json()
    except Exception as e:
        error_msg = f'Возникла проблема с доступом к API. Ошибка: {e}'
        logger.error(error_msg)


def send_message(message, bot_client):
    send_status = bot_client.send_message(CHAT_ID, message)
    logger.info('Сообщение отправлено')
    return send_status


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен')
    current_timestamp = int(time.time())
    time_for_error_renew = int(time.time())
    err_tmp = str()

    send_message('Бот запущен', bot)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homework_data = new_homework.get('homeworks')
            if homework_data:
                send_message(
                    parse_homework_status(homework_data[0]),
                    bot
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(600)

        except Exception as e:
            error_msg = f'Бот столкнулся с ошибкой: {e}'
            logger.error(error_msg)
            if error_msg != err_tmp:
                err_tmp = error_msg
                send_message(error_msg, bot)
            time.sleep(60)

        if int(time.time()) - 3600 > time_for_error_renew:
            err_tmp = str()
            time_for_error_renew = int(time.time())


if __name__ == '__main__':
    main()
