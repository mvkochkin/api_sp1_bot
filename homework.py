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


def parse_homework_status(homework):
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
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
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        params=data,
        headers=headers)
    return homework_statuses.json()


def send_message(message, bot_client):
    send_status = bot_client.send_message(CHAT_ID, message)
    logger.info('Сообщение отправлено')
    return send_status


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            error_msg = f'Бот столкнулся с ошибкой: {e}'
            logger.error(error_msg)
            send_message(error_msg, bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
