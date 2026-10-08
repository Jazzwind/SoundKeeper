"""Regression tests; no playback, registry writes, or real user config changes."""

import json
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import soundkeeper
from settings import Settings, load_settings, save_settings
from translations import TRANSLATIONS, resolve_language, translate


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "SoundKeeper" / "config.json"

    def test_round_trip_all_preferences(self):
        settings = Settings(wait_seconds=895, duration_seconds=0.01, language="ar")
        save_settings(self.path, settings)
        self.assertEqual(load_settings(self.path), settings)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_missing_corrupt_and_non_object_files_use_defaults(self):
        self.assertEqual(load_settings(self.path), Settings())
        self.path.parent.mkdir()
        for content in ("{broken", "[]", "null", '{"version": 2}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(load_settings(self.path), Settings())

    def test_invalid_fields_do_not_discard_valid_fields(self):
        self.path.parent.mkdir()
        self.path.write_text(
            json.dumps(
                {"wait_seconds": 295, "duration_seconds": True, "language": ["en"]}
            ),
            encoding="utf-8",
        )
        self.assertEqual(load_settings(self.path), Settings(wait_seconds=295))

    def test_failed_replace_preserves_previous_file(self):
        save_settings(self.path, Settings())
        with patch("settings.os.replace", side_effect=OSError("read-only")):
            with self.assertRaises(OSError):
                save_settings(self.path, Settings(wait_seconds=30))
        self.assertEqual(load_settings(self.path), Settings())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class LanguageTests(unittest.TestCase):
    def test_system_preference_order_regions_and_fallback(self):
        examples = (
            (["th-TH"], "en"),
            (["th-TH", "fr-CA", "en-US"], "fr"),
            (["zh-TW"], "zh-Hans"),
            (["ar-SA"], "ar"),
            (["es_MX"], "es"),
            (["ru-RU"], "ru"),
            ([], "en"),
        )
        for preferred, expected in examples:
            with self.subTest(preferred=preferred):
                self.assertEqual(resolve_language("auto", preferred), expected)
        self.assertEqual(resolve_language("fr", ["zh-CN"]), "fr")

    def test_all_languages_cover_menu_and_error_strings(self):
        for language, texts in TRANSLATIONS.items():
            self.assertEqual(set(texts), set(TRANSLATIONS["en"]))
            for key in texts:
                self.assertTrue(
                    translate(language, key, value="0.01", minutes=4, seconds=55)
                )


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.device = dict(
            index=2,
            name="Test output",
            hostapi=0,
            default_samplerate=96000,
            max_output_channels=2,
        )
        self.query = patch(
            "soundkeeper.sd.query_devices", return_value=self.device
        ).start()
        self.check = patch("soundkeeper.sd.check_output_settings").start()
        self.addCleanup(patch.stopall)
        self.output = soundkeeper.AudioOutput()

    def test_prefers_default_and_caches_checks(self):
        self.assertEqual(self.output.select_format(), (2, 96000))
        self.assertEqual(self.output.select_format(), (2, 96000))
        self.check.assert_called_once_with(
            device=2, channels=2, dtype="float32", samplerate=96000
        )

    def test_fallback_order_and_no_duplicate_checks(self):
        self.check.side_effect = [
            soundkeeper.sd.PortAudioError("unsupported"),
            soundkeeper.sd.PortAudioError("unsupported"),
            None,
        ]
        self.assertEqual(self.output.select_format(), (2, 48000))
        self.assertEqual(
            [call.kwargs["samplerate"] for call in self.check.call_args_list],
            [96000, 44100, 48000],
        )
        self.output.invalidate()
        self.device["default_samplerate"] = 44100
        self.check.reset_mock(side_effect=True)
        self.check.side_effect = [soundkeeper.sd.PortAudioError("unsupported"), None]
        self.assertEqual(self.output.select_format(), (2, 48000))
        self.assertEqual(self.check.call_count, 2)

    def test_device_change_and_failure_invalidate_cache(self):
        self.output.select_format()
        self.device["index"] = 3
        self.output.select_format()
        self.assertEqual(self.check.call_count, 2)
        with patch(
            "soundkeeper.sd.play",
            side_effect=soundkeeper.sd.PortAudioError("disconnected"),
        ):
            with self.assertRaises(soundkeeper.sd.PortAudioError):
                self.output.play(0.01)
        self.assertIsNone(self.output.device_key)

    def test_all_rates_unsupported(self):
        self.check.side_effect = soundkeeper.sd.PortAudioError("unsupported")
        with self.assertRaises(soundkeeper.sd.PortAudioError):
            self.output.select_format()
        self.assertIsNone(self.output.samplerate)

    def test_playback_uses_selected_rate_duration_and_fixed_amplitude(self):
        with patch("soundkeeper.sd.play") as play, patch("soundkeeper.sd.wait"):
            self.output.play(0.01)
        noise, rate = play.call_args.args
        self.assertEqual(rate, 96000)
        self.assertEqual(noise.shape, (960, 2))
        self.assertEqual(str(noise.dtype), "float32")
        self.assertLessEqual(abs(noise).max(), soundkeeper.AMPLITUDE)


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"
        self.icon_patch = patch("soundkeeper.pystray.Icon", return_value=Mock())
        self.icon_patch.start()
        self.addCleanup(self.icon_patch.stop)
        self.app = soundkeeper.SoundKeeper(self.path)

    def test_menu_options_checked_state_and_language_update(self):
        menu = self.app.icon.menu
        settings = menu.items[2].submenu
        waits = settings.items[0].submenu.items
        durations = settings.items[1].submenu.items
        languages = menu.items[3].submenu.items
        self.assertEqual(len(waits), 5)
        self.assertEqual(len(durations), 3)
        self.assertEqual(len(languages), 7)
        waits[-1](self.app.icon)
        durations[0](self.app.icon)
        languages[-1](self.app.icon)
        self.assertEqual(
            load_settings(self.path),
            Settings(wait_seconds=895, duration_seconds=0.01, language="ar"),
        )
        self.assertEqual(
            [entry.checked for entry in waits], [False, False, False, False, True]
        )
        self.assertEqual(menu.items[0].text, TRANSLATIONS["ar"]["active"])
        self.app.reset_settings(self.app.icon, None)
        self.assertEqual(load_settings(self.path), Settings(language="ar"))

    def test_save_failure_keeps_session_setting_and_reports_error(self):
        with patch("soundkeeper.save_settings", side_effect=OSError("read-only")):
            self.app.change_setting("wait_seconds", 30)(self.app.icon, None)
        self.assertEqual(self.app.settings.wait_seconds, 30)
        self.app.icon.notify.assert_called_once()

    def test_quit_interrupts_long_wait(self):
        played = threading.Event()
        self.app.settings = replace(self.app.settings, wait_seconds=895)
        self.app.output.play = lambda duration: played.set()
        worker = threading.Thread(target=self.app.play_keep_alive_sound, daemon=True)
        worker.start()
        self.assertTrue(played.wait(2))
        with patch("soundkeeper.sd.stop"):
            self.app.quit(self.app.icon, None)
        worker.join(2)
        self.assertFalse(worker.is_alive())

    def test_paused_worker_resumes_without_waiting_full_interval(self):
        played = threading.Event()
        self.app.audio_active = False
        self.app.output.play = lambda duration: played.set()
        worker = threading.Thread(target=self.app.play_keep_alive_sound, daemon=True)
        worker.start()
        try:
            self.app.toggle_activation(self.app.icon, None)
            self.assertTrue(played.wait(2))
        finally:
            with patch("soundkeeper.sd.stop"):
                self.app.quit(self.app.icon, None)
            worker.join(2)
        self.assertFalse(worker.is_alive())


if __name__ == "__main__":
    unittest.main()
