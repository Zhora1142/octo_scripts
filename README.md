# Octo Scripts

Набор Python-скриптов для автоматизации работы с [OctoBrowser](https://app.octobrowser.net/). Включает три утилиты:

1. **Change Proxy** — массовая смена прокси для существующих профилей.
2. **Octo Creator** — создание новых профилей с заданными прокси и настройками хранилища.
3. **Octo Restorer** — восстановление кошельков (MetaMask, Keplr, Phantom, Backpack, Sui) в профилях через локальный API OctoBrowser и Selenium.

---

## 🛠️ Общие требования

- **Python 3.7+**  
- `pip install --upgrade pip`
- Базовые библиотеки (во всех модулях):  
  ```bash
  pip install configparser requests colorama
  ```

---

## 🔄 1. Change Proxy

Массовая смена прокси для уже существующих профилей с указанным тегом.

### Подготовка

1. Перейдите в папку `change_proxy/`.
2. Откройте `config.ini` и заполните поля:
   ```ini
   [settings]
   token                = <ВАШ_API_TOKEN_OCTOBROWSER>
   tag                  = <ТЕГ_ПРОФИЛЕЙ>
   proxy_type           = socks5        # или http, https
   requests_per_minute  = 30            # лимит запросов в минуту
   requests_per_hour    = 1000          # лимит запросов в час
   ```
3. В файле `proxy.txt` укажите список прокси (по одной записи на строку) в формате:
   ```
   хост:порт:логин:пароль
   ```

### Установка зависимостей

```bash
pip install requests colorama
```

### Запуск

```bash
python change.py
```

Скрипт:
- Получит все профили с заданным тегом.
- Проверит, что число прокси совпадает с числом профилей.
- Поочерёдно сменит прокси в каждом профиле через API OctoBrowser.
- При достижении лимитов будет приостанавливать работу (throttling).

---

## ➕ 2. Octo Creator

Создание новых профилей с тегом, прокси и опциями хранения.

### Подготовка

1. Перейдите в папку `octo_creator/`.
2. Откройте `config.ini` и пропишите:
   ```ini
   [settings]
   token        = <ВАШ_API_TOKEN_OCTOBROWSER>
   number       = 1-50        # диапазон или одно число — сколько профилей создать
   tag          = <ТЕГ_ПРОФИЛЕЙ>
   storage      = 1           # 1 — включить все опции хранения (cookies, history, bookmarks…)
   proxy_type   = socks5      # или http, https
   ```
3. В `proxy.txt` перечислите столько прокси, сколько профилей будет создано, в формате:
   ```
   хост:порт:логин:пароль
   ```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск

```bash
python create_profiles.py
```

Скрипт:
- Считает количество профилей (`number`) и сравнит с количеством строк в `proxy.txt`.
- Разобьёт создание на батчи по 200 профилей (ограничение API).
- Между батчами будет пауза 60 секунд.
- Создаст профили с указанным тегом, прокси и (опционально) хранением данных.

---

## 🔄 3. Octo Restorer

Восстановление кошельков в профилях OctoBrowser (MetaMask, Keplr, Phantom, Backpack, Sui).

### Подготовка

1. Перейдите в папку `octo_restorer/`.
2. Откройте `config.ini` и пропишите:
   ```ini
   [settings]
   api_token         = <ВАШ_API_TOKEN_OCTOBROWSER>
   tag_name          = <ТЕГ_ПРОФИЛЕЙ>          # те же профили, что вы создавали/использовали
   profiles  		     = 1-10,12                 # если нужно запустить конкретные профили (иначе пустое)
   first_profile     = 1                       # номер первого профиля в OctoBrowser
   profiles_number   = 10                      # сколько профилей восстановить
   metamask_file     = metamask.txt            # файл со мнемословами
   metamask_password = <ПАРОЛЬ_МЕТАМАСК>       # используется в UI расширения
   thread_number     = 2                       # сколько параллельных потоков
   do_metamask       = 1                       # 1/0 — восстанавливать MetaMask
   do_keplr          = 0                       # 1/0 — восстанавливать Keplr
   do_phantom        = 0                       # …
   do_backpack       = 0
   do_sui            = 0
   ```
3. Файл `metamask.txt`: мнемоники кошельков, по одному на строку:
   ```
   seed phrase wallet #1
   seed phrase wallet #2
   …
   ```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск

```bash
python restore.py
```

Скрипт:
1. Считает список seed-фраз.
2. Получит профили через API OctoBrowser по тегу.
3. Отфильтрует диапазон профилей `[first_profile, first_profile+profiles_number)`.
4. Запустит каждый профиль локально.
5. Параллельно (по `thread_number` потоков) вставит в расширения кошельки в указанном порядке.
6. После завершения предложит при необходимости повторно прогнуть скрипт по выбору профилей.

---

## 📝 Советы и рекомендации

- **API Token** берите в личном кабинете OctoBrowser (секция интеграций).
- При массовых операциях сначала протестируйте на 1–2 профилях с небольшим количеством прокси/кошельков.
