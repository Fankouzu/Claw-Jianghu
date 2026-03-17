# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Arx is a MUX-style multiplayer text game built on Evennia, a Python MUD/MUX framework. It features an original low-fantasy setting with domain management, crafting, magic, and roleplaying systems.

## Development Commands

### Running Tests
```bash
evennia test --settings=test_settings --nomigrations .
```

### Running a Single Test Module
```bash
evennia test --settings=test_settings --nomigrations path.to.test_module
# Example: evennia test --settings=test_settings --nomigrations world.dominion.tests
```

### Linting
```bash
black .  # Version 22.3.0 is used
```

### Database Migrations
```bash
evennia migrate --settings=<settings_file>
```
Squash migrations into a single file when possible.

### Running the Server
```bash
evennia start --settings=production_settings
```

## Architecture

### Evennia Framework Basics
Evennia uses typeclasses to define game objects. All game entities inherit from Evennia's base classes and are extended through mixins. Key typeclasses are defined in `server/conf/base_settings.py`:
- `BASE_ROOM_TYPECLASS = "typeclasses.rooms.ArxRoom"`
- `BASE_SCRIPT_TYPECLASS = "typeclasses.scripts.scripts.Script"`
- `BASE_GUEST_TYPECLASS = "typeclasses.guest.Guest"`

### Directory Structure

**typeclasses/** - Core game objects that persist in the database:
- `characters.py` - Player characters (uses multiple mixins)
- `rooms.py` - Game rooms/locations
- `objects.py` - Items and in-game objects
- `scripts/` - Background scripts (combat, recovery, events)
- `wearable/` - Equipment system
- `npcs/` - NPC implementations

**commands/** - Player commands organized into command sets:
- `default_cmdsets.py` - Main entry point defining CharacterCmdSet, AccountCmdSet, UnloggedinCmdSet
- `base_commands/` - Individual command modules (general, social, staff, etc.)
- `cmdsets/` - Situational command sets (combat, bank, market, etc.)

**world/** - Game-specific Django apps and logic:
- `dominion/` - Estate management, armies, organizations
- `magic/` - Magic system with conditional parser
- `conditions/` - Status effects and modifiers
- `crafting/` - Item crafting system
- `stat_checks/` - Dice rolling and skill checks

**web/** - Django web application:
- `character/` - Character sheets, investigations, scenes
- `helpdesk/` - Ticket/bug tracking system
- `news/` - News/announcements

**evennia_extensions/** - Extensions to Evennia core:
- `character_extensions/` - Character data storage
- `object_extensions/` - Item data storage, display names
- `room_extensions/` - Room-specific extensions

**server/conf/** - Settings files:
- `base_settings.py` - Base configuration, INSTALLED_APPS
- `production_settings.py` - Production overrides
- `test_settings.py` - Test configuration

### Key Patterns

**Mixins Pattern**: Typeclasses use multiple inheritance with mixins defined in `typeclasses/mixins.py`:
- `ObjectMixins` - Core object functionality (names, descriptions, appearance)
- `MsgMixins` - Message handling with language support
- `ModifierMixin` - Stat/skill modifiers
- `DescMixins`, `NameMixins`, `AppearanceMixins` - Display handling

**Handlers**: Complex logic is encapsulated in handler classes:
- `ItemDataHandler` - Persistent item data storage
- `MessageHandler` - In-game messaging
- `TriggerHandler` - Event triggers
- `CraftDataHandler` - Crafting data

**Command Sets**: Commands are grouped into sets that can be added/removed at runtime. See `default_cmdsets.py` for how commands are registered.

### Configuration

Settings use python-decouple. Create a `settings.ini` file at the repo root for configuration. Key settings:
- `SERVERNAME` - Game name
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode
- Database settings, email settings, etc.

### Testing Notes

Tests should be written for all pull requests. Evennia testing can be challenging due to the framework's complexity. Test files are typically named `tests.py` within each module.