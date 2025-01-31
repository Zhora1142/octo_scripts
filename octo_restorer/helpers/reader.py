from entities import Wallet, Error
from restore import config_object


def read_wallets():
    try:
        filename = config_object.metamask_file

        with open(filename, encoding='utf-8') as file:
            seeds_raw = file.read().split('\n')
            if not seeds_raw[-1]:
                seeds_raw = seeds_raw[:-1]
            file.close()

        result = []

        for seed in seeds_raw:
            result.append(Wallet(seed))

        return result
    except Exception as e:
        return Error('Wallets reading error', 'Couldn\'t read wallets list from file', e)
