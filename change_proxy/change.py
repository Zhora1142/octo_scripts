from configparser import ConfigParser
import requests
from colorama import Fore, init
import time

config = ConfigParser()
config.read('config.ini')

API_URL = 'https://app.octobrowser.net/api/v2/automation/'
LOCAL_API_URL = 'http://localhost:58888/api/'

last_request_time = []
minute_limit = int(config['settings']['requests_per_minute'])
hour_limit = int(config['settings']['requests_per_hour'])

class Error:
    error_type = ''
    message = ''
    exception = None

    def __init__(self, error_type, message, exception=None):
        self.error_type = error_type
        self.message = message
        self.exception = exception

    def __str__(self):
        return f'{Fore.RED}({self.error_type}) {self.message}{f": {type(self.exception)}" if self.exception else ""}{Fore.RESET}'


def throttle_requests():
    global last_request_time
    current_time = time.time()
    last_request_time = [t for t in last_request_time if current_time - t < 3600]

    if len(last_request_time) >= hour_limit:
        sleep_time = 3600 - (current_time - last_request_time[0])
        print(f'{Fore.YELLOW}Hourly limit reached. Sleeping for {int(sleep_time)} seconds...{Fore.RESET}')
        time.sleep(sleep_time)
        return

    last_minute = [t for t in last_request_time if current_time - t < 60]
    if len(last_minute) >= minute_limit:
        sleep_time = 60 - (current_time - last_minute[0])
        print(f'{Fore.YELLOW}Minute limit reached. Sleeping for {int(sleep_time)} seconds...{Fore.RESET}')
        time.sleep(sleep_time)

    last_request_time.append(time.time())


def init_exit():
    input('\nPress Enter to close the program...')
    exit()


def parse_range(input_str: str) -> list[int]:
    result = []
    parts = input_str.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))

    return result


def get_profiles():
    request_data = {
        'search_tags': config['settings']['tag'],
        'fields': 'title',
        'ordering': 'created',
        'page': 0
    }

    headers = {
        'X-Octo-Api-Token': config['settings']['token'],
    }

    result = []

    while 1:
        try:
            throttle_requests()
            r = requests.get(API_URL + 'profiles', params=request_data, headers=headers).json()
        except Exception as e:
            return Error('Profiles searching error', 'An error occurred while processing the response from OctoBrowser', e)
        else:
            if not r.get('success'):
                return Error('Profiles searching error', r)
            else:
                if not r['data']:
                    return result

                for i in r['data']:
                    result.append(i)

                request_data['page'] += 1


def edit_proxy(profile_id, proxy):
    request_data = {
        'proxy': {
            'type': config['settings']['proxy_type'],
            'host': proxy.split(':')[0],
            'port': proxy.split(':')[1],
            'login': proxy.split(':')[2],
            'password': proxy.split(':')[3],
        }
    }

    headers = {
        'X-Octo-Api-Token': config['settings']['token'],
    }

    try:
        throttle_requests()
        r = requests.patch(API_URL + f'profiles/{profile_id}', json=request_data, headers=headers).json()
    except Exception as e:
        return Error('Proxy edit error', 'An error occurred while processing the response from OctoBrowser', e)
    else:
        if not r.get('success'):
            return Error('Proxy edit error', r)


def main():
    print('Pre-launch verification...\n')

    profiles = get_profiles()
    if isinstance(profiles, Error):
        print(profiles)
        init_exit()
    proxy_list = open('proxy.txt', 'r').read().splitlines()

    if len(proxy_list) != len(profiles):
        print(Error('Proxies reading error', 'The number of proxy doesn\'t equals to number of profiles in tag'))
        init_exit()

    for i in range(len(proxy_list)):
        proxy = proxy_list[i]
        if not proxy:
            continue

        result = edit_proxy(profiles[i]['uuid'], proxy)
        if isinstance(result, Error):
            print(result)
        else:
            print(f'{Fore.GREEN}Proxy edit on {profiles[i]["uuid"]} ({profiles[i]["title"]}) succeeded{Fore.RESET}')

    init_exit()


if __name__ == '__main__':
    init()
    main()
