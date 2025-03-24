from configparser import ConfigParser
from requests import Session
from time import sleep

config = ConfigParser()
config.read('config.ini')

s = Session()
s.headers = {
    'X-Octo-Api-Token': config['settings']['token']
}


def create_profile(title, tag, proxy):
    host, port, login, password = proxy.split(':')

    data = {
        'title': title,
        'tags': [tag],
        'fingerprint': {
            'os': 'win'
        },
        'proxy': {
            'type': config['settings']['proxy_type'],
            'host': host,
            'port': port,
            'login': login,
            'password': password
        }
    }

    if config['settings']['storage'] == '1':
        data['storage_options'] = {
            "cookies": True,
            "passwords": True,
            "extensions": True,
            "localstorage": True,
            "history": True,
            "bookmarks": True,
            "serviceworkers": True
        }

    s.post('https://app.octobrowser.net/api/v2/automation/profiles', json=data)


def main():
    proxies = open('proxy.txt').read().splitlines()
    proxy_index = 0

    if '-' in config['settings']['number']:
        from_profile = int(config['settings']['number'].split('-')[0])
        to_profile = int(config['settings']['number'].split('-')[1])
        number = len(list(range(from_profile - 1, to_profile)))
    else:
        number = int(config['settings']['number'])
    if len(proxies) != number:
        print('Количество профилей и прокси должно совпадать')
        input()
        return

    if '-' in config['settings']['number']:
        from_profile = int(config['settings']['number'].split('-')[0])
        to_profile = int(config['settings']['number'].split('-')[1])
        batches = range(from_profile - 1, to_profile)
    else:
        batches = range(int(config['settings']['number']))

    batches = [batches[i:i + 60] for i in range(0, len(batches), 60)]

    for batch in batches:
        print(f'Создаём {len(batch)} профилей')
        for profile in batch:
            create_profile(profile + 1, config['settings']['tag'], proxies[proxy_index])
            proxy_index += 1
        if batches.index(batch) != len(batches) - 1:
            print('Спим 60 секунд (ограничения octobrowser)')
            sleep(60)

    print('\nПрофили созданы')
    input()


if __name__ == '__main__':
    main()