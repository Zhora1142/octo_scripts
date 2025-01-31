from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.devtools.v85.fetch import continue_request
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from entities import Error
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from entities import Wallet
from random import sample
from string import ascii_letters, digits
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager
from sys import exc_info
from helpers import octobrowser


def get_extensions(driver: webdriver.Chrome):
    try:
        driver.get('chrome://extensions/')

        script = '''ext_manager = document.getElementsByTagName('extensions-manager')[0].shadowRoot;
        item_list = ext_manager.getElementById('items-list').shadowRoot;
        container = item_list.getElementById('container');
        extension_list = container.getElementsByClassName('items-container')[1].getElementsByTagName('extensions-item');

        var extensions = {};

        for (i = 0; i < extension_list.length; i++) {
            console.log(extension_list[i]);
            name = extension_list[i].shadowRoot.getElementById('name').textContent.trim();
            id = extension_list[i].id;
            extensions[name] = id;
        }

        return extensions;'''

        return driver.execute_script(script)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t get extensions list: exception at {exc_tb.tb_lineno}: {e}')


def get_metamask_status(driver: webdriver.Chrome, metamask_id):
    driver.get(f'chrome-extension://{metamask_id}/home.html')

    try:
        WebDriverWait(driver, 10).until(ec.url_changes(f'chrome-extension://{metamask_id}/home.html'))
    except TimeoutException:
        driver.get('about:blank')
        return 'unlocked'

    current_url = driver.current_url

    if 'unlock' in current_url:
        return 'locked'
    elif 'onboarding' in current_url:
        return 'new'
    else:
        raise Exception('Can\'t receive metamask state')


def import_metamask(driver: webdriver.Chrome, wallet: Wallet, password, metamask_id):
    try:
        driver.get(f'chrome-extension://{metamask_id}/home.html#onboarding/welcome')

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-terms-checkbox"]'))).click()
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-import-wallet"]'))).click()

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="metametrics-no-thanks"]'))).click()

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="import-srp__srp-word-0"]')))

        seed = wallet.seed_phrase.split(' ')

        for i in range(12):
            driver.find_element(By.XPATH, f'//input[@data-testid="import-srp__srp-word-{i}"]').send_keys(seed[i])

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="import-srp-confirm"]'))).click()

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-new"]'))).send_keys(password)
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-confirm"]'))).send_keys(password)
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-terms"]'))).click()
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="create-password-import"]'))).click()

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-complete-done"]'))).click()
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="pin-extension-next"]'))).click()
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="pin-extension-done"]'))).click()

        try:
            WebDriverWait(driver, 3).until(ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]')))
            WebDriverWait(driver, 60).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]')))
            sleep(3)
        except:
            pass

        driver.get('about:blank')
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t import metamask: exception at {exc_tb.tb_lineno}')


def restore_metamask(driver: webdriver.Chrome, wallet: Wallet, password, metamask_id):
    try:
        driver.get(f'chrome-extension://{metamask_id}/home.html#onboarding/unlock')

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//a[@class="button btn-link unlock-page__link"]'))).click()

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="import-srp__srp-word-0"]')))

        seed = wallet.seed_phrase.split(' ')

        for i in range(12):
            driver.find_element(By.XPATH, f'//input[@data-testid="import-srp__srp-word-{i}"]').send_keys(seed[i])

        url_before = driver.current_url

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-vault-password"]'))).send_keys(password)
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-vault-confirm-password"]'))).send_keys(
            password)
        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="create-new-vault-submit-button"]'))).click()

        WebDriverWait(driver, 60).until(ec.url_changes(url_before))

        try:
            WebDriverWait(driver, 3).until(ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]')))
            WebDriverWait(driver, 60).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]')))
            sleep(3)
        except:
            pass

        driver.get('about:blank')
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t restore metamask: exception at {exc_tb.tb_lineno} ({e})')


def get_phantom_status(driver: webdriver.Chrome, phantom_id):
    driver.get(f'chrome-extension://{phantom_id}/popup.html')

    window = driver.current_window_handle

    try:
        WebDriverWait(driver, 5).until(
            lambda d: window not in driver.window_handles
        )
    except TimeoutException:
        return 'imported'
    else:
        driver.switch_to.window(driver.window_handles[0])
        return 'new'


def import_phantom(driver: webdriver.Chrome, wallet: Wallet, password, phantom_id):
    try:
        while 1:
            driver.get(f'chrome-extension://{phantom_id}/onboarding.html')

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="root"]/main/div[2]/div/div[2]/button[2]'))).click()
            sleep(0.5)
            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="root"]/main/div[2]/div/div[2]/button[2]'))).click()

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="secret-recovery-phrase-word-input-0"]')))

            seed = wallet.seed_phrase.split(' ')

            for i in range(12):
                driver.find_element(By.XPATH, f'//input[@data-testid="secret-recovery-phrase-word-input-{i}"]').send_keys(seed[i])

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()
            sleep(0.5)
            WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-form-password-input"]'))).send_keys(password)
            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-form-confirm-password-input"]'))).send_keys(password)

            WebDriverWait(driver, 15).until(ec.presence_of_element_located((By.XPATH, '//input[@data-testid="onboarding-form-terms-of-service-checkbox"]'))).click()
            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()
            sleep(0.5)

            try:
                WebDriverWait(driver, 30).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]')))
            except TimeoutException:
                status = get_phantom_status(driver, phantom_id)
                if status == 'new':
                    continue
                else:
                    driver.get('about:blank')
                    sleep(3)
                    return
            else:
                break

        before = driver.current_window_handle
        driver.switch_to.new_window()
        new = driver.current_window_handle
        driver.switch_to.window(before)
        sleep(0.5)
        WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()
        driver.switch_to.window(new)
        driver.get('about:blank')

        sleep(3)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t import phantom: exception at {exc_tb.tb_lineno} ({e})')


def restore_phantom(driver: webdriver.Chrome, wallet: Wallet, password, phantom_id):
    try:
        attempts = 0
        while 1:
            driver.get(f'chrome-extension://{phantom_id}/onboarding.html?restore=true')

            try:
                WebDriverWait(driver, 30).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="secret-recovery-phrase-word-input-0"]')))
            except:
                attempts += 1
                if attempts == 3:
                    raise Exception('Can\'t import phantom. Error on load.')
                driver.get('about:blank')
                sleep(1)
                continue

            seed = wallet.seed_phrase.split(' ')

            for i in range(12):
                driver.find_element(By.XPATH, f'//input[@data-testid="secret-recovery-phrase-word-input-{i}"]').send_keys(seed[i])

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()
            sleep(0.5)
            WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-form-password-input"]'))).send_keys(password)
            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-form-confirm-password-input"]'))).send_keys(password)

            WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()

            try:
                WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]')))
            except TimeoutException:
                continue
            else:
                break

        before = driver.current_window_handle
        driver.switch_to.new_window()
        new = driver.current_window_handle
        driver.switch_to.window(before)
        sleep(0.5)
        WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-form-submit-button"]'))).click()
        driver.switch_to.window(new)
        driver.get('about:blank')

        sleep(3)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t import phantom: exception at {exc_tb.tb_lineno} ({e})')


def get_keplr_status(driver: webdriver.Chrome, keplr_id):
    driver.get(f'chrome-extension://{keplr_id}/popup.html')

    window = driver.current_window_handle

    try:
        WebDriverWait(driver, 5).until(
            lambda d: window not in driver.window_handles
        )
    except TimeoutException:
        return 'imported'
    else:
        driver.switch_to.window(driver.window_handles[0])
        return 'new'


def import_keplr(driver: webdriver.Chrome, wallet: Wallet, password, keplr_id):
    try:
        driver.get(f'chrome-extension://{keplr_id}/register.html')

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div/div/div/div[3]/div[3]/button'))).click()
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[2]/div/div/div/div[1]/div/div[5]/button'))).click()

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[3]/div/div/div[1]/div[1]/div[2]/div[2]/div/div/input')))

        sleep(1)

        seed = wallet.seed_phrase.split(' ')

        for i in range(12):
            driver.find_element(By.XPATH, f'//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[3]/div/div/div[1]/div[{i + 1}]/div[2]/div[2]/div/div/input').send_keys(seed[i])

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[6]/div/button'))).click()

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[1]/div[2]/div/div/input')))

        sleep(1)

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[1]/div[2]/div/div/input'))).send_keys('Wallet')
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[3]/div[2]/div/div/input'))).send_keys(password)
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[5]/div[2]/div/div/input'))).send_keys(password)

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[7]/button'))).click()

        WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div/div/div/div/div[10]/div/button'))).click()

        before = driver.current_window_handle
        driver.switch_to.new_window()
        new_window = driver.current_window_handle
        driver.get('about:blank')
        driver.switch_to.window(before)

        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div[5]/div[1]/button'))).click()

        driver.switch_to.window(new_window)

        sleep(3)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t import keplr: exception at {exc_tb.tb_lineno} ({e})')


def close_all_tabs(driver: webdriver.Chrome, number):
    try:
        try:
            WebDriverWait(driver, 15).until(ec.number_of_windows_to_be(number + 1))
        except:
            pass

        windows = driver.window_handles
        for window in windows:
            driver.switch_to.window(window)
            if 'offscreen.html' in driver.current_url:
                driver.close()
        driver.switch_to.window(driver.window_handles[0])

        driver.switch_to.new_window()
        current = driver.current_window_handle
        windows = driver.window_handles
        windows.remove(current)

        for window in windows:
            driver.switch_to.window(window)
            driver.close()

        driver.switch_to.window(current)
        driver.get('about:blank')
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f'Can\'t close tabs: {type(e)} at {exc_tb.tb_lineno}')


def worker(uuid, wallet: Wallet, bar, password, version, do_metamask, do_keplr, do_phantom, repeat, errors, profile_index):
    try:
        ws = octobrowser.run_profile(uuid)
        options = Options()
        options.add_experimental_option("debuggerAddress", f'127.0.0.1:{ws}')
        options.page_load_strategy = 'eager'
        service = Service(executable_path=ChromeDriverManager(version).install())
        driver = webdriver.Chrome(options=options, service=service)

        try:
            driver.maximize_window()
        except:
            pass

        number = do_metamask + do_keplr + do_phantom

        close_all_tabs(driver, number)

        if do_metamask:
            metamask_id = get_extensions(driver).get('ZavodMetaMask')
            if not metamask_id:
                raise Exception('Can\'t find metamask id')

            password = password if password else ''.join(sample(ascii_letters + digits, 15))

            metamask_state = get_metamask_status(driver, metamask_id)

            if metamask_state == 'unlocked':
                driver.get('about:blank')
                return
            elif metamask_state == 'locked':
                restore_metamask(driver, wallet, password, metamask_id)
            elif metamask_state == 'new':
                import_metamask(driver, wallet, password, metamask_id)

        if do_keplr:
            keplr_id = get_extensions(driver).get('ZavodKeplr')
            if not keplr_id:
                raise Exception('Can\'t find keplr id')

            password = password if password else ''.join(sample(ascii_letters + digits, 15))

            keplr_state = get_keplr_status(driver, keplr_id)

            if keplr_state == 'new':
                import_keplr(driver, wallet, password, keplr_id)
            else:
                raise Exception('Вход в Keplr уже выполнен, необходимо переустановить расширение')

        if do_phantom:
            phantom_id = get_extensions(driver).get("ZavodPhantom")
            if not phantom_id:
                raise Exception('Can\'t find phantom id')

            password = password if password else ''.join(sample(ascii_letters + digits, 15))

            phantom_state = get_keplr_status(driver, phantom_id)

            if phantom_state == 'new':
                import_phantom(driver, wallet, password, phantom_id)
            else:
                restore_phantom(driver, wallet, password, phantom_id)

        octobrowser.close_profile(uuid)

        if repeat:
            while 1:
                ws = octobrowser.run_profile(uuid)
                if not ws or isinstance(ws, Error):
                    continue
                options = Options()
                options.add_experimental_option("debuggerAddress", f'127.0.0.1:{ws}')
                service = Service(executable_path=ChromeDriverManager(version).install())
                driver = webdriver.Chrome(options=options, service=service)

                f = False

                if do_metamask:
                    metamask_state = get_metamask_status(driver, metamask_id)

                    if metamask_state != 'locked':
                        import_metamask(driver, wallet, password, metamask_id)
                        f = True

                if do_keplr:
                    keplr_state = get_keplr_status(driver, keplr_id)

                    if keplr_state != 'imported':
                        import_metamask(driver, wallet, password, metamask_id)
                        f = True

                if do_phantom:
                    phantom_state = get_phantom_status(driver, phantom_id)

                    if phantom_state != 'imported':
                        import_phantom(driver, wallet, password, phantom_id)
                        f = True

                if f:
                    octobrowser.close_profile(uuid)
                    continue

                driver.get('about:blank')
                break
    except Exception as e:
        errors.append(profile_index)
        print(e)
    finally:
        octobrowser.close_profile(uuid)
        bar.next()
