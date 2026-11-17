import ctypes
import locale

TRANSLATIONS = {
    "ru": {
        # Главный виджет (main.py)
        "loading": "Загрузка...",
        "offline": "Нет сети",
        "copied": "Скопировано!",
        "copied_ipv6": "IPv6 скопирован!",

        # Карточка при наведении (hover_card.py)
        "unknown": "Неизвестно",
        "ping_ms": "{ms} мс",
        "hover_isp": "Провайдер: {isp}",
        "hover_iface": "Интерфейс: {iface}",
        "hover_ping": "Пинг: {ping}",
        "hover_tz": "Часовой пояс: {tz}",
        "hover_privacy": "🔒 Приватный режим (IP скрыт до наведения)",

        # Трей и уведомления (tray.py)
        "tray_detecting": "Определение IP...",
        "tray_hide": "Скрыть виджет",
        "tray_show": "Показать виджет",
        "tray_refresh": "Обновить сейчас",
        "tray_copy_ip": "Копировать IP",
        "tray_copy_ipv6": "Копировать IPv6",
        "tray_settings": "Настройки...",
        "tray_exit": "Выход",
        "notify_ip_title": "{app}: сменился адрес",
        "notify_ip_body": "Новое подключение: {loc}\nIP: {ip}",
        "notify_upd_title": "{app}: доступно обновление v{ver}",
        "notify_upd_body": "Нажмите на уведомление или откройте Настройки, чтобы обновиться.",

        # Окно настроек (settings_ui.py)
        "settings_title": "{app} — Настройки",
        "settings_language": "Язык интерфейса:",
        "lang_auto": "Авто (система)",
        "lang_ru": "Русский",
        "lang_en": "English",
        "settings_opacity": "Прозрачность окна:",
        "settings_scale": "Масштаб виджета:",
        "settings_pos": "Позиция отображения:",
        "pos_bottom_right": "Снизу справа",
        "pos_bottom_left": "Снизу слева",
        "pos_top_right": "Сверху справа",
        "pos_top_left": "Сверху слева",
        "pos_custom": "Произвольная (Alt / СКМ)",
        "settings_theme": "Тема оформления:",
        "theme_system": "Системная (Windows)",
        "theme_dark": "Тёмная",
        "theme_light": "Светлая",
        "settings_interval": "Период проверки (сек):",
        "cb_mask_ip": "Скрывать IP до наведения курсора (приватность)",
        "cb_idle_pause": "Пауза опросов при простое более 5 мин (AFK)",
        "cb_on_top": "Отображать поверх других окон\n(автоскрытие в полноэкранном режиме)",
        "cb_notify": "Уведомлять при смене IP или страны",
        "cb_autostart": "Запускать вместе с Windows",
        "upd_progress": "Загрузка обновления: %p%",
        "btn_check_upd": "Проверить обновления",
        "btn_checking": "Проверка...",
        "btn_cancel": "Отмена",
        "btn_save": "Сохранить",
        "author_prefix": "© Иван Черкез",

        # Диалоги обновлений (settings_ui.py, updater.py)
        "upd_dlg_title": "{app} — Обновления",
        "upd_check_err": "Не удалось проверить обновления.\nПроверьте подключение к интернету.\n\nДетали: {error}",
        "upd_up_to_date": "У вас установлена актуальная версия (v{ver}).",
        "upd_avail_title": "{app} — Доступно обновление",
        "upd_avail_header": "Доступна новая версия {app} v{new_ver} (текущая: v{cur_ver}).",
        "upd_whats_new": "Что нового:\n{notes}",
        "upd_ask_install": "Скачать и установить обновление сейчас?",
        "upd_dl_err_title": "{app} — Ошибка загрузки",
        "upd_dl_err_body": "Не удалось скачать обновление:\n{error}",
        "upd_info_title": "{app} — Обновление",
        "upd_dev_saved": "Запущена dev-версия (.py). Новый бинарник сохранён как:\n{dest}",
        "upd_save_err": "Не удалось сохранить файл: {error}",
        "upd_bat_err": "Ошибка запуска установщика: {error}",
    },
    "en": {
        # Main widget
        "loading": "Loading...",
        "offline": "Offline",
        "copied": "Copied!",
        "copied_ipv6": "IPv6 copied!",

        # Hover card
        "unknown": "Unknown",
        "ping_ms": "{ms} ms",
        "hover_isp": "ISP: {isp}",
        "hover_iface": "Interface: {iface}",
        "hover_ping": "Ping: {ping}",
        "hover_tz": "Timezone: {tz}",
        "hover_privacy": "🔒 Privacy mode (IP hidden until hover)",

        # Tray & notifications
        "tray_detecting": "Detecting IP...",
        "tray_hide": "Hide widget",
        "tray_show": "Show widget",
        "tray_refresh": "Refresh now",
        "tray_copy_ip": "Copy IP",
        "tray_copy_ipv6": "Copy IPv6",
        "tray_settings": "Settings...",
        "tray_exit": "Exit",
        "notify_ip_title": "{app}: IP address changed",
        "notify_ip_body": "New connection: {loc}\nIP: {ip}",
        "notify_upd_title": "{app}: update v{ver} available",
        "notify_upd_body": "Click this notification or open Settings to update.",

        # Settings dialog
        "settings_title": "{app} — Settings",
        "settings_language": "Language:",
        "lang_auto": "Auto (System)",
        "lang_ru": "Русский",
        "lang_en": "English",
        "settings_opacity": "Window opacity:",
        "settings_scale": "Widget scale:",
        "settings_pos": "Screen position:",
        "pos_bottom_right": "Bottom right",
        "pos_bottom_left": "Bottom left",
        "pos_top_right": "Top right",
        "pos_top_left": "Top left",
        "pos_custom": "Custom (Alt / MMB)",
        "settings_theme": "Theme:",
        "theme_system": "System (Windows)",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "settings_interval": "Poll interval (sec):",
        "cb_mask_ip": "Mask IP until cursor hover (privacy)",
        "cb_idle_pause": "Pause polling when idle over 5 min (AFK)",
        "cb_on_top": "Always on top\n(auto-hide in fullscreen apps)",
        "cb_notify": "Notify when IP or country changes",
        "cb_autostart": "Start with Windows",
        "upd_progress": "Downloading update: %p%",
        "btn_check_upd": "Check for updates",
        "btn_checking": "Checking...",
        "btn_cancel": "Cancel",
        "btn_save": "Save",
        "author_prefix": "© Ivan Cherkez",

        # Update dialogs
        "upd_dlg_title": "{app} — Updates",
        "upd_check_err": "Failed to check for updates.\nPlease check your internet connection.\n\nDetails: {error}",
        "upd_up_to_date": "You have the latest version installed (v{ver}).",
        "upd_avail_title": "{app} — Update Available",
        "upd_avail_header": "A new version {app} v{new_ver} is available (current: v{cur_ver}).",
        "upd_whats_new": "What's new:\n{notes}",
        "upd_ask_install": "Download and install the update now?",
        "upd_dl_err_title": "{app} — Download Error",
        "upd_dl_err_body": "Failed to download update:\n{error}",
        "upd_info_title": "{app} — Update",
        "upd_dev_saved": "Running dev version (.py). New binary saved as:\n{dest}",
        "upd_save_err": "Failed to save file: {error}",
        "upd_bat_err": "Failed to launch installer: {error}",
    },
}

_current_lang = "en"


def get_system_language() -> str:
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        lang_code = locale.windows_locale.get(lang_id, "")
        if lang_code.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


def set_language(lang_pref: str) -> str:
    global _current_lang
    if lang_pref in TRANSLATIONS:
        _current_lang = lang_pref
    else:
        _current_lang = get_system_language()
    return _current_lang


def t(key: str, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text