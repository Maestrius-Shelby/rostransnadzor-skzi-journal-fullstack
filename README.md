# 🚀 Парсер Ространснадзор

> Автоматический сбор данных из личного кабинета
> Поддержка Windows и Linux (altLinux, Ubuntu, Debian)  
> Fullstack: Python + FastAPI + React SPA

---

## 📋 Требования

### Backend
| Компонент | Минимальная версия |
|-----------|-------------------|
| Python | 3.12+ |
| Браузер | Яндекс Браузер (Windows) / Chromium (Linux) |
| ОЗУ | 4 GB (рекомендуется) |
| Дисковое пространство | 500 MB |

### Frontend
| Компонент | Минимальная версия |
|-----------|-------------------|
| Node.js | 20.0+ |
| npm | 10.0+ |

---

## 📁 Структура проекта

<details>
<summary><b>Развернуть полную структуру проекта</b></summary>

```text

📦 rostransnadzor-parser/
│
├── 📂 backend/ # ⚙️ Backend (Python + FastAPI)
│ │
│ ├── ⚙️ .env # Реальные переменные окружения (секреты, в репозиторий не попадает)
│ ├── ⚙️ .env.example # Шаблон переменных окружения (без значений)
│ ├── 🐍 .python-version # Версия Python для менеджера pyenv
│ │
│ ├── 📂 assets/ # 🖼️ Графические шаблоны для распознавания элементов интерфейса
│ │ ├── 🖼️ ok_button.png # Эталонное изображение кнопки «ОК» в окне CAdES
│ │ ├── 🖼️ select_button.png # Эталонное изображение кнопки «Выбрать» для выбора сертификата
│ │ └── 📄 Thumbs.db # Служебный файл Windows (кэш миниатюр, можно игнорировать)
│ │
│ ├── 📂 chromedriver-linux64/ # 🌐 ChromeDriver для Linux
│ │ └── 📂 chromedriver-linux64/
│ │ ├── 🔧 chromedriver # Исполняемый файл драйвера
│ │ ├── 📜 LICENSE.chromedriver # Лицензия ChromeDriver
│ │ └── 📜 THIRD_PARTY_NOTICES.chromedriver # Сторонние компоненты ChromeDriver
│ │
│ ├── 📂 chromedriver-win64/ # 🌐 ChromeDriver для Windows
│ │ ├── 🔧 chromedriver.exe # Исполняемый файл драйвера
│ │ ├── 📜 LICENSE.chromedriver # Лицензия ChromeDriver
│ │ └── 📜 THIRD_PARTY_NOTICES.chromedriver # Сторонние компоненты ChromeDriver
│ │
│ ├── 📂 data/ # 🗄️ Файлы состояния приложения и конфигурации (JSON)
│ │ ├── 🏁 .excel_updated # Флаг-файл: временная метка последнего обновления Excel
│ │ ├── 👤 admin.json # Хеш пароля администратора веб-интерфейса (bcrypt)
│ │ ├── 📜 history.json # История запусков парсера: дата, время, количество записей
│ │ └── 🔑 tokens.json # Массив токенов доступа к личному кабинету (base64url-строки)
│ │
│ ├── 🔐 hash_password.py # Утилита генерации bcrypt-хеша пароля администратора
│ │
│ ├── 📂 linux/ # 🐧 Вспомогательные скрипты для развёртывания на Linux
│ │ ├── 📦 install_dependencies.sh # Установка системных зависимостей (пакетов ОС)
│ │ └── 🔧 setup_chromedriver.sh # Загрузка и настройка ChromeDriver под Linux
│ │
│ ├── 🐧 main_linux.py # Точка входа для запуска на Linux
│ ├── 🪟 main_windows.py # Точка входа для запуска на Windows
│ │
│ ├── 📂 output/ # 📤 Результаты парсинга (создаётся автоматически)
│ │ ├── 📊 Журнал_СКЗИ.json # Спарсенные данные в JSON
│ │ └── 📊 Журнал_СКЗИ.xlsx # Спарсенные данные в формате Excel (целевой журнал)
│ │
│ ├── 📝 parser_15D(undecomposed).py # Черновая версия парсера (недекомпозированная, 15 дней)
│ ├── 📝 parser_all(undecomposed).py # Черновая версия парсера (недекомпозированная, полный период)
│ │
│ ├── ⚙️ pyproject.toml # Метаданные Python-проекта (для пакетных менеджеров uv/pip)
│ ├── 📦 requirements.txt # Список Python-зависимостей
│ │
│ ├── 📂 src/ # 💻 Основной исходный код backend
│ │ │
│ │ ├── 📂 api/ # 🚀 FastAPI-приложение
│ │ │ ├── 🚀 main.py # Точка входа FastAPI: создание приложения, монтирование роутов
│ │ │ ├── 📂 models/
│ │ │ │ ├── 📋 schemas.py # Pydantic-схемы для валидации запросов и ответов
│ │ │ │ └── 📄 init.py
│ │ │ ├── 📂 routes/
│ │ │ │ ├── 🔐 auth.py # Эндпоинты аутентификации (логин, проверка сессии)
│ │ │ │ ├── 📜 history.py # Эндпоинты истории запусков парсера
│ │ │ │ ├── ▶️ parser.py # Эндпоинты управления парсером (запуск, остановка)
│ │ │ │ ├── 📋 records.py # Эндпоинты доступа к записям журнала СКЗИ
│ │ │ │ ├── ⚙️ settings.py # Эндпоинты управления настройками парсера
│ │ │ │ ├── 👁️ watcher.py # Эндпоинты для WebSocket-уведомлений об изменениях Excel
│ │ │ │ └── 📄 init.py
│ │ │ ├── 📂 services/
│ │ │ │ ├── 🗄️ data_manager.py # Сервис управления данными: загрузка/сохранение JSON и Excel
│ │ │ │ ├── 🔄 parser_service.py # Сервис-обёртка над ядром парсера для вызова из API
│ │ │ │ ├── 📂 excel_watcher/ # 👁️ Подсистема отслеживания изменений Excel-файла
│ │ │ │ │ ├── 📊 excel_handler.py # Обработчик операций с Excel (чтение, запись, парсинг)
│ │ │ │ │ ├── ▶️ run_watcher.py # Точка запуска наблюдателя
│ │ │ │ │ ├── 🟢 status_calculator.py # Расчёт статусов сертификатов (действует / истекает / истёк)
│ │ │ │ │ ├── 👁️ watcher.py # Наблюдатель файловой системы (отслеживает изменения Excel)
│ │ │ │ │ ├── 🔌 websocket_server.py # WebSocket-сервер для уведомления фронтенда
│ │ │ │ │ └── 📄 init.py
│ │ │ │ ├── 📄 init.py
│ │ │ │ └── 📁 pycache/
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 core/ # 🧠 Ядро парсера
│ │ │ ├── 🌐 browser_manager.py # Управление экземпляром браузера (Selenium WebDriver)
│ │ │ ├── ⚙️ config.py # Загрузка и валидация конфигурации из .env
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 data/
│ │ │ └── 📋 records.json # Кэш спарсенных записей (промежуточное хранение)
│ │ │
│ │ ├── 📂 export/ # 📤 Модуль экспорта данных
│ │ │ ├── 📊 excel_exporter.py # Формирование файла Журнал_СКЗИ.xlsx
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 navigation/ # 🖱️ Навигация и взаимодействие с элементами страницы
│ │ │ ├── 🖱️ click_actions.py # Функции кликов, ожидания элементов, обработки диалогов
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 parsing/ # 🔍 Модуль парсинга данных
│ │ │ ├── 🔍 data_parser.py # Извлечение и структурирование данных из HTML-таблиц
│ │ │ ├── 📜 scroll_manager.py # Управление прокруткой страницы для загрузки всех строк
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 recognition/ # 👁️ Модуль распознавания изображений
│ │ │ ├── 👁️ image_recognizer.py # Поиск элементов по эталонным изображениям (OpenCV)
│ │ │ ├── 📐 template_manager.py # Управление шаблонами (загрузка, предобработка)
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📂 rostransnadzor_parser.egg-info/ # 📦 Метаданные пакета (генерируется автоматически)
│ │ │ ├── 📄 dependency_links.txt
│ │ │ ├── 📄 entry_points.txt
│ │ │ ├── 📄 PKG-INFO
│ │ │ ├── 📄 requires.txt
│ │ │ ├── 📄 SOURCES.txt
│ │ │ └── 📄 top_level.txt
│ │ │
│ │ ├── 📂 utils/ # 🛠️ Вспомогательные утилиты
│ │ │ ├── ❌ exceptions.py # Пользовательские классы исключений
│ │ │ ├── 📝 logger.py # Настройка логирования
│ │ │ ├── 📂 path_utils.py # Утилиты для работы с путями (кросс-платформенные)
│ │ │ ├── 📄 init.py
│ │ │ └── 📁 pycache/
│ │ │
│ │ ├── 📄 init.py
│ │ └── 📁 pycache/
│ │
│ ├── 📂 tests/ # 🧪 Модульные тесты
│ │ ├── ✅ test_check_excel.py # Тесты сверки Excel с исходными данными
│ │ ├── ✅ test_parser.py # Тесты логики парсинга
│ │ ├── ✅ test_recognizer.py # Тесты модуля распознавания изображений
│ │ ├── ✅ test_server.py # Тесты API-сервера
│ │ └── 📄 init.py
│ │
│ └── 📁 pycache/
│
├── 📂 frontend/ # 🎨 Frontend (React SPA)
│ │
│ ├── ⚙️ .env # Реальные переменные окружения (URL API и т.п.)
│ ├── ⚙️ .env.example # Шаблон переменных окружения для frontend
│ │
│ ├── 📂 dist/ # 📦 Собранная production-версия (результат npm run build)
│ │ ├── 📂 assets/
│ │ │ ├── 📦 index-DOYMz_9C.js # Бандл JavaScript (минифицированный, с хешем)
│ │ │ └── 🎨 index-Oro1N9Jm.css # Бандл стилей (минифицированный, с хешем)
│ │ ├── 🖼️ favicon.svg # Иконка сайта
│ │ ├── 🎨 icons.svg # Спрайт иконок
│ │ └── 🌐 index.html # Точка входа SPA
│ │
│ ├── ✅ eslint.config.js # Конфигурация ESLint
│ ├── 🌐 index.html # HTML-шаблон для разработки
│ ├── 🔧 install_nvm.sh # Скрипт установки nvm на Linux-сервере
│ ├── 🔒 package-lock.json # Зафиксированные версии npm-зависимостей
│ ├── 📦 package.json # Метаданные и зависимости frontend-проекта
│ │
│ ├── 📂 public/ # 🖼️ Статические файлы (копируются в dist/ при сборке)
│ │ ├── 🖼️ favicon.svg
│ │ └── 🎨 icons.svg
│ │
│ ├── 📂 src/ # 💻 Исходный код React-приложения
│ │ │
│ │ ├── 📂 api/ # 🔌 Модуль взаимодействия с backend API
│ │ │ ├── 🔌 apiServices.js # Функции-обёртки над конкретными эндпоинтами
│ │ │ ├── ⚙️ axiosInstance.js # Настройка экземпляра Axios (baseURL, перехватчики)
│ │ │ └── 📄 index.js # Реэкспорт API-функций
│ │ │
│ │ ├── ⚛️ App.jsx # Корневой компонент приложения
│ │ ├── 🎨 App.module.scss # Стили корневого компонента
│ │ ├── 🧭 AppRouter.jsx # Настройка маршрутов (React Router v6)
│ │ │
│ │ ├── 📂 assets/ # 🖼️ Статические ресурсы, импортируемые в компонентах
│ │ │ ├── ⚛️ react.svg
│ │ │ └── ⚡ vite.svg
│ │ │
│ │ ├── 📂 components/ # 🧩 React-компоненты
│ │ │ │
│ │ │ ├── 📂 AuthProvider/ # 🔐 Провайдер аутентификации (контекст)
│ │ │ │ └── 🔐 AuthProvider.jsx
│ │ │ │
│ │ │ ├── 📂 features/ # 🎯 Бизнес-компоненты (осмысленные блоки интерфейса)
│ │ │ │ ├── 📂 Dashboard/ # 📊 Дашборд: сводка, статусы сертификатов
│ │ │ │ │ ├── 📊 Dashboard.jsx
│ │ │ │ │ └── 🎨 Dashboard.module.scss
│ │ │ │ ├── 📂 DataTable/ # 📋 Таблица с данными журнала СКЗИ
│ │ │ │ │ ├── 📋 DataTable.jsx
│ │ │ │ │ └── 🎨 DataTable.module.scss
│ │ │ │ ├── 📄 index.js # Реэкспорт всех бизнес-компонентов
│ │ │ │ ├── 📂 Login/ # 🔑 Страница входа в веб-интерфейс
│ │ │ │ │ ├── 🔑 Login.jsx
│ │ │ │ │ └── 🎨 Login.module.scss
│ │ │ │ ├── 📂 Logs/ # 📝 Компонент отображения логов работы парсера
│ │ │ │ │ ├── 📝 Logs.jsx
│ │ │ │ │ └── 🎨 Logs.module.scss
│ │ │ │ ├── 📂 ParserControl/ # 🕹️ Панель управления парсером (запуск / остановка)
│ │ │ │ │ ├── 🕹️ ParserControl.jsx
│ │ │ │ │ └── 🎨 ParserControl.module.scss
│ │ │ │ └── 📂 ParserHistory/ # 📜 История запусков парсера
│ │ │ │ ├── 📜 ParserHistory.jsx
│ │ │ │ └── 🎨 ParserHistory.module.scss
│ │ │ │
│ │ │ ├── 📂 layouts/ # 📐 Компоненты макета страницы
│ │ │ │ ├── 📂 Footer/ # 🦶 Подвал
│ │ │ │ │ ├── 🦶 Footer.jsx
│ │ │ │ │ └── 🎨 Footer.module.scss
│ │ │ │ ├── 📂 Header/ # 🧭 Шапка
│ │ │ │ │ ├── 🧭 Header.jsx
│ │ │ │ │ └── 🎨 Header.module.scss
│ │ │ │ ├── 📄 index.js # Реэкспорт компонентов макета
│ │ │ │ └── 📂 Layout/ # 🏗️ Корневой макет (Header + Content + Footer)
│ │ │ │ ├── 🏗️ Layout.jsx
│ │ │ │ └── 🎨 Layout.module.scss
│ │ │ │
│ │ │ ├── 📂 shared/ # 🔄 Общие (shared) компоненты
│ │ │ │ ├── 📂 ErrorBoundary/ # 🛡️ Предохранитель (отлов ошибок рендеринга)
│ │ │ │ │ └── 🛡️ ErrorBoundary.jsx
│ │ │ │ ├── 📄 index.js
│ │ │ │ ├── 📂 LoadingSpinner/ # ⏳ Индикатор загрузки
│ │ │ │ │ ├── ⏳ LoadingSpinner.jsx
│ │ │ │ │ └── 🎨 LoadingSpinner.module.scss
│ │ │ │ └── 📂 Notification/ # 🔔 Всплывающие уведомления
│ │ │ │ ├── 🔔 Notification.jsx
│ │ │ │ └── 🎨 Notification.module.scss
│ │ │ │
│ │ │ └── 📂 ui/ # 🧱 UI-кирпичики (атомарные переиспользуемые компоненты)
│ │ │ ├── 📂 Button/ # 🔘 Кнопка
│ │ │ │ ├── 🔘 Button.jsx
│ │ │ │ └── 🎨 Button.module.scss
│ │ │ ├── 📂 Card/ # 🃏 Карточка
│ │ │ │ ├── 🃏 Card.jsx
│ │ │ │ └── 🎨 Card.module.scss
│ │ │ ├── 📂 ConfirmDialog/ # ❓ Диалог подтверждения действия
│ │ │ │ ├── ❓ ConfirmDialog.jsx
│ │ │ │ └── 🎨 ConfirmDialog.module.scss
│ │ │ ├── 📄 index.js
│ │ │ ├── 📂 Input/ # ⌨️ Поле ввода
│ │ │ │ ├── ⌨️ Input.jsx
│ │ │ │ └── 🎨 Input.module.scss
│ │ │ ├── 📂 Modal/ # 🪟 Модальное окно
│ │ │ │ ├── 🪟 Modal.jsx
│ │ │ │ └── 🎨 Modal.module.scss
│ │ │ └── 📂 SearchInput/ # 🔍 Поисковая строка
│ │ │ ├── 🔍 SearchInput.jsx
│ │ │ └── 🎨 SearchInput.module.scss
│ │ │
│ │ ├── 📂 hooks/ # 🪝 Кастомные React-хуки
│ │ │ ├── 📄 index.js
│ │ │ ├── 🪝 useParser.js # Хук для взаимодействия с API парсера
│ │ │ └── 🔌 useWebSocket.js # Хук для WebSocket-соединения (обновления в реальном времени)
│ │ │
│ │ ├── ⚛️ main.jsx # Точка входа React-приложения
│ │ │
│ │ ├── 📂 pages/ # 📄 Компоненты страниц
│ │ │ ├── 📂 HomePage/ # 🏠 Домашняя страница
│ │ │ │ ├── 🏠 HomePage.jsx
│ │ │ │ └── 🎨 HomePage.module.scss
│ │ │ ├── 📄 index.js
│ │ │ └── 📂 ParserPage/ # 🕹️ Страница управления парсером
│ │ │ ├── 🕹️ ParserPage.jsx
│ │ │ └── 🎨 ParserPage.module.scss
│ │ │
│ │ ├── 📂 router/
│ │ │ └── 🧭 index.jsx # Конфигурация маршрутов приложения
│ │ │
│ │ ├── 📂 store/ # 🗃️ Хранилище состояния (Redux Toolkit)
│ │ │ ├── 🗃️ index.js # Конфигурация store
│ │ │ ├── 📂 selectors/
│ │ │ │ ├── 🔐 authSelectors.js # Селекторы состояния аутентификации
│ │ │ │ └── 📊 parserSelectors.js # Селекторы состояния парсера
│ │ │ └── 📂 slices/
│ │ │ ├── 🔐 authSlice.js # Срез состояния аутентификации
│ │ │ ├── 📊 parserSlice.js # Срез состояния парсера
│ │ │ ├── ⚙️ settingsSlice.js # Срез состояния настроек
│ │ │ └── 🎨 uiSlice.js # Срез состояния интерфейса (уведомления, модалки)
│ │ │
│ │ ├── 📂 styles/ # 🎨 Глобальные стили
│ │ │ ├── 🌍 global.scss # Глобальные сбросы и базовые стили
│ │ │ └── 🎨 variables.scss # SCSS-переменные (цвета, брейкпоинты)
│ │ │
│ │ └── 📂 utils/ # 🛠️ Вспомогательные утилиты frontend
│ │ ├── 📋 constants.js # Константы приложения
│ │ └── 🔧 helpers.js # Вспомогательные функции
│ │
│ └── ⚙️ vite.config.js # Конфигурация сборщика Vite
│
└── 📄 README.md # 📖 Документация проекта
```

</details>

---

## ⚙️ Конфигурационные файлы и безопасность

### Переменные окружения (`.env` и `.env.example`)

Чувствительные параметры (пути к драйверам, учётные данные, токены) **не хранятся в коде**.
Они вынесены в файлы `.env`, которые добавлены в `.gitignore` и **никогда не попадают в репозиторий**.

| Файл | Назначение |
| :--- | :--- |
| `backend/.env.example` | Шаблон переменных окружения для backend. Содержит ключи без значений. |
| `backend/.env` | Реальный конфигурационный файл. Создаётся вручную путём копирования `.env.example` и заполнения актуальными данными. |
| `frontend/.env.example` | Шаблон переменных окружения для frontend (URL API и т.п.). |
| `frontend/.env` | Реальный конфигурационный файл для frontend. |

**Порядок настройки:**
```bash
# Backend
cp backend/.env.example backend/.env
# → отредактировать backend/.env, вписав реальные значения

# Frontend
cp frontend/.env.example frontend/.env
# → отредактировать frontend/.env при необходимости
```

### Организация хранения конфигурационных данных и аутентификации пользователей

При разработке автоматизированной системы было принято решение отказаться от использования полноценной системы управления базами данных. Анализ требований показал, что для поставленной задачи отсутствует необходимость хранения большого объема взаимосвязанных данных, а количество пользователей системы ограничено сотрудниками отдела информационной безопасности.

В качестве механизма хранения служебной информации используются JSON-файлы, что позволило упростить архитектуру программного комплекса, исключить необходимость администрирования СУБД и сократить время развертывания приложения.

В системе используются следующие конфигурационные файлы.

#### Файл `admin.json`

Файл предназначен для хранения учетной записи администратора системы.

В нем содержатся:

- логин администратора;
- хэш пароля;
- дата создания учетной записи.

Хранение пароля осуществляется исключительно в виде криптографического хэша, что исключает возможность получения исходного пароля при компрометации файла.

#### Скрипт `hash_password.py`

Для формирования защищенного значения пароля разработан отдельный служебный скрипт `hash_password.py`.

Назначение скрипта:

- генерация криптографического хэша пользовательского пароля;
- исключение хранения паролей в открытом виде;
- подготовка значения для последующего сохранения в `admin.json`.

Использование отдельного скрипта позволяет создавать и изменять учетные данные администратора без внесения изменений в исходный код программного комплекса.

#### Файл `tokens.json`

Файл `tokens.json` предназначен для хранения перечня действующих токенов авторизации.

Каждый токен представляет собой случайно сгенерированную строку, используемую для проверки подлинности запросов пользователя к серверной части приложения.

При выполнении защищённых запросов сервер проверяет наличие переданного токена в файле `tokens.json`. Если токен присутствует в списке, запрос считается авторизованным; в противном случае доступ отклоняется.

Использование данного файла позволяет реализовать механизм авторизации пользователей без применения отдельной системы хранения сессий или базы данных.

### Обоснование отказа от использования СУБД

В разработанном программном комплексе не используется традиционная система управления базами данных (PostgreSQL, MySQL, SQLite и др.). Хранение состояния приложения, конфигурационных параметров и служебной информации реализовано посредством JSON-файлов.

Данное архитектурное решение обусловлено следующими причинами:

- **Простота развёртывания.** Отсутствует необходимость установки, настройки и администрирования отдельной системы управления базами данных.

- **Портируемость.** Все данные приложения представлены в виде самодостаточных файлов, которые могут быть легко перенесены на другое рабочее место или включены в резервную копию системы.

- **Достаточность.** Объём обрабатываемой информации (реестр сертификатов сотрудников одного территориального управления, настройки приложения, история запусков и результаты парсинга) не превышает нескольких тысяч записей, что полностью соответствует возможностям файлового хранения без снижения производительности.

- **Прозрачность хранения данных.** Формат JSON обладает простой и читаемой структурой, благодаря чему служебные данные могут быть просмотрены и, при необходимости, скорректированы без использования специализированных инструментов.

Таким образом, применение файлового хранения вместо традиционной СУБД позволило упростить архитектуру программного комплекса, уменьшить количество внешних зависимостей и обеспечить достаточную производительность при эксплуатации системы.

> **Примечание.** Файлы `admin.json`, `tokens.json`, а также файлы конфигурации `.env` содержат конфиденциальную служебную информацию (учётные данные, хэши паролей, токены доступа и параметры конфигурации). По этой причине они исключены из системы контроля версий с помощью файла `.gitignore` и не подлежат публикации в открытых репозиториях.

## 🚀 Установка и запуск

### Windows

#### Backend

<details>
<summary><b>📌 Установка и запуск Backend</b></summary>

```bash
# 1. Переход в папку проекта
cd C:\rostransnadzor-parser\backend

# 2. Удаление старого виртуального окружения (если есть)
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# 3. Создание виртуального окружения через uv с Python 3.12
uv venv --python 3.12

# 4. Активация виртуального окружения
.\.venv\Scripts\activate

# 5. Установка зависимостей через uv
uv pip install -r requirements.txt

# 6. Выбрать правильный интерпретатор
Ctrl+Shift+P → Python: Select Interpreter → Enter interpreter path...
C:\Users\Prakt5\Desktop\rostransnadzor-parser\backend\.venv\Scripts\python.exe

# 7. Запуск парсера
python main_windows.py
```

</details>

## 🐧 Linux (ALT Linux / Ubuntu / Debian)

### Backend

<details> <summary><b>📌 Установка и запуск Backend</b></summary>

```bash
# 1. Установка системных зависимостей
bash linux/install_dependencies.sh

# 2. Настройка ChromeDriver
bash linux/setup_chromedriver.sh

# 3. Создание виртуального окружения
python3 -m venv venv

# 4. Активация виртуального окружения
source .venv/bin/activate

# 5. Установка Python-зависимостей
pip install -r requirements.txt

# 6. Запуск парсера
python main_linux.py
```

</details>

<details>
<summary><b>🐛 Решение проблем с виртуальным окружением на Linux</b></summary>

### ❌ Ошибка: `cannot create venv: noexec`

Если при создании виртуального окружения возникает ошибка, связанная с `noexec` (запрет выполнения файлов в папке), следуйте инструкции ниже.

### 📋 Причина

На некоторых Linux-системах (особенно на серверах) папка `/tmp` или `/var/tmp` может быть смонтирована с опцией `noexec`, что запрещает запуск исполняемых файлов. Виртуальное окружение требует права на выполнение.

### ✅ Решение

```bash
# 1. Деактивировать текущее виртуальное окружение (если активно)
deactivate

# 2. Удалить старый venv
rm -rf .venv

# 3. Дать права на всю папку проекта
chmod -R 755 ~/rostransnadzor-parser

# 4. Создать venv заново
python3 -m venv .venv

# 5. Дать права на venv
chmod -R 755 .venv

# 6. Активировать виртуальное окружение
source .venv/bin/activate

# 7. Установить зависимости
python3 -m pip install -r requirements.txt

# Посмотреть, какие папки смонтированы без noexec
mount | grep -v noexec | grep ext4

# /dev/nvme0n1p2 on / type ext4 (rw,relatime) — корень / смонтирован без noexec! 
# Создайте venv там: если sudo нет — попробовать /var/tmp (обычно exec)
```

</details>

<details>
<summary><b>🔧 Настройка ChromeDriver для Linux</b></summary>

**ChromeDriver должен совпадать по версии с установленным браузером** (Яндекс Браузер, Chromium или Chrome). Несоответствие версий приведёт к ошибке `session not created`.

```bash
# 1. Узнать версию браузера
rpm -qa | grep -i "yandex\|chromium\|chrome"

# 2. Перейти в папку backend
cd /var/tmp/rostransnadzor-parser/backend

# 3. Создать папку для ChromeDriver
mkdir -p chromedriver-linux64

# 4. Скачать ChromeDriver нужной версии
# Пример для версии 139.0.7258.139 (подставьте свою)
wget "https://storage.googleapis.com/chrome-for-testing-public/139.0.7258.139/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip

# или вручную
https://www.chromedriverdownload.com/
https://googlechromelabs.github.io/

# 5. Распаковать архив
python3 -c "
import zipfile
with zipfile.ZipFile('/tmp/chromedriver.zip', 'r') as z:
    z.extractall('chromedriver-linux64/')
"

# 6. Дать права на выполнение
chmod +x chromedriver-linux64/chromedriver-linux64/chromedriver

# 7. Проверить версию
./chromedriver-linux64/chromedriver-linux64/chromedriver --version

```

</details>

#### Frontend

<details>
<summary><b>📌 Установка и запуск Frontend</b></summary>

```bash

# 1. Переход в папку frontend
cd frontend

# 2. Установка зависимостей
npm install

# 3. Разработка (запуск dev сервера)
npm run dev
# → http://localhost:5173

# 4. Проверка кода (ESLint)
npm run lint

# 5. Сборка для продакшена
npm run build
# → создает папку dist/ с оптимизированными файлами

# 6. Просмотр продакшен сборки
npm run preview
# → http://localhost:4173

```

</details>

<details>
<summary><b>🔧 Настройка Node.js через nvm на Linux</b></summary>

**Если на сервере установлена старая версия Node.js, её нужно обновить через nvm.**

```bash
# 1. Скачайте скрипт установки:
curl -o install_nvm.sh https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh

# или вручную
https://github.com/nvm-sh/nvm

# 2. Сделайте скрипт исполняемым:
chmod +x install_nvm.sh

# 3. Запустите скрипт:
./install_nvm.sh

# 4. Активируйте nvm в текущей сессии
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# 5. Проверить установку
nvm --version

# 6. Установите нужную версию Node.js (например, 24.18.0)
wget https://nodejs.org/dist/v24.18.0/node-v24.18.0-linux-x64.tar.xz -O /tmp/node24.tar.xz

# 7. Распакуйте Node.js в /var/tmp
tar -xf /tmp/node24.tar.xz -C /var/tmp/

# 8. Проверьте что работает
/var/tmp/node-v24.18.0-linux-x64/bin/node --version

# 9. Создайте ссылки в ~/bin и пропишите PATH, перезапустив оболочку
mkdir -p ~/bin
ln -sf /var/tmp/node-v24.18.0-linux-x64/bin/node ~/bin/node
ln -sf /var/tmp/node-v24.18.0-linux-x64/bin/npm ~/bin/npm
ln -sf /var/tmp/node-v24.18.0-linux-x64/bin/npx ~/bin/npx
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
exec bash

# 10. Проверьте версию
node --version

# 11. Перейдите в папку frontend и установите зависимости
cd /var/tmp/rostransnadzor-parser/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

```

</details>
