import os
import requests
from dotenv import load_dotenv
import time
import telegram
load_dotenv()

token = os.getenv('TOKEN')

def get_status(current_time):
    data = {'from_date': current_time}
    headers = {'Authorization': f'OAuth {token}'}
    status = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        params=data,
        headers=headers
    ).json().get('homeworks')
    if status == []:
        pass
    parse_status_map={'homework_status': status}
    return parse_status_map

time_now = int(time.time())
print(get_status(time_now))
