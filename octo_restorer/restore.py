from configparser import ConfigParser
import colorama
from colorama import Fore
from threading import Thread
from time import sleep
from progress.bar import Bar
from typing import List, Tuple

from entities import Config, Error, Wallet


# --------------------------------------------------------------------------------
#                                   НАСТРОЙКИ
# --------------------------------------------------------------------------------
cfg_parser = ConfigParser()
cfg_parser.read('config.ini')
config_obj = Config(**cfg_parser['settings'])

from helpers import reader, octobrowser, chunks, worker

# --------------------------------------------------------------------------------
#                       ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# --------------------------------------------------------------------------------
def init_exit() -> None:
    """Ждёт нажатия Enter и завершает программу."""
    input('\nPress Enter to close the program...')
    exit()


def ask_yes_no(question: str) -> bool:
    """Возвращает True/False в зависимости от ответа пользователя (y/n)."""
    while True:
        ans = input(f"{question} (y/n): ").strip().lower()
        if ans in ('y', 'yes'):
            return True
        if ans in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'.")


def ask_for_profiles() -> List[int]:
    """
    Спрашивает, какие профили перезапустить.
    'all' → [] (значит «все»), иначе строку «1, 12, 46» → [1, 12, 46].
    """
    while True:
        answer = input("Enter profiles (e.g. 'all' or '1, 12, 46'): ").strip().lower()
        if answer == 'all':
            return []
        try:
            return list(map(int, answer.split(',')))
        except ValueError:
            print("Некорректный ввод. Пример: 1, 12, 46 или all.")


def ask_for_new_do_params(cfg: Config) -> None:
    """Позволяет переопределить do_* флаги без перезапуска скрипта."""
    print("Введите 0 или 1, чтобы изменить флаги do_* (Enter — оставить как есть).")
    cfg.do_metamask  = int(input(f"do_metamask  (сейчас {cfg.do_metamask}):  ") or cfg.do_metamask)
    cfg.do_keplr     = int(input(f"do_keplr     (сейчас {cfg.do_keplr}):     ") or cfg.do_keplr)
    cfg.do_phantom   = int(input(f"do_phantom   (сейчас {cfg.do_phantom}):   ") or cfg.do_phantom)
    cfg.do_backpack  = int(input(f"do_backpack  (сейчас {cfg.do_backpack}):  ") or cfg.do_backpack)
    cfg.do_sui       = int(input(f"do_sui       (сейчас {cfg.do_sui}):       ") or cfg.do_sui)


# --------------------------------------------------------------------------------
#                        ОСНОВНЫЕ ОПЕРАЦИИ С ПРОФИЛЯМИ
# --------------------------------------------------------------------------------
def launch_profiles(uuid_list: List[str]):
    """
    Запускает профили в OctoBrowser.
    При первой же ошибке возвращает Error.
    """
    bar = Bar('Launching', max=len(uuid_list))
    bar.start()

    ws_list = []
    for uuid in uuid_list:
        result = octobrowser.run_profile(uuid)            # заглушка
        if isinstance(result, Error):
            bar.finish()
            return result
        ws_list.append(result)
        bar.next()
        sleep(3)

    bar.finish()
    return ws_list


def setup_profiles(
        profile_data: List[Tuple[str, str]],       # [(uuid, title), …]
        wallet_list: List[Wallet],
        cfg: Config
    ):
    """
    Настраивает профили (MetaMask, Keplr, Phantom и т.д.).
    - profile_data: список кортежей (uuid, title), где title — «родной» номер профиля.
      Это гарантирует верные номера в отчётах об ошибках даже при повторных запусках.
    - wallet_list: соответствующие кошельки.
    """
    # Делаем список [(uuid, title, wallet), …] и режем на чанки.
    triples = list(zip(profile_data, wallet_list))        # [((uuid, title), wallet), …]
    triple_chunks = chunks(triples, cfg.thread_number)

    bar = Bar('Configuring', max=len(profile_data))
    bar.start()

    errors: List[Error] = []

    for group in triple_chunks:
        threads: List[Thread] = []

        for ((uuid, title_for_profile), wallet) in group:
            t = Thread(
                target=worker,
                args=(
                    uuid,
                    wallet,
                    bar,
                    cfg.metamask_password,
                    cfg.do_metamask,
                    cfg.do_keplr,
                    cfg.do_phantom,
                    cfg.do_backpack,
                    cfg.do_sui,
                    errors,
                    title_for_profile          # теперь это настоящий номер, а не вычисленный индекс
                )
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

    bar.finish()
    return errors


# --------------------------------------------------------------------------------
#                    ПОЛУЧЕНИЕ И ФИЛЬТРАЦИЯ ДАННЫХ
# --------------------------------------------------------------------------------
def get_and_check_wallets():
    wallet_list = reader.read_wallets()           # заглушка
    return wallet_list


def get_and_check_profiles():
    profiles = octobrowser.get_profiles()         # заглушка
    return profiles


def filter_profiles_and_wallets(cfg: Config, profiles_full, wallets_full):
    """
    Возвращает отфильтрованные (profiles, wallets) в соответствии с config.ini.
    profiles_full — результат get_profiles(): [{'uuid': ..., 'title': ...}, …]
    """
    if len(profiles_full) != len(wallets_full):
        return Error('Wallet reading error',
                     'The number of wallets does not equal the number of profiles in the tag')

    # Явно перечисленные номера профилей
    if cfg.profiles:
        res_p, res_w = [], []
        for target_title in cfg.profiles:
            for idx, p in enumerate(profiles_full):
                if p['title'] == str(target_title):
                    res_p.append(p)
                    res_w.append(wallets_full[idx])
                    break
            else:
                return Error('Getting profiles error', f'Could not find profile {target_title}')
        return res_p, res_w

    # Диапазон от first_profile
    first_idx = next(
        (i for i, p in enumerate(profiles_full) if p['title'] == str(cfg.first_profile)),
        None
    )
    if first_idx is None:
        return Error('Getting profiles error',
                     f'Couldn\'t find profile {cfg.first_profile}')

    slice_p = profiles_full[first_idx:first_idx + cfg.profiles_number]
    slice_w = wallets_full[first_idx:first_idx + cfg.profiles_number]

    if len(slice_p) != cfg.profiles_number:
        return Error('Getting profiles error',
                     'Wrong first_profile and profiles_number')

    return slice_p, slice_w


def select_profiles_by_titles(titles: List[int], profiles_full, wallets_full):
    """
    При повторном запуске:
    - titles == []  → вернуть все профили
    - иначе вернуть только те, чьи 'title' ∈ titles
    """
    if not titles:
        return profiles_full, wallets_full

    res_p, res_w = [], []
    for t in titles:
        for idx, p in enumerate(profiles_full):
            if p['title'] == str(t):
                res_p.append(p)
                res_w.append(wallets_full[idx])
                break
        else:
            return Error('Getting profiles error', f'Could not find profile {t}')
    return res_p, res_w


# --------------------------------------------------------------------------------
#                                    MAIN
# --------------------------------------------------------------------------------
def main():
    colorama.init()

    # 1. Кошельки
    wallets_full = get_and_check_wallets()
    if isinstance(wallets_full, Error):
        print(wallets_full)
        init_exit()

    # 2. Профили
    profiles_full = get_and_check_profiles()
    if isinstance(profiles_full, Error):
        print(profiles_full)
        init_exit()

    # 3. Фильтруем согласно config.ini
    filtered = filter_profiles_and_wallets(config_obj, profiles_full, wallets_full)
    if isinstance(filtered, Error):
        print(filtered)
        init_exit()

    profiles_filtered, wallets_filtered = filtered
    print('Pre-launch verification completed.\n')

    # 4. Готовим данные для setup_profiles()
    profiles_data = [(p['uuid'], p['title']) for p in profiles_filtered]

    # 5. Первый запуск
    errors = setup_profiles(profiles_data, wallets_filtered, config_obj)
    errors = list(map(str, errors))

    print(f'\n{Fore.GREEN}All profiles are ready! Check for errors on them.{Fore.RESET}')
    if errors:
        print(f'\nThere were some errors on: {", ".join(errors)}')

    # 6. Повторные запуски
    while ask_yes_no("Do you want to rerun the script on some/all profiles?"):
        titles_to_rerun = ask_for_profiles()          # [] или список номеров
        ask_for_new_do_params(config_obj)

        selection = select_profiles_by_titles(
            titles=titles_to_rerun,
            profiles_full=profiles_full,
            wallets_full=wallets_full
        )
        if isinstance(selection, Error):
            print(selection)
            continue

        sel_profiles, sel_wallets = selection
        sel_data = [(p['uuid'], p['title']) for p in sel_profiles]

        errors = setup_profiles(sel_data, sel_wallets, config_obj)
        errors = list(map(str, errors))

        print(f'\n{Fore.GREEN}Rerun completed! Check for errors.{Fore.RESET}')
        if errors:
            print(f'\nThere were errors on: {", ".join(errors)}')

    print("No more reruns requested.")
    init_exit()


if __name__ == '__main__':
    main()
