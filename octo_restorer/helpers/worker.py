from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from entities import Wallet
from random import sample
from string import ascii_letters, digits
from time import sleep
from sys import exc_info
from helpers import octobrowser

def safe_click(driver, element):
    driver.execute_script("arguments[0].click();", element)

def safe_send_keys(driver, element, text):
    driver.execute_script(
        """
        const [element, value] = arguments;
        const lastValue = element.value;
        element.value = value;
        const event = new Event('input', { bubbles: true });
        const tracker = element._valueTracker;
        if (tracker) {
            tracker.setValue(lastValue);
        }
        element.dispatchEvent(event);
        """,
        element,
        text
    )

def get_extensions(driver: webdriver.Chrome):
    try:
        driver.get('chrome://extensions/')
        script = '''ext_manager = document.getElementsByTagName('extensions-manager')[0].shadowRoot;
        item_list = ext_manager.getElementById('items-list').shadowRoot;
        container = item_list.getElementById('container');
        extension_list = container.getElementsByClassName('items-container')[1].getElementsByTagName('extensions-item');
        var extensions = {};
        for (i = 0; i < extension_list.length; i++) {
            name = extension_list[i].shadowRoot.getElementById('name').textContent.trim();
            id = extension_list[i].id;
            extensions[name] = id;
        }
        return extensions;'''
        return driver.execute_script(script)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't get extensions list: exception at {exc_tb.tb_lineno}: {e}")

def get_metamask_status(driver: webdriver.Chrome, metamask_id):
    driver.get(f'chrome-extension://{metamask_id}/home.html')
    try:
        WebDriverWait(driver, 10).until(
            ec.url_changes(f'chrome-extension://{metamask_id}/home.html')
        )
    except TimeoutException:
        driver.get('about:blank')
        return 'unlocked'
    current_url = driver.current_url
    if 'unlock' in current_url:
        return 'locked'
    elif 'onboarding' in current_url:
        return 'new'
    else:
        raise Exception("Can't receive metamask state")

def import_metamask(driver: webdriver.Chrome, wallet: Wallet, password, metamask_id):
    try:
        driver.get(f'chrome-extension://{metamask_id}/home.html#onboarding/welcome')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="onboarding-terms-checkbox"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-import-wallet"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="metametrics-no-thanks"]'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="import-srp__srp-word-0"]'))
        )

        seed = wallet.seed_phrase.split(' ')
        seed_length = len(seed)
        if seed_length not in (12, 15, 18, 21, 24):
            raise Exception("Wrong seed length")

        if seed_length != 12:
            element = WebDriverWait(driver, 15).until(
                ec.presence_of_element_located((By.XPATH,
                    '//*[@id="app-content"]/div/div[2]/div/div/div/div[4]/div/div/div[2]/select'))
            ); safe_click(driver, element)
            sleep(1)
            element = WebDriverWait(driver, 15).until(
                ec.presence_of_element_located((By.XPATH,
                    f'//*[@id="app-content"]/div/div[2]/div/div/div/div[4]/div/div/div[2]/select/option[{(12,15,18,21,24).index(seed_length)+1}]'))
            ); safe_click(driver, element)

        for i in range(seed_length):
            element = driver.find_element(
                By.XPATH,
                f'//input[@data-testid="import-srp__srp-word-{i}"]'
            )
            safe_send_keys(driver, element, seed[i])

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="import-srp-confirm"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-new"]'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-confirm"]'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//input[@data-testid="create-password-terms"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="create-password-import"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="onboarding-complete-done"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="pin-extension-next"]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, '//button[@data-testid="pin-extension-done"]'))
        ); safe_click(driver, element)

        try:
            WebDriverWait(driver, 3).until(
                ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]'))
            )
            WebDriverWait(driver, 60).until_not(
                ec.presence_of_element_located((By.XPATH, '//div[@class="mm-box loading-overlay"]'))
            )
            sleep(3)
        except:
            pass

        driver.get('about:blank')
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't import metamask: exception at {exc_tb.tb_lineno}")

def restore_metamask(driver: webdriver.Chrome, wallet: Wallet, password, metamask_id):
    try:
        driver.get(f'chrome-extension://{metamask_id}/home.html#onboarding/unlock')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//a[@class="button btn-link unlock-page__link"]'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//input[@data-testid="import-srp__srp-word-0"]'))
        )

        seed = wallet.seed_phrase.split(' ')
        for i in range(12):
            element = driver.find_element(
                By.XPATH,
                f'//input[@data-testid="import-srp__srp-word-{i}"]'
            )
            safe_send_keys(driver, element, seed[i])

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//input[@data-testid="create-vault-password"]'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//input[@data-testid="create-vault-confirm-password"]'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//button[@data-testid="create-new-vault-submit-button"]'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 60).until(
            ec.url_changes(driver.current_url)
        )

        try:
            WebDriverWait(driver, 3).until(
                ec.presence_of_element_located((By.XPATH,
                    '//div[@class="mm-box loading-overlay"]'))
            )
            WebDriverWait(driver, 60).until_not(
                ec.presence_of_element_located((By.XPATH,
                    '//div[@class="mm-box loading-overlay"]'))
            )
            sleep(3)
        except:
            pass

        driver.get('about:blank')
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't restore metamask: exception at {exc_tb.tb_lineno} ({e})")

def get_phantom_status(driver: webdriver.Chrome, phantom_id):
    driver.get(f'chrome-extension://{phantom_id}/popup.html')
    window = driver.current_window_handle
    try:
        WebDriverWait(driver, 5).until(lambda d: window not in driver.window_handles)
    except TimeoutException:
        return 'imported'
    else:
        sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        return 'new'

def import_phantom(driver: webdriver.Chrome, wallet: Wallet, password, phantom_id):
    try:
        while True:
            driver.get(f'chrome-extension://{phantom_id}/onboarding.html')

            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//*[@id="root"]/main/div[2]/div/div[2]/button[2]'))
            ); safe_click(driver, element)
            sleep(0.5)
            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//*[@id="root"]/main/div[2]/div/div[2]/button[2]'))
            ); safe_click(driver, element)

            WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//input[@data-testid="secret-recovery-phrase-word-input-0"]'))
            )

            seed = wallet.seed_phrase.split(' ')
            for i in range(12):
                element = driver.find_element(
                    By.XPATH,
                    f'//input[@data-testid="secret-recovery-phrase-word-input-{i}"]'
                )
                safe_send_keys(driver, element, seed[i])

            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//button[@data-testid="onboarding-form-submit-button"]'))
            ); safe_click(driver, element)
            sleep(0.5)

            try:
                element = WebDriverWait(driver, 60).until(
                    ec.element_to_be_clickable((By.XPATH,
                        '//button[@data-testid="onboarding-form-submit-button"]'))
                ); safe_click(driver, element)
            except TimeoutException:
                status = get_phantom_status(driver, phantom_id)
                if status == 'new':
                    continue
                else:
                    driver.get('about:blank')
                    sleep(3)
                    return

            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//input[@data-testid="onboarding-form-password-input"]'))
            ); safe_send_keys(driver, element, password)
            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//input[@data-testid="onboarding-form-confirm-password-input"]'))
            ); safe_send_keys(driver, element, password)

            element = WebDriverWait(driver, 15).until(
                ec.presence_of_element_located((By.XPATH,
                    '//input[@data-testid="onboarding-form-terms-of-service-checkbox"]'))
            ); safe_click(driver, element)

            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//button[@data-testid="onboarding-form-submit-button"]'))
            ); safe_click(driver, element)
            sleep(0.5)

            before = driver.current_window_handle
            driver.switch_to.new_window()
            new = driver.current_window_handle
            driver.switch_to.window(before)
            sleep(0.5)

            element = WebDriverWait(driver, 60).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//button[@data-testid="onboarding-form-submit-button"]'))
            ); safe_click(driver, element)

            driver.switch_to.window(new)
            driver.get('about:blank')
            sleep(3)
            return
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't import phantom: exception at {exc_tb.tb_lineno} ({e})")

def restore_phantom(driver: webdriver.Chrome, wallet: Wallet, password, phantom_id):
    try:
        attempts = 0
        while True:
            driver.get(f'chrome-extension://{phantom_id}/onboarding.html?restore=true')
            try:
                driver.minimize_window(); sleep(1); driver.maximize_window()
                element = WebDriverWait(driver, 30).until(
                    ec.element_to_be_clickable((By.XPATH,
                        '//input[@data-testid="secret-recovery-phrase-word-input-0"]'))
                )
            except:
                attempts += 1
                if attempts == 3:
                    raise Exception("Can't import phantom. Error on load.")
                driver.get('about:blank'); sleep(1)
                continue

            seed = wallet.seed_phrase.split(' ')
            for i in range(12):
                element = driver.find_element(
                    By.XPATH,
                    f'//input[@data-testid="secret-recovery-phrase-word-input-{i}"]'
                )
                safe_send_keys(driver, element, seed[i])

            element = WebDriverWait(driver, 15).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//button[@data-testid="onboarding-form-submit-button"]'))
            ); safe_click(driver, element)
            sleep(0.5)

            try:
                element = WebDriverWait(driver, 60).until(
                    ec.element_to_be_clickable((By.XPATH,
                        '//button[@data-testid="onboarding-form-submit-button"]'))
                ); safe_click(driver, element)
            except TimeoutException:
                continue

            before = driver.current_window_handle
            driver.switch_to.new_window()
            new = driver.current_window_handle
            driver.switch_to.window(before)
            sleep(0.5)

            element = WebDriverWait(driver, 60).until(
                ec.element_to_be_clickable((By.XPATH,
                    '//button[@data-testid="onboarding-form-submit-button"]'))
            ); safe_click(driver, element)

            driver.switch_to.window(new)
            driver.get('about:blank')
            sleep(3)
            return
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't restore phantom: exception at {exc_tb.tb_lineno} ({e})")

def get_keplr_status(driver: webdriver.Chrome, keplr_id):
    driver.get(f'chrome-extension://{keplr_id}/popup.html')
    window = driver.current_window_handle
    try:
        WebDriverWait(driver, 5).until(lambda d: window not in driver.window_handles)
    except TimeoutException:
        return 'imported'
    else:
        driver.switch_to.window(driver.window_handles[0])
        return 'new'

def import_keplr(driver: webdriver.Chrome, wallet: Wallet, password, keplr_id):
    try:
        driver.get(f'chrome-extension://{keplr_id}/register.html')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div/div/div/div[3]/div[3]/button'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[2]/div/div/div/div[1]/div/div[5]/button'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[3]/div/div/div[1]/div[1]/div[2]/div[2]/div/div/input'))
        )
        sleep(1)

        seed = wallet.seed_phrase.split(' ')
        for i in range(12):
            element = driver.find_element(
                By.XPATH,
                f'//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[3]/div/div/div[1]/div[{i+1}]/div[2]/div[2]/div/div/input'
            )
            safe_send_keys(driver, element, seed[i])

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[3]/div/div/form/div[6]/div/button'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 60).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[1]/div[2]/div/div/input'))
        )
        sleep(1)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[1]/div[2]/div/div/input'))
        ); safe_send_keys(driver, element, 'Wallet')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[3]/div[2]/div/div/input'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[5]/div[2]/div/div/input'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div[4]/div/div/form/div/div[7]/button'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 60).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div/div/div/div/div/div[10]/div/button'))
        ); safe_click(driver, element)

        before = driver.current_window_handle
        driver.switch_to.new_window()
        new_window = driver.current_window_handle
        driver.get('about:blank')
        driver.switch_to.window(before)

        while True:
            try:
                element = WebDriverWait(driver, 5).until(
                    ec.element_to_be_clickable((By.XPATH,
                        '//*[@id="app"]/div/div[2]/div/div/div/div/div/div/div[7]/div/button'))
                ); safe_click(driver, element); sleep(0.5)
            except:
                break

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="app"]/div/div[2]/div[5]/div[1]/button'))
        ); safe_click(driver, element)

        driver.switch_to.window(new_window)
        sleep(3)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't import keplr: exception at {exc_tb.tb_lineno} ({e})")

def close_all_tabs(driver: webdriver.Chrome):
    try:
        try:
            WebDriverWait(driver, 15).until_not(ec.number_of_windows_to_be(1))
            sleep(10)
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
        raise Exception(f"Can't close tabs: {type(e)} at {exc_tb.tb_lineno}")

def import_backpack(driver: webdriver.Chrome, wallet: Wallet, password, backpack_id):
    driver.get(f'chrome-extension://{backpack_id}/onboarding.html')

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div/div[1]/div/div/button/div/div[1]'))
    ); safe_click(driver, element)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div/div[3]'))
    ); safe_click(driver, element)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/span/div/div/div/div/div[2]/div[3]'))
    ); safe_click(driver, element)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[3]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[2]/div[2]'))
    ); safe_click(driver, element)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[4]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/span/div/div/div/div/div[2]/div/span/textarea'))
    ); safe_send_keys(driver, element, wallet.seed_phrase)
    sleep(2)

    element = WebDriverWait(driver, 15).until(
        ec.presence_of_element_located((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[4]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div'))
    ); safe_click(driver, element)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[5]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/span/div/div/div/div/div[2]/div/span/input'))
    ); safe_send_keys(driver, element, password)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[5]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/span/div/div/div/div/div[3]/div/span/input'))
    ); safe_send_keys(driver, element, password)

    element = WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[5]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div'))
    ); safe_click(driver, element)

    WebDriverWait(driver, 15).until(
        ec.element_to_be_clickable((By.XPATH,
            '//*[@id="onboarding"]/div/div/span[1]/div[1]/div[2]/div/div/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/div/div/div[1]/div/div/div/div/div[1]/div'))
    )

    driver.get('about:blank')
    sleep(3)

def get_sui_status(driver: webdriver.Chrome, sui_id):
    driver.get(f'chrome-extension://{sui_id}/index.html')
    WebDriverWait(driver, 15).until(
        ec.url_changes(f'chrome-extension://{sui_id}/index.html')
    )
    url = driver.current_url
    if 'Home/Tokens' in url:
        return 'imported'
    else:
        return 'new'

def import_sui(driver: webdriver.Chrome, wallet: Wallet, password, sui_id):
    try:
        driver.get(f'chrome-extension://{sui_id}/index.html')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div/div[2]/div[3]/button[2]'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[1]'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[1]/div/div/div/input'))
        )

        seed = wallet.seed_phrase.split(' ')
        for i in range(12):
            element = driver.find_element(
                By.XPATH,
                f'//*[@id="root"]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[{i+1}]/div/div/div/input'
            )
            safe_send_keys(driver, element, seed[i])

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[2]/button'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[3]/div[2]/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[1]/div/div/div/input'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[3]/div[2]/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div/div/div/input'))
        ); safe_send_keys(driver, element, password)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[3]/div[2]/div/div/div[2]/div/div/div/div/div[2]/button'))
        ); safe_click(driver, element)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '//*[@id="root"]/div/div/div/div/div[2]/div/div[2]/div/div[4]/div[2]/div/div/div[2]/div/div/div/div/div[3]/button'))
        ); safe_click(driver, element)

        WebDriverWait(driver, 15).until(ec.url_contains('Home/Tokens'))
        driver.get('about:blank')
        sleep(3)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't import sui: exception at {exc_tb.tb_lineno} ({e})")

def restore_sui(driver: webdriver.Chrome, wallet: Wallet, password, sui_id):
    try:
        driver.get(f'chrome-extension://{sui_id}/index.html')

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '/html/body/div[6]/div/div[2]/div/div/div/div/div/div[2]/div[2]/button[2]'))
        ); safe_click(driver, element)

        before = driver.current_window_handle
        driver.switch_to.new_window()
        after = driver.current_window_handle
        driver.switch_to.window(before)

        element = WebDriverWait(driver, 15).until(
            ec.element_to_be_clickable((By.XPATH,
                '/html/body/div[6]/div/div[2]/div/div/div/div/div/div/div[3]/button'))
        ); safe_click(driver, element)

        driver.switch_to.window(after)
        import_sui(driver, wallet, password, sui_id)
    except Exception as e:
        exc_type, exc_value, exc_tb = exc_info()
        raise Exception(f"Can't restore sui: exception at {exc_tb.tb_lineno} ({e})")

def worker(uuid, wallet: Wallet, bar, password, do_metamask, do_keplr, do_phantom, do_backpack, do_sui, errors, profile_index):
    try:
        ws = octobrowser.run_profile(uuid)
        options = Options()
        options.add_experimental_option("enableExtensionTargets", True)
        options.add_experimental_option("debuggerAddress", f'127.0.0.1:{ws}')
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(options=options)

        try:
            driver.maximize_window()
        except:
            pass

        close_all_tabs(driver)

        if do_metamask:
            metamask_id = get_extensions(driver).get('ZavodMetaMask')
            if not metamask_id:
                raise Exception("Can't find metamask id")
            password = password or ''.join(sample(ascii_letters + digits, 15))
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
                raise Exception("Can't find keplr id")
            password = password or ''.join(sample(ascii_letters + digits, 15))
            keplr_state = get_keplr_status(driver, keplr_id)
            if keplr_state == 'new':
                import_keplr(driver, wallet, password, keplr_id)
            else:
                raise Exception('Вход в Keplr уже выполнен, необходимо переустановить расширение')

        if do_phantom:
            phantom_id = get_extensions(driver).get("ZavodPhantom")
            if not phantom_id:
                raise Exception("Can't find phantom id")
            password = password or ''.join(sample(ascii_letters + digits, 15))
            phantom_state = get_phantom_status(driver, phantom_id)
            if phantom_state == 'new':
                import_phantom(driver, wallet, password, phantom_id)
            else:
                restore_phantom(driver, wallet, password, phantom_id)

        if do_backpack:
            backpack_id = get_extensions(driver).get("ZavodBackpack")
            if not backpack_id:
                raise Exception("Can't find backpack id")
            password = password or ''.join(sample(ascii_letters + digits, 15))
            import_backpack(driver, wallet, password, backpack_id)

        if do_sui:
            sui_id = get_extensions(driver).get("ZavodSuiWallet")
            if not sui_id:
                raise Exception("Can't find Sui Wallet id")
            password = password or ''.join(sample(ascii_letters + digits, 15))
            sui_state = get_sui_status(driver, sui_id)
            if sui_state == 'new':
                import_sui(driver, wallet, password, sui_id)
            else:
                restore_sui(driver, wallet, password, sui_id)

        octobrowser.close_profile(uuid)
    except Exception as e:
        errors.append(profile_index)
        exc_type, exc_value, exc_tb = exc_info()
        print(f'Unknown error: at {exc_tb.tb_lineno}: {str(e)}')
    finally:
        octobrowser.close_profile(uuid)
        bar.next()
