"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""
from functools import wraps


def check_errors(func):
    """
    Decorator for catching/printing out any errors in method calls. Designed for safer imports.
    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """
    # noinspection PyBroadException
    @wraps(func)
    def new_func(*args, **kwargs):
        """Wrapper around function with exception handling"""
        try:
            return func(*args, **kwargs)
        except Exception as err:
            import traceback
            import sys
            print(f"<<ERROR>>: Error in {func.__name__}: {err}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

    return new_func


def _get_cmdset_class():
    """Lazy import of CmdSet class."""
    from evennia.commands.cmdset import CmdSet
    return CmdSet


# Define command sets as factory functions to avoid module-level import errors
# These are loaded lazily when Evennia is properly initialized

def CharacterCmdSet(cmdsetobj=None):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `PlayerCmdSet` when a Player puppets a Character.
    """
    CmdSet = _get_cmdset_class()

    class _CharacterCmdSet(CmdSet):
        key = "DefaultCharacter"
        priority = 101

        def at_cmdset_creation(self):
            """
            Populates the cmdset
            """
            # Add Evennia's default character commands first
            self.add_default_character_commands()
            # Then add our custom command sets
            self.add_standard_cmdsets()
            self.add_other_cmdsets()

        @check_errors
        def add_default_character_commands(self):
            """Add Evennia's default character commands"""
            from evennia.commands.default.cmdset_character import CharacterCmdSet as EvenniaCharacterCmdSet
            # Create Evennia's default cmdset and copy its commands
            evennia_cmdset = EvenniaCharacterCmdSet()
            evennia_cmdset.at_cmdset_creation()
            for cmd in evennia_cmdset.commands:
                self.add(cmd)

        @check_errors
        def add_standard_cmdsets(self):
            """Add different command sets that all characters should have"""
            from commands.cmdsets import standard
            self.add(standard.StateIndependentCmdSet)
            self.add(standard.MobileCmdSet)
            self.add(standard.OOCCmdSet)
            self.add(standard.StaffCmdSet)

        @check_errors
        def add_other_cmdsets(self):
            """Miscellaneous command sets"""
            from typeclasses.wearable import cmdset_wearable
            from commands import agent_commands
            self.add(cmdset_wearable.WearCmdSet)
            # Agent authentication commands
            self.add(agent_commands.CmdAgentStatus())

    return _CharacterCmdSet()


def AccountCmdSet(cmdsetobj=None):
    """
    This is the cmdset available to the Player at all times. It is
    combined with the `CharacterCmdSet` when the Player puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    CmdSet = _get_cmdset_class()

    class _AccountCmdSet(CmdSet):
        key = "DefaultPlayer"
        priority = 101

        def at_cmdset_creation(self):
            """
            Populates the cmdset
            """
            # Add Evennia's default account commands first
            self.add_default_account_commands()
            # Then add our custom commands
            self.add_default_commands()
            self.add_overridden_commands()
            self.add_general_commands()
            self.add_bboard_commands()
            self.add_roster_commands()
            self.add_jobs_commands()
            self.add_dominion_commands()
            self.add_social_commands()
            self.add_staff_commands()
            self.add_investigation_commands()
            self.add_scene_commands()
            self.add_gming_actions_commands()
            self.add_lore_commands()

        @check_errors
        def add_default_account_commands(self):
            """Add Evennia's default account commands"""
            from evennia.commands.default.cmdset_account import AccountCmdSet as EvenniaAccountCmdSet
            # Create Evennia's default cmdset and copy its commands
            evennia_cmdset = EvenniaAccountCmdSet()
            evennia_cmdset.at_cmdset_creation()
            for cmd in evennia_cmdset.commands:
                self.add(cmd)

        @check_errors
        def add_default_commands(self):
            """Add selected Evennia built-in commands"""
            from evennia.commands.default import account, building, system, admin
            from commands.base_commands import overrides
            # Import channel commands from compatibility module
            from commands.base_commands.channel_compat import CmdAddCom, CmdDelCom, CmdCemit
            from evennia.commands.default import comms

            # Player-specific commands
            self.add(account.CmdOOCLook())
            self.add(account.CmdIC())
            self.add(overrides.CmdArxOOC())
            self.add(account.CmdOption())
            self.add(account.CmdQuit())
            self.add(account.CmdPassword())
            self.add(account.CmdColorTest())
            self.add(account.CmdQuell())
            self.add(building.CmdExamine())
            # system commands
            self.add(system.CmdReset())
            self.add(system.CmdShutdown())
            self.add(system.CmdPy())
            self.add(system.CmdAccounts())
            self.add(system.CmdAbout())
            # Admin commands
            self.add(admin.CmdNewPassword())
            # Comm commands - use the new CmdChannel for basic operations
            self.add(comms.CmdChannel())
            self.add(comms.CmdIRC2Chan())
            self.add(comms.CmdRSS2Chan())

        @check_errors
        def add_overridden_commands(self):
            """Add arx overrides of Evennia commands"""
            from commands.base_commands import help as cmd_help, overrides

            self.add(cmd_help.CmdHelp())
            self.add(overrides.CmdWho())
            self.add(overrides.CmdArxSetAttribute())
            self.add(overrides.CmdArxCdestroy())
            self.add(overrides.CmdArxChannelCreate())
            self.add(overrides.CmdArxClock())
            self.add(overrides.CmdArxCBoot())
            self.add(overrides.CmdArxCdesc())
            self.add(overrides.CmdArxAllCom())
            self.add(overrides.CmdArxChannels())
            self.add(overrides.CmdArxCWho())
            self.add(overrides.CmdArxReload())

        @check_errors
        def add_general_commands(self):
            """Add general/misc commands"""
            from commands.base_commands import general

            self.add(general.CmdPage())
            self.add(general.CmdMail())
            self.add(general.CmdGradient())
            self.add(general.CmdInform())
            self.add(general.CmdGameSettings())

        @check_errors
        def add_bboard_commands(self):
            """Add commands for bulletin boards"""
            from commands.base_commands import bboards

            self.add(bboards.CmdBBReadOrPost())
            self.add(bboards.CmdBBSub())
            self.add(bboards.CmdBBUnsub())
            self.add(bboards.CmdBBCreate())
            self.add(bboards.CmdBBNew())
            self.add(bboards.CmdOrgStance())

        @check_errors
        def add_roster_commands(self):
            """Add commands around roster viewing or management"""
            from commands.base_commands import roster

            self.add(roster.CmdRosterList())
            self.add(roster.CmdAdminRoster())
            self.add(roster.CmdSheet())
            self.add(roster.CmdRelationship())
            self.add(roster.CmdDelComment())
            self.add(roster.CmdAdmRelationship())

        @check_errors
        def add_jobs_commands(self):
            """Add commands for interacting with helpdesk"""
            from commands.base_commands import jobs

            self.add(jobs.CmdJob())
            self.add(jobs.CmdRequest())
            self.add(jobs.CmdApp())

        @check_errors
        def add_dominion_commands(self):
            """Add commands related to Dominion, the offscreen estate-management game"""
            from world.dominion import general_dominion_commands as domcommands
            from world.dominion import agent_commands as dominion_agents

            self.add(domcommands.CmdAdmDomain())
            self.add(domcommands.CmdAdmArmy())
            self.add(domcommands.CmdAdmCastle())
            self.add(domcommands.CmdAdmAssets())
            self.add(domcommands.CmdAdmFamily())
            self.add(domcommands.CmdAdmOrganization())
            self.add(domcommands.CmdDomain())
            self.add(domcommands.CmdFamily())
            self.add(domcommands.CmdOrganization())
            self.add(domcommands.CmdArmy())
            self.add(dominion_agents.CmdAgents())
            self.add(domcommands.CmdPatronage())
            self.add(dominion_agents.CmdRetainers())

        @check_errors
        def add_social_commands(self):
            """Add commands for social RP"""
            from commands.base_commands import social

            self.add(social.CmdFinger())
            self.add(social.CmdWatch())
            self.add(social.CmdCalendar())
            self.add(social.CmdAFK())
            self.add(social.CmdWhere())
            self.add(social.CmdCensus())
            self.add(social.CmdIAmHelping())
            self.add(social.CmdRPHooks())

        @check_errors
        def add_staff_commands(self):
            """Add commands for staff players"""
            from commands.base_commands import staff_commands

            # more recently implemented staff commands
            self.add(staff_commands.CmdRestore())
            self.add(staff_commands.CmdSendVision())
            self.add(staff_commands.CmdAskStaff())
            self.add(staff_commands.CmdListStaff())
            self.add(staff_commands.CmdPurgeJunk())
            self.add(staff_commands.CmdAdjustReputation())
            self.add(staff_commands.CmdViewLog())
            self.add(staff_commands.CmdSetLanguages())
            self.add(staff_commands.CmdGMNotes())
            self.add(staff_commands.CmdJournalAdminForDummies())
            self.add(staff_commands.CmdTransferKeys())
            self.add(staff_commands.CmdAdminTitles())
            self.add(staff_commands.CmdAdminWrit())
            self.add(staff_commands.CmdAdminBreak())
            self.add(staff_commands.CmdSetServerConfig())
            from commands.cmdsets import starting_gear

            self.add(starting_gear.CmdSetupGear())
            from world.fashion import fashion_commands

            self.add(fashion_commands.CmdAdminFashion())
            from web.character import file_commands

            self.add(file_commands.CmdAdminFile)

        @check_errors
        def add_investigation_commands(self):
            """Add commands based on investigations/clus"""
            from web.character import investigation

            self.add(investigation.CmdAdminInvestigations())
            self.add(investigation.CmdListClues())
            self.add(investigation.CmdTheories())
            self.add(investigation.CmdListRevelations())
            self.add(investigation.CmdPRPClue())
            self.add(investigation.CmdPRPRevelation())

        @check_errors
        def add_scene_commands(self):
            """Commands for flashbacks"""
            from web.character import scene_commands

            self.add(scene_commands.CmdFlashback())

        @check_errors
        def add_gming_actions_commands(self):
            """Add commands for interacting with crises and GMing"""
            from world.dominion import crisis_commands

            self.add(crisis_commands.CmdViewCrisis())
            self.add(crisis_commands.CmdGMCrisis())
            from commands.base_commands import story_actions

            self.add(story_actions.CmdGMAction)

        @check_errors
        def add_lore_commands(self):
            """Add commands for using lore knowledge base"""
            from web.helpdesk import lore_commands

            self.add(lore_commands.CmdLoreSearch())

    return _AccountCmdSet()


def UnloggedinCmdSet(cmdsetobj=None):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """
    CmdSet = _get_cmdset_class()

    class _UnloggedinCmdSet(CmdSet):
        key = "DefaultUnloggedin"

        def at_cmdset_creation(self):
            """
            Populates the cmdset
            """
            try:
                # Add Evennia's default unloggedin commands
                from evennia.commands.default.cmdset_unloggedin import UnloggedinCmdSet as EvenniaUnloggedinCmdSet
                evennia_cmdset = EvenniaUnloggedinCmdSet()
                evennia_cmdset.at_cmdset_creation()
                for cmd in evennia_cmdset.commands:
                    self.add(cmd)

                # Add our custom unloggedin commands
                from commands.base_commands import unloggedin
                from commands import agent_commands
                self.add(unloggedin.CmdGuestConnect())
                self.add(unloggedin.CmdUnconnectedHelp())
                # Agent authentication commands for unloggedin users
                self.add(agent_commands.CmdAgentConnect())
            except Exception as err:
                print("<<ERROR>>: Error encountered in loading Unlogged cmdset: %s" % err)

    return _UnloggedinCmdSet()


def SessionCmdSet(cmdsetobj=None):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """
    CmdSet = _get_cmdset_class()

    class _SessionCmdSet(CmdSet):
        key = "DefaultSession"

        def at_cmdset_creation(self):
            """
            This is the only method defined in a cmdset, called during
            its creation. It should populate the set with command instances.

            As and example we just add the empty base `Command` object.
            It prints some info.
            """
            # Add Evennia's default session commands
            from evennia.commands.default.cmdset_session import SessionCmdSet as EvenniaSessionCmdSet
            evennia_cmdset = EvenniaSessionCmdSet()
            evennia_cmdset.at_cmdset_creation()
            for cmd in evennia_cmdset.commands:
                self.add(cmd)

    return _SessionCmdSet()