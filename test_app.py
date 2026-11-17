import os
import sys
import unittest
from unittest.mock import patch

# Запускаем Qt в режиме без вывода окон на экран, если возможно
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

import i18n
from config import DEFAULT_CONFIG, APP_VERSION
from network import iso2_to_iso3, normalize_city, _parse_response
from positioning import mask_ip_address
from updater import parse_version
from hover_card import HoverCard
from settings_ui import SettingsDialog
from tray import WidgetTray


class TestLocalization(unittest.TestCase):
    def test_ru_and_en_keys_match(self):
        """Проверяем, что наборы ключей в RU и EN полностью совпадают."""
        ru_keys = set(i18n.TRANSLATIONS["ru"].keys())
        en_keys = set(i18n.TRANSLATIONS["en"].keys())

        missing_in_en = ru_keys - en_keys
        missing_in_ru = en_keys - ru_keys

        self.assertEqual(missing_in_en, set(), f"В EN не хватает ключей: {missing_in_en}")
        self.assertEqual(missing_in_ru, set(), f"В RU не хватает ключей: {missing_in_ru}")

    def test_no_empty_translations(self):
        """Проверяем, что ни одна строка перевода не пустая."""
        for lang, entries in i18n.TRANSLATIONS.items():
            for key, val in entries.items():
                self.assertTrue(isinstance(val, str) and len(val.strip()) > 0, f"Пустой перевод: {lang}.{key}")

    def test_all_placeholders_format_cleanly(self):
        """Проверяем, что все шаблоны с {переменными} подставляются без KeyError."""
        sample_kwargs = {
            "ms": 42,
            "isp": "Test ISP",
            "iface": "Ethernet (192.168.1.2)",
            "ping": "42 ms",
            "tz": "Europe/Moscow",
            "app": "IPWidget",
            "loc": "RUS, Moscow",
            "ip": "1.2.3.4",
            "ver": "0.6.0",
            "new_ver": "0.7.0",
            "cur_ver": "0.6.0",
            "notes": "Bug fixes",
            "error": "Timeout",
            "dest": "C:\\IPWidget_latest.exe",
        }
        for lang in ("ru", "en"):
            i18n.set_language(lang)
            for key in i18n.TRANSLATIONS[lang]:
                result = i18n.t(key, **sample_kwargs)
                self.assertNotIn("{", result, f"Неподставленная переменная в {lang}.{key}: {result}")


class TestCoreLogic(unittest.TestCase):
    def test_ip_masking(self):
        """Проверяем маскировку IPv4 и IPv6."""
        self.assertEqual(mask_ip_address("192.168.10.55"), "192.168.•••.•••")
        self.assertEqual(mask_ip_address("2a00:1450:4001:81b::200e"), "2a00:1450:••••:••••")
        self.assertEqual(mask_ip_address(""), "")

    def test_country_and_city_helpers(self):
        """Проверяем конвертацию кодов стран и исправление названий городов."""
        self.assertEqual(iso2_to_iso3("ru"), "RUS")
        self.assertEqual(iso2_to_iso3("US"), "USA")
        self.assertEqual(iso2_to_iso3(""), "UNK")
        self.assertEqual(normalize_city("Krasnogvardeiskii"), "Saint Petersburg")

    def test_api_response_parsing(self):
        """Проверяем разбор ответов от разных IP-сервисов."""
        ipwho_sample = {
            "ip": "8.8.8.8",
            "country_code": "US",
            "city": "Mountain View",
            "connection": {"isp": "Google LLC"},
            "timezone": {"id": "America/Los_Angeles"},
        }
        self.assertEqual(
            _parse_response(ipwho_sample),
            ("8.8.8.8", "US", "Mountain View", "Google LLC", "America/Los_Angeles")
        )

        failed_sample = {"status": "fail", "message": "reserved range"}
        self.assertEqual(_parse_response(failed_sample), ("", "", "", "", ""))

    def test_version_comparison(self):
        """Проверяем сравнение версий для автообновления."""
        self.assertTrue(parse_version("v0.6.1") > parse_version("0.6.0"))
        self.assertTrue(parse_version("0.10.0") > parse_version("0.6.0"))
        self.assertFalse(parse_version("v0.6.0") > parse_version(APP_VERSION))


class TestUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_ui_renders_in_both_languages(self):
        """Проверяем создание окна настроек, трея и карточки наведения на RU и EN."""
        for lang in ("ru", "en"):
            i18n.set_language(lang)
            cfg = DEFAULT_CONFIG.copy()
            cfg["language"] = lang

            card = HoverCard()
            card.update_content("Cloudflare", 25, "UTC", is_light=False, is_private=True, iface="Wi-Fi", ipv6="2606:4700::1111")
            self.assertIn("Cloudflare", card.isp_label.text())
            card.close()

            with patch("settings_ui.get_autostart_enabled", return_value=False):
                dlg = SettingsDialog(cfg)
                self.assertIn("IPWidget", dlg.windowTitle())
                dlg.close()

            tray = WidgetTray()
            tray.retranslate_ui(visible=True, has_ip=False)
            tray.update_status("1.1.1.1", "AUS, Sydney", "2606:4700::1111")
            tray.hide()


if __name__ == "__main__":
    unittest.main(verbosity=2)