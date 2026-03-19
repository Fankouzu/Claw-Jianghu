# Translation management script
"""
Script for managing translations in Arx/Claw-Dominion.

Usage:
    python manage_translation.py extract    # Extract translatable strings
    python manage_translation.py compile    # Compile .po to .mo files
    python manage_translation.py stats      # Show translation statistics
    python manage_translation.py init       # Initialize locale directory
"""

import os
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
LOCALE_DIR = PROJECT_ROOT / "locale"


def run_command(cmd: list, cwd: str = None):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def extract_messages():
    """Extract translatable strings from Python files and templates."""
    print("Extracting translatable strings...")

    # Create locale directory if it doesn't exist
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    (LOCALE_DIR / "zh_Hans" / "LC_MESSAGES").mkdir(parents=True, exist_ok=True)

    # Run makemessages for Python files
    print("\nExtracting from Python files...")
    code, stdout, stderr = run_command([
        "python", "manage.py", "makemessages",
        "--locale=zh_Hans",
        "--ignore=venv/*",
        "--ignore=env/*",
        "--no-location"
    ])

    if code == 0:
        print("Python messages extracted successfully")
    else:
        print(f"Error extracting Python messages: {stderr}")

    # Run makemessages for templates
    print("\nExtracting from templates...")
    code, stdout, stderr = run_command([
        "python", "manage.py", "makemessages",
        "--locale=zh_Hans",
        "--domain=djangojs",
        "--extension=html",
        "--ignore=venv/*",
        "--ignore=env/*",
        "--no-location"
    ])

    if code == 0:
        print("Template messages extracted successfully")
    else:
        print(f"Error extracting template messages: {stderr}")


def compile_messages():
    """Compile .po files to .mo files."""
    print("Compiling translation files...")

    code, stdout, stderr = run_command([
        "python", "manage.py", "compilemessages"
    ])

    if code == 0:
        print("Translation files compiled successfully")
    else:
        print(f"Error compiling: {stderr}")


def show_stats():
    """Show translation statistics."""
    po_file = LOCALE_DIR / "zh_Hans" / "LC_MESSAGES" / "django.po"

    if not po_file.exists():
        print("No translation file found. Run 'extract' first.")
        return

    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count translated and untranslated entries
    import re
    translated = len(re.findall(r'^msgstr ".+"', content, re.MULTILINE))
    untranslated = len(re.findall(r'^msgstr ""', content, re.MULTILINE))
    total = translated + untranslated

    print(f"\nTranslation Statistics for zh_Hans:")
    print(f"  Total entries: {total}")
    print(f"  Translated: {translated} ({translated/total*100:.1f}%)")
    print(f"  Untranslated: {untranslated} ({untranslated/total*100:.1f}%)")


def init_locale():
    """Initialize the locale directory structure."""
    print("Initializing locale directory...")

    dirs = [
        LOCALE_DIR,
        LOCALE_DIR / "zh_Hans",
        LOCALE_DIR / "zh_Hans" / "LC_MESSAGES",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {d}")

    # Create initial django.po file
    po_file = LOCALE_DIR / "zh_Hans" / "LC_MESSAGES" / "django.po"
    if not po_file.exists():
        po_file.write_text(DEFAULT_PO_CONTENT, encoding='utf-8')
        print(f"  Created: {po_file}")

    print("\nLocale directory initialized successfully!")


DEFAULT_PO_CONTENT = """# Chinese (Simplified) translation for Arx/Claw-Dominion
# Copyright (C) 2024
# This file is distributed under the same license as the Arx package.
#
msgid ""
msgstr ""
"Project-Id-Version: Arx\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"PO-Revision-Date: 2024-01-01 00:00+0000\\n"
"Last-Translator: \\n"
"Language-Team: Chinese (Simplified)\\n"
"Language: zh_Hans\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"

# Common game terms
msgid "Character"
msgstr "角色"

msgid "Player"
msgstr "玩家"

msgid "Account"
msgstr "账户"

msgid "Session"
msgstr "会话"

msgid "Stat"
msgstr "属性"

msgid "Skill"
msgstr "技能"

msgid "Ability"
msgstr "能力"

msgid "Check"
msgstr "检定"

msgid "Roll"
msgstr "投骰"

msgid "Combat"
msgstr "战斗"

msgid "Domain"
msgstr "领地"

msgid "Organization"
msgstr "组织"

msgid "Estate"
msgstr "庄园"

msgid "Army"
msgstr "军队"

msgid "Item"
msgstr "物品"

msgid "Weapon"
msgstr "武器"

msgid "Armor"
msgstr "护甲"

msgid "Potion"
msgstr "药剂"

msgid "Channel"
msgstr "频道"

msgid "Message"
msgstr "消息"

msgid "Journal"
msgstr "日志"

msgid "Health"
msgstr "生命"

msgid "Mana"
msgstr "法力"

msgid "Stamina"
msgstr "体力"
"""


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "extract":
        extract_messages()
    elif command == "compile":
        compile_messages()
    elif command == "stats":
        show_stats()
    elif command == "init":
        init_locale()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()