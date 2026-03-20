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
import sys

# Debug flag - set to True to enable debug output
DEBUG_CMDSETS = True


def debug_log(msg):
    """Log debug message if DEBUG_CMDSETS is True."""
    if DEBUG_CMDSETS:
        print(f"[CMDSET DEBUG] {msg}", file=sys.stderr)
        sys.stderr.flush()


def check_errors(func):
    """
    Decorator for catching/printing out any errors in method calls. Designed for safer imports.
    """
    @wraps(func)
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            import traceback
            print(f"<<ERROR>>: Error in {func.__name__}: {err}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    return new_func


# Lazy load the CmdSet base class when needed
_CmdSetClass = None

def _get_cmdset_class():
    """Get the CmdSet base class lazily."""
    global _CmdSetClass
    if _CmdSetClass is None:
        import evennia
        evennia._init()
        from evennia.commands.cmdset import CmdSet
        _CmdSetClass = CmdSet
        debug_log(f"CmdSet class loaded: {CmdSet}")
    return _CmdSetClass


# Define the classes. They will be replaced with proper CmdSet subclasses
# when Evennia is initialized. This allows the module to be imported before
# Evennia is ready, while still providing the expected class names.

class _CharacterCmdSetPlaceholder:
    """Placeholder that will be replaced with the actual class."""
    def __new__(cls, *args, **kwargs):
        debug_log("_CharacterCmdSetPlaceholder.__new__ called")
        CmdSet = _get_cmdset_class()

        # Create the actual class
        class CharacterCmdSet(CmdSet):
            key = "DefaultCharacter"
            priority = 101

            def at_cmdset_creation(self):
                debug_log(f"CharacterCmdSet.at_cmdset_creation(), cmdsetobj={self.cmdsetobj}")
                self.add_default_character_commands()
                self.add_standard_cmdsets()
                self.add_other_cmdsets()
                debug_log(f"CharacterCmdSet populated with {len(list(self.commands))} commands")

            @check_errors
            def add_default_character_commands(self):
                from evennia.commands.default.cmdset_character import CharacterCmdSet as EvenniaCharacterCmdSet
                evennia_cmdset = EvenniaCharacterCmdSet()
                evennia_cmdset.at_cmdset_creation()
                for cmd in evennia_cmdset.commands:
                    self.add(cmd)

            @check_errors
            def add_standard_cmdsets(self):
                from commands.cmdsets import standard
                self.add(standard.StateIndependentCmdSet)
                self.add(standard.MobileCmdSet)
                self.add(standard.OOCCmdSet)
                self.add(standard.StaffCmdSet)

            @check_errors
            def add_other_cmdsets(self):
                from typeclasses.wearable import cmdset_wearable
                from commands import agent_commands
                self.add(cmdset_wearable.WearCmdSet)
                self.add(agent_commands.CmdAgentStatus())

        # Return an instance of the actual class
        return CharacterCmdSet(*args, **kwargs)


class _AccountCmdSetPlaceholder:
    """Placeholder that will be replaced with the actual class."""
    def __new__(cls, *args, **kwargs):
        debug_log("_AccountCmdSetPlaceholder.__new__ called")
        CmdSet = _get_cmdset_class()

        class AccountCmdSet(CmdSet):
            key = "DefaultPlayer"
            priority = 101

            def at_cmdset_creation(self):
                debug_log(f"AccountCmdSet.at_cmdset_creation(), cmdsetobj={self.cmdsetobj}")
                self.add_default_account_commands()
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
                debug_log(f"AccountCmdSet populated with {len(list(self.commands))} commands")

            @check_errors
            def add_default_account_commands(self):
                from evennia.commands.default.cmdset_account import AccountCmdSet as EvenniaAccountCmdSet
                evennia_cmdset = EvenniaAccountCmdSet()
                evennia_cmdset.at_cmdset_creation()
                for cmd in evennia_cmdset.commands:
                    self.add(cmd)

            @check_errors
            def add_default_commands(self):
                from evennia.commands.default import account, building, system, admin
                from commands.base_commands import overrides
                from evennia.commands.default import comms

                self.add(account.CmdOOCLook())
                self.add(account.CmdIC())
                self.add(overrides.CmdArxOOC())
                self.add(account.CmdOption())
                self.add(account.CmdQuit())
                self.add(account.CmdPassword())
                self.add(account.CmdColorTest())
                self.add(account.CmdQuell())
                self.add(building.CmdExamine())
                self.add(system.CmdReset())
                self.add(system.CmdShutdown())
                self.add(system.CmdPy())
                self.add(system.CmdAccounts())
                self.add(system.CmdAbout())
                self.add(admin.CmdNewPassword())
                self.add(comms.CmdChannel())
                self.add(comms.CmdIRC2Chan())
                self.add(comms.CmdRSS2Chan())

            @check_errors
            def add_overridden_commands(self):
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
                from commands.base_commands import general
                self.add(general.CmdPage())
                self.add(general.CmdMail())
                self.add(general.CmdGradient())
                self.add(general.CmdInform())
                self.add(general.CmdGameSettings())

            @check_errors
            def add_bboard_commands(self):
                from commands.base_commands import bboards
                self.add(bboards.CmdBBReadOrPost())
                self.add(bboards.CmdBBSub())
                self.add(bboards.CmdBBUnsub())
                self.add(bboards.CmdBBCreate())
                self.add(bboards.CmdBBNew())
                self.add(bboards.CmdOrgStance())

            @check_errors
            def add_roster_commands(self):
                from commands.base_commands import roster
                self.add(roster.CmdRosterList())
                self.add(roster.CmdAdminRoster())
                self.add(roster.CmdSheet())
                self.add(roster.CmdRelationship())
                self.add(roster.CmdDelComment())
                self.add(roster.CmdAdmRelationship())

            @check_errors
            def add_jobs_commands(self):
                from commands.base_commands import jobs
                self.add(jobs.CmdJob())
                self.add(jobs.CmdRequest())
                self.add(jobs.CmdApp())

            @check_errors
            def add_dominion_commands(self):
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
                from commands.base_commands import staff_commands
                from commands.cmdsets import starting_gear
                from world.fashion import fashion_commands
                from web.character import file_commands
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
                self.add(starting_gear.CmdSetupGear())
                self.add(fashion_commands.CmdAdminFashion())
                self.add(file_commands.CmdAdminFile)

            @check_errors
            def add_investigation_commands(self):
                from web.character import investigation
                self.add(investigation.CmdAdminInvestigations())
                self.add(investigation.CmdListClues())
                self.add(investigation.CmdTheories())
                self.add(investigation.CmdListRevelations())
                self.add(investigation.CmdPRPClue())
                self.add(investigation.CmdPRPRevelation())

            @check_errors
            def add_scene_commands(self):
                from web.character import scene_commands
                self.add(scene_commands.CmdFlashback())

            @check_errors
            def add_gming_actions_commands(self):
                from world.dominion import crisis_commands
                from commands.base_commands import story_actions
                self.add(crisis_commands.CmdViewCrisis())
                self.add(crisis_commands.CmdGMCrisis())
                self.add(story_actions.CmdGMAction)

            @check_errors
            def add_lore_commands(self):
                from web.helpdesk import lore_commands
                self.add(lore_commands.CmdLoreSearch())

        return AccountCmdSet(*args, **kwargs)


class _UnloggedinCmdSetPlaceholder:
    """Placeholder that will be replaced with the actual class."""
    def __new__(cls, *args, **kwargs):
        CmdSet = _get_cmdset_class()

        class UnloggedinCmdSet(CmdSet):
            key = "DefaultUnloggedin"

            def at_cmdset_creation(self):
                try:
                    from evennia.commands.default.cmdset_unloggedin import UnloggedinCmdSet as EvenniaUnloggedinCmdSet
                    evennia_cmdset = EvenniaUnloggedinCmdSet()
                    evennia_cmdset.at_cmdset_creation()
                    for cmd in evennia_cmdset.commands:
                        self.add(cmd)

                    from commands.base_commands import unloggedin
                    from commands import agent_commands
                    self.add(unloggedin.CmdGuestConnect())
                    self.add(unloggedin.CmdUnconnectedHelp())
                    self.add(agent_commands.CmdAgentConnect())
                except Exception as err:
                    print("<<ERROR>>: Error encountered in loading Unlogged cmdset: %s" % err)

        return UnloggedinCmdSet(*args, **kwargs)


class _SessionCmdSetPlaceholder:
    """Placeholder that will be replaced with the actual class."""
    def __new__(cls, *args, **kwargs):
        CmdSet = _get_cmdset_class()

        class SessionCmdSet(CmdSet):
            key = "DefaultSession"

            def at_cmdset_creation(self):
                from evennia.commands.default.cmdset_session import SessionCmdSet as EvenniaSessionCmdSet
                evennia_cmdset = EvenniaSessionCmdSet()
                evennia_cmdset.at_cmdset_creation()
                for cmd in evennia_cmdset.commands:
                    self.add(cmd)

        return SessionCmdSet(*args, **kwargs)


# Export the placeholders as the expected names
CharacterCmdSet = _CharacterCmdSetPlaceholder
AccountCmdSet = _AccountCmdSetPlaceholder
UnloggedinCmdSet = _UnloggedinCmdSetPlaceholder
SessionCmdSet = _SessionCmdSetPlaceholder