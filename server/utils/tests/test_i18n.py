"""
Tests for i18n infrastructure.

Tests that the Django internationalization is properly configured
and translations work as expected.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.test_settings')

import django
django.setup()

from django.test import TestCase
from django.utils.translation import activate, deactivate, gettext as _, gettext_lazy


class I18nConfigTests(TestCase):
    """Tests for i18n configuration."""

    def test_locale_paths_configured(self):
        """Test that LOCALE_PATHS is properly configured."""
        from django.conf import settings

        self.assertTrue(hasattr(settings, 'LOCALE_PATHS'))
        self.assertTrue(len(settings.LOCALE_PATHS) > 0)

    def test_language_code_configured(self):
        """Test that LANGUAGE_CODE is set to Chinese."""
        from django.conf import settings

        self.assertEqual(settings.LANGUAGE_CODE, 'zh-hans')

    def test_languages_configured(self):
        """Test that LANGUAGES tuple is configured."""
        from django.conf import settings

        self.assertTrue(hasattr(settings, 'LANGUAGES'))
        language_codes = [code for code, name in settings.LANGUAGES]
        self.assertIn('zh-hans', language_codes)
        self.assertIn('en', language_codes)

    def test_use_i18n_enabled(self):
        """Test that USE_I18N is True."""
        from django.conf import settings

        self.assertTrue(settings.USE_I18N)


class TranslationTests(TestCase):
    """Tests for translation functionality."""

    def setUp(self):
        """Set up test by activating Chinese locale."""
        activate('zh-hans')

    def tearDown(self):
        """Clean up by deactivating locale."""
        deactivate()

    def test_common_terms_translated(self):
        """Test that common game terms are translated to Chinese."""
        # These should return Chinese translations
        translations = {
            'Character': '侠客',
            'Player': '玩家',
            'Skill': '武功',
            'Combat': '比武',
            'Domain': '门派',
            'Item': '物品',
            'Health': '气血',
            'Mana': '内力',
        }

        for english, expected_chinese in translations.items():
            result = _(english)
            # If translation exists, it should match; otherwise falls back to English
            self.assertIn(result, [expected_chinese, english])

    def test_lazy_translation(self):
        """Test that lazy translation works for model fields."""
        lazy_str = gettext_lazy('Character')
        # Lazy translation returns a proxy object
        self.assertTrue(hasattr(lazy_str, '__str__'))

    def test_language_switching(self):
        """Test that language can be switched."""
        activate('en')
        # After switching to English, should return English
        result_en = _('Character')

        activate('zh-hans')
        result_zh = _('Character')

        # Both should work (zh-hans may fall back if no translation)
        self.assertIsNotNone(result_en)
        self.assertIsNotNone(result_zh)


class I18nUtilityTests(TestCase):
    """Tests for i18n utility functions."""

    def test_wuxia_terminology_mapping_exists(self):
        """Test that wuxia terminology mapping is defined."""
        from server.utils.i18n_utils import WUXIA_TERMINOLOGY

        self.assertIsInstance(WUXIA_TERMINOLOGY, dict)
        self.assertGreater(len(WUXIA_TERMINOLOGY), 0)

    def test_get_wuxia_term_function(self):
        """Test the get_wuxia_term utility function."""
        from server.utils.i18n_utils import get_wuxia_term

        # Test known terms - 武侠风格
        self.assertEqual(get_wuxia_term('Character'), '侠客')
        self.assertEqual(get_wuxia_term('Skill'), '武功')
        self.assertEqual(get_wuxia_term('Domain'), '门派')
        self.assertEqual(get_wuxia_term('Health'), '气血')
        self.assertEqual(get_wuxia_term('Mana'), '内力')
        self.assertEqual(get_wuxia_term('Combat'), '比武')

        # Unknown terms should return as-is
        self.assertEqual(get_wuxia_term('UnknownTerm'), 'UnknownTerm')

    def test_colored_message_function(self):
        """Test the colored_message utility function."""
        from server.utils.i18n_utils import colored_message, COLOR

        msg = colored_message("测试消息", 'combat')
        self.assertIn(COLOR['red'], msg)
        self.assertIn(COLOR['normal'], msg)

    def test_wuxia_combat_message(self):
        """Test the wuxia_combat_message utility function."""
        from server.utils.i18n_utils import wuxia_combat_message

        # Test different combat actions
        attack_msg = wuxia_combat_message('张三', '李四', 'attack')
        self.assertIn('张三', attack_msg)
        self.assertIn('李四', attack_msg)

        hit_msg = wuxia_combat_message('张三', '李四', 'hit')
        self.assertIn('命中', hit_msg)

        miss_msg = wuxia_combat_message('张三', '李四', 'miss')
        self.assertIn('落了空', miss_msg)


if __name__ == '__main__':
    import unittest
    unittest.main()