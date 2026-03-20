"""
Basic starting cmdsets for characters. Each of these
cmdsets attempts to represent some aspect of how
characters function, so that different conditions
on characters can extend/modify/remove functionality
from them without explicitly calling individual commands.

"""
# Only import CmdSet at module level - it's safe
from evennia.commands.cmdset import CmdSet


class OOCCmdSet(CmdSet):
    """Character-specific OOC commands. Most OOC commands defined in player."""

    key = "OOCCmdSet"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.
        """
        # Lazy imports to avoid Evennia initialization order issues
        from commands.base_commands import overrides, rolling, general, social, xp, roster, bboards, help as cmd_help
        from world.stat_checks import check_commands
        from world.exploration import exploration_commands
        from world.weather import weather_commands
        from typeclasses import rooms as extended_room
        from evennia.commands.default import general as default_general

        self.add(overrides.CmdInventory())
        self.add(default_general.CmdNick())
        self.add(default_general.CmdAccess())
        # Help command - must be available for all characters
        self.add(cmd_help.CmdHelp())
        self.add(rolling.CmdDiceString())
        self.add(rolling.CmdDiceCheckVersionOne())
        self.add(rolling.CmdOldSpoofCheck())
        self.add(check_commands.CmdStatCheck())
        self.add(check_commands.CmdHarm())
        self.add(check_commands.CmdSpoofCheck())
        self.add(general.CmdBriefMode())
        self.add(general.CmdTidyUp())
        self.add(extended_room.CmdGameTime())
        self.add(extended_room.CmdSetGameTimescale())
        self.add(extended_room.CmdStudyRawAnsi())
        self.add(xp.CmdVoteXP())
        self.add(social.CmdPosebreak())
        self.add(social.CmdSocialNotable())
        self.add(social.CmdSocialNominate())
        self.add(social.CmdSocialReview())
        self.add(overrides.SystemNoMatch())
        self.add(weather_commands.CmdAdminWeather())
        self.add(roster.CmdPropriety())
        self.add(exploration_commands.CmdExplorationCmdSet())
        # BBoard commands
        self.add(bboards.CmdBBSub())
        self.add(bboards.CmdBBUnsub())
        self.add(bboards.CmdBBReadOrPost())
        self.add(bboards.CmdBBNew())


class StateIndependentCmdSet(CmdSet):
    """
    Character commands that will always exist, regardless of character state.
    Poses and emits, for example, should be allowed even when a character is
    dead, because they might be posing something about the corpse, etc.
    """

    key = "StateIndependentCmdSet"

    def at_cmdset_creation(self):
        # Lazy imports to avoid Evennia initialization order issues
        from commands.base_commands import overrides, general, social, maps, story_actions, roster
        from typeclasses import rooms as extended_room
        from typeclasses.readable.readable_commands import WriteCmdSet
        from world.magic import magic_commands
        from world.dominion.plots import plot_commands
        from web.character import goal_commands
        from commands.cmdsets import combat

        self.add(overrides.CmdPose())
        self.add(overrides.CmdEmit())
        self.add(overrides.CmdArxTime())
        self.add(general.CmdOOCSay())
        self.add(general.CmdDirections())
        self.add(general.CmdKeyring())
        self.add(general.CmdGlance())
        self.add(extended_room.CmdExtendedLook())
        self.add(roster.CmdHere())
        self.add(social.CmdHangouts())
        self.add(social.CmdWhere())
        self.add(social.CmdJournal())
        self.add(social.CmdMessenger())
        self.add(social.CmdRoomHistory())
        self.add(social.CmdRoomMood())
        self.add(social.CmdRandomScene())
        self.add(social.CmdRoomTitle())
        self.add(social.CmdTempDesc())
        self.add(social.CmdLanguages())
        self.add(maps.CmdMap())
        self.add(story_actions.CmdAction())
        self.add(plot_commands.CmdPlots())
        self.add(goal_commands.CmdGoals())
        self.add(combat.CmdHeal())
        self.add(WriteCmdSet())
        self.add(magic_commands.MagicCmdSet())


class MobileCmdSet(CmdSet):
    """
    Commands that should only be allowed if the character is able to move.
    """

    key = "MobileCmdSet"

    def at_cmdset_creation(self):
        # Lazy imports to avoid Evennia initialization order issues
        from commands.base_commands import overrides, general, exchanges, xp, crafting, social
        from typeclasses.places import cmdset_places
        from typeclasses.gambling import cmdset_gambling as gambling
        from commands.cmdsets import combat
        from world.dominion import agent_commands, general_dominion_commands as domcommands
        from typeclasses.consumable.use_commands import CmdApplyConsumable
        from world.fashion import fashion_commands
        from world.prayer import prayer_commands
        from world.dominion.plots import plot_commands
        from web.character import investigation
        from world.petitions import petitions_commands
        from world.conditions import condition_commands

        self.add(overrides.CmdGet())
        self.add(overrides.CmdDrop())
        self.add(exchanges.CmdGive())
        self.add(exchanges.CmdTrade())
        self.add(overrides.CmdArxSay())
        self.add(general.CmdWhisper())
        self.add(general.CmdFollow())
        self.add(general.CmdDitch())
        self.add(general.CmdShout())
        self.add(general.CmdPut())
        self.add(general.CmdLockObject())
        self.add(xp.CmdTrain())
        self.add(xp.CmdUseXP())
        self.add(cmdset_places.CmdListPlaces())
        self.add(combat.CmdStartCombat())
        self.add(combat.CmdProtect())
        self.add(combat.CmdAutoattack())
        self.add(combat.CmdCombatStats())
        self.add(combat.CmdOldHarm())
        self.add(combat.CmdFightStatus())
        self.add(agent_commands.CmdGuards())
        self.add(domcommands.CmdPlotRoom())
        self.add(domcommands.CmdWork())
        self.add(domcommands.CmdCleanupDomain())
        self.add(crafting.CmdCraft())
        self.add(crafting.CmdRecipes())
        self.add(crafting.CmdJunk())
        self.add(social.CmdPraise())
        self.add(social.CmdThink())
        self.add(social.CmdFeel())
        self.add(social.CmdDonate())
        self.add(social.CmdCoinFlip())
        self.add(social.CmdFirstImpression())
        self.add(social.CmdGetInLine())
        self.add(investigation.CmdInvestigate())
        self.add(investigation.CmdAssistInvestigation())
        self.add(general.CmdDump())
        self.add(CmdApplyConsumable())
        self.add(gambling.CmdDice())
        self.add(fashion_commands.CmdFashionModel())
        self.add(fashion_commands.CmdFashionOutfit())
        self.add(petitions_commands.CmdPetition())
        self.add(condition_commands.CmdKnacks())
        self.add(prayer_commands.CmdPray())
        self.add(plot_commands.CmdStlist())


class StaffCmdSet(CmdSet):
    """OOC staff and building commands. Character-based due to interacting with game world."""

    key = "StaffCmdSet"

    def at_cmdset_creation(self):
        # Lazy imports to avoid Evennia initialization order issues
        from evennia.commands.default import help, admin, system, building, batchprocess
        from commands.base_commands import overrides, staff_commands, xp, maps, bboards
        from typeclasses import rooms as extended_room
        from world.dominion import general_dominion_commands as domcommands
        from world.dominion.plots import plot_commands
        from web.character import goal_commands
        from typeclasses.containers.container import CmdRoot
        from world.templates.template_commands import CmdTemplateForm
        from commands.cmdsets import combat, home
        from world.conditions import condition_commands

        # The help system
        self.add(help.CmdSetHelp())
        # System commands
        self.add(overrides.CmdArxScripts())
        self.add(building.CmdObjects())
        self.add(system.CmdAccounts())
        self.add(system.CmdService())
        self.add(system.CmdAbout())
        self.add(system.CmdServerLoad())
        # Admin commands
        self.add(admin.CmdBoot())
        self.add(admin.CmdBan())
        self.add(admin.CmdUnban())
        self.add(admin.CmdPerm())
        self.add(admin.CmdWall())
        # Building and world manipulation
        self.add(overrides.CmdTeleport())
        self.add(building.CmdSetObjAlias())
        self.add(building.CmdListCmdSets())
        self.add(building.CmdWipe())
        self.add(building.CmdName())
        self.add(building.CmdCpAttr())
        self.add(building.CmdMvAttr())
        self.add(building.CmdCopy())
        self.add(building.CmdFind())
        self.add(building.CmdOpen())
        self.add(building.CmdLink())
        self.add(building.CmdUnLink())
        self.add(building.CmdCreate())
        self.add(overrides.CmdDig())
        self.add(building.CmdTunnel())
        self.add(overrides.CmdArxDestroy())
        self.add(overrides.CmdArxExamine())
        self.add(building.CmdTypeclass())
        self.add(overrides.CmdArxLock())
        self.add(building.CmdScripts())
        self.add(building.CmdSetHome())
        self.add(overrides.CmdArxTag())
        # Batchprocessor commands
        self.add(batchprocess.CmdBatchCommands())
        self.add(batchprocess.CmdBatchCode())
        # more recently implemented staff commands
        self.add(staff_commands.CmdGemit())
        self.add(staff_commands.CmdWall())
        self.add(staff_commands.CmdHome())
        self.add(staff_commands.CmdResurrect())
        self.add(staff_commands.CmdKill())
        self.add(staff_commands.CmdForce())
        self.add(staff_commands.CmdCcolor())
        self.add(staff_commands.CmdGMDisguise())
        self.add(staff_commands.CmdGMEvent())
        self.add(staff_commands.CmdRelocateExit())
        self.add(staff_commands.CmdAdminKey())
        self.add(staff_commands.CmdAdminPropriety())
        self.add(staff_commands.CmdAdjustFame())
        self.add(staff_commands.CmdAdjust())
        self.add(staff_commands.CmdStaffPost())
        self.add(plot_commands.CmdGMPlots())
        self.add(plot_commands.CmdStoryCoordinators())
        self.add(goal_commands.CmdGMGoals())
        self.add(extended_room.CmdExtendedDesc())
        self.add(xp.CmdAdjustSkill())
        self.add(xp.CmdAwardXP())
        self.add(maps.CmdMapCreate())
        self.add(maps.CmdMapRoom())
        self.add(combat.CmdObserveCombat())
        self.add(combat.CmdAdminCombat())
        self.add(combat.CmdCreateAntagonist())
        self.add(combat.CmdStandYoAssUp())
        self.add(domcommands.CmdSetRoom())
        self.add(condition_commands.CmdModifiers())
        # home commands
        self.add(home.CmdAllowBuilding())
        self.add(home.CmdBuildRoom())
        self.add(home.CmdManageRoom())
        self.add(CmdRoot())
        self.add(CmdTemplateForm())
        # Staff bboard commands
        self.add(bboards.CmdBBCreate())