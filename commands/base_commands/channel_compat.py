"""
Compatibility module for Evennia 5.0 channel commands.

In Evennia 5.0, the old separate channel commands (CmdCdestroy, CmdChannelCreate, etc.)
were consolidated into a single CmdChannel command with subcommands.

This module provides compatibility wrappers for legacy code.
"""
from django.conf import settings


def _get_command_class():
    """Lazy import to avoid circular import during Evennia initialization."""
    from evennia.utils.utils import class_from_module
    return class_from_module(settings.COMMAND_DEFAULT_CLASS)


def _get_cmd_channel():
    """Lazy import of CmdChannel to avoid initialization order issues."""
    from evennia.commands.default.comms import CmdChannel
    return CmdChannel


# Base class that will be set at runtime
_CommandBase = None

def _get_base_class():
    """Get or create the base class for compatibility commands."""
    global _CommandBase
    if _CommandBase is None:
        _CommandBase = _get_command_class()
    return _CommandBase


class _CompatCommandMixin:
    """
    Mixin that ensures compatibility command attributes are properly set.
    This is needed because our compatibility classes don't inherit from
    the standard Command class at definition time.
    """

    # These are the attributes that Evennia's Command metaclass sets
    auto_help = True
    arg_regex = None  # Will be compiled by Evennia if string
    auto_help_display_key = None
    is_exit = False
    retain_instance = False

    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is created."""
        super().__init_subclass__(**kwargs)
        # Ensure auto_help is set on the subclass
        if not hasattr(cls, 'auto_help'):
            cls.auto_help = True


class CmdCdestroy(_CompatCommandMixin):
    """
    Destroy a channel. Compatibility wrapper for Evennia 5.0.
    Uses the new CmdChannel /destroy subcommand internally.
    """

    key = "@cdestroy"
    aliases = ["cdestroy"]
    locks = "cmd:perm(Builder)"
    help_category = "Comms"

    def __init__(self):
        # Set the actual parent class at runtime
        CmdChannel = _get_cmd_channel()
        COMMAND_DEFAULT_CLASS = _get_command_class()
        # Create a dynamic class that inherits from the right parent
        self.__class__ = type('CmdCdestroyImpl', (COMMAND_DEFAULT_CLASS,), dict(CmdCdestroy.__dict__))

    def func(self):
        """Destroy a channel."""
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: @cdestroy <channelname>")
            return

        # Use the new channel command's destroy functionality
        from evennia.comms.models import ChannelDB

        channel = ChannelDB.objects.channel_search(args)
        if not channel:
            caller.msg(f"Channel '{args}' not found.")
            return
        channel = channel[0]

        if not channel.access(caller, "control"):
            caller.msg("You don't have permission to destroy this channel.")
            return

        channel.delete()
        caller.msg(f"Channel '{args}' has been destroyed.")


class CmdChannelCreate(_CompatCommandMixin):
    """
    Create a new channel. Compatibility wrapper for Evennia 5.0.
    """

    key = "@ccreate"
    aliases = ["ccreate", "channelcreate"]
    locks = "cmd:perm(Builder)"
    help_category = "Comms"

    def func(self):
        """Create a channel."""
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: @ccreate <channelname>[;alias;alias...][ = description]")
            return

        # Parse arguments
        if "=" in args:
            name_part, desc = [part.strip() for part in args.split("=", 1)]
        else:
            name_part = args
            desc = ""

        from evennia.utils import create

        # Create the channel
        channel = create.create_channel(name_part, desc=desc)
        if channel:
            caller.msg(f"Created channel '{channel.key}'.")
        else:
            caller.msg(f"Failed to create channel '{name_part}'.")


class CmdChannels(_CompatCommandMixin):
    """
    List all channels. Compatibility wrapper for Evennia 5.0.
    """

    key = "@channels"
    aliases = ["channels", "@clist", "clist", "comlist"]
    locks = "cmd:all()"
    help_category = "Comms"

    def func(self):
        """List channels."""
        from evennia.comms.models import ChannelDB

        caller = self.caller

        # Get all channels
        all_channels = ChannelDB.objects.get_all_channels()

        # Get subscribed channels
        subscribed = ChannelDB.objects.get_subscriptions(caller)

        # Format output
        if not all_channels:
            caller.msg("No channels available.")
            return

        string = "Available Channels:\n"
        for channel in all_channels:
            if channel in subscribed:
                string += f"  [X] {channel.key}"
            else:
                string += f"  [ ] {channel.key}"
            if channel.desc:
                string += f" - {channel.desc}"
            string += "\n"

        caller.msg(string)


class CmdClock(_CompatCommandMixin):
    """
    Lock a channel. Compatibility wrapper for Evennia 5.0.
    """

    key = "@clock"
    aliases = ["clock", "channellock"]
    locks = "cmd:perm(Builder)"
    help_category = "Comms"

    def func(self):
        """Lock a channel."""
        caller = self.caller
        args = self.args.strip()

        if not args or "=" not in args:
            caller.msg("Usage: @clock <channel> = <lockstring>")
            return

        channel_name, lockstring = [part.strip() for part in args.split("=", 1)]

        from evennia.comms.models import ChannelDB

        channel = ChannelDB.objects.channel_search(channel_name)
        if not channel:
            caller.msg(f"Channel '{channel_name}' not found.")
            return
        channel = channel[0]

        if not channel.access(caller, "control"):
            caller.msg("You don't have permission to lock this channel.")
            return

        try:
            channel.locks.add(lockstring)
            caller.msg(f"Lock added to channel '{channel.key}'.")
        except Exception as e:
            caller.msg(f"Error setting lock: {e}")


class CmdCBoot(_CompatCommandMixin):
    """
    Boot a user from a channel. Compatibility wrapper for Evennia 5.0.
    """

    key = "@cboot"
    aliases = ["cboot", "channelboot"]
    locks = "cmd:perm(Builder)"
    help_category = "Comms"

    def func(self):
        """Boot user from channel."""
        caller = self.caller
        args = self.args.strip()

        if not args or "=" not in args:
            caller.msg("Usage: @cboot <channel> = <user>")
            return

        channel_name, username = [part.strip() for part in args.split("=", 1)]

        from evennia.comms.models import ChannelDB
        from evennia.accounts.models import AccountDB

        channel = ChannelDB.objects.channel_search(channel_name)
        if not channel:
            caller.msg(f"Channel '{channel_name}' not found.")
            return
        channel = channel[0]

        if not channel.access(caller, "control"):
            caller.msg("You don't have permission to boot from this channel.")
            return

        account = AccountDB.objects.filter(username__iexact=username).first()
        if not account:
            caller.msg(f"Account '{username}' not found.")
            return

        channel.disconnect(account)
        caller.msg(f"Booted '{username}' from channel '{channel.key}'.")


class CmdCdesc(_CompatCommandMixin):
    """
    Set channel description. Compatibility wrapper for Evennia 5.0.
    """

    key = "@cdesc"
    aliases = ["cdesc", "channeldesc"]
    locks = "cmd:perm(Builder)"
    help_category = "Comms"

    def func(self):
        """Set channel description."""
        caller = self.caller
        args = self.args.strip()

        if not args or "=" not in args:
            caller.msg("Usage: @cdesc <channel> = <description>")
            return

        channel_name, desc = [part.strip() for part in args.split("=", 1)]

        from evennia.comms.models import ChannelDB

        channel = ChannelDB.objects.channel_search(channel_name)
        if not channel:
            caller.msg(f"Channel '{channel_name}' not found.")
            return
        channel = channel[0]

        if not channel.access(caller, "control"):
            caller.msg("You don't have permission to describe this channel.")
            return

        channel.desc = desc
        channel.save()
        caller.msg(f"Description set for channel '{channel.key}'.")


class CmdAllCom(_CompatCommandMixin):
    """
    Turn all channels on or off. Compatibility wrapper for Evennia 5.0.
    """

    key = "allcom"
    aliases = ["allchannels"]
    locks = "cmd:all()"
    help_category = "Comms"

    def func(self):
        """Turn all channels on/off."""
        from evennia.comms.models import ChannelDB

        caller = self.caller
        args = self.args.strip().lower()

        if args not in ("on", "off", ""):
            caller.msg("Usage: allcom [on|off]")
            return

        channels = ChannelDB.objects.get_all_channels()

        if args == "on":
            for channel in channels:
                if channel.access(caller, "listen"):
                    channel.connect(caller)
            caller.msg("All channels turned on.")
        elif args == "off":
            for channel in channels:
                if channel.access(caller, "listen"):
                    channel.disconnect(caller)
            caller.msg("All channels turned off.")
        else:
            # Show status
            subscribed = ChannelDB.objects.get_subscriptions(caller)
            string = "Channel Status:\n"
            for channel in channels:
                if channel.access(caller, "listen"):
                    if channel in subscribed:
                        string += f"  [X] {channel.key}\n"
                    else:
                        string += f"  [ ] {channel.key}\n"
            caller.msg(string)


class CmdCWho(_CompatCommandMixin):
    """
    Show who is on a channel. Compatibility wrapper for Evennia 5.0.
    """

    key = "@cwho"
    aliases = ["cwho", "channelwho"]
    locks = "cmd:all()"
    help_category = "Comms"

    def func(self):
        """Show who is on a channel."""
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: @cwho <channel>")
            return

        from evennia.comms.models import ChannelDB

        channel = ChannelDB.objects.channel_search(args)
        if not channel:
            caller.msg(f"Channel '{args}' not found.")
            return
        channel = channel[0]

        if not channel.access(caller, "listen"):
            caller.msg("You don't have access to this channel.")
            return

        subscribers = channel.subscriptions.all()
        if not subscribers:
            caller.msg(f"No subscribers on channel '{channel.key}'.")
            return

        string = f"Subscribers on '{channel.key}':\n"
        for subscriber in subscribers:
            string += f"  {subscriber}\n"
        caller.msg(string)


def find_channel(caller, channelname):
    """
    Helper function to find a channel.
    This replaces the old find_channel from evennia.commands.default.comms
    """
    from evennia.comms.models import ChannelDB

    channel = ChannelDB.objects.channel_search(channelname)
    if not channel:
        return None
    return channel[0]


# Lazy-loaded aliases for backward compatibility
# These will be replaced with actual CmdChannel when first accessed
def _create_cmd_channel_alias():
    """Create an alias class that wraps CmdChannel."""
    CmdChannel = _get_cmd_channel()

    class CmdAddCom(CmdChannel):
        """Alias for addcom - uses CmdChannel."""
        pass

    class CmdDelCom(CmdChannel):
        """Alias for delcom - uses CmdChannel."""
        pass

    class CmdCemit(CmdChannel):
        """Alias for cemit - uses CmdChannel."""
        pass

    return CmdAddCom, CmdDelCom, CmdCemit


# Module-level cache for the lazy-loaded classes
_cmd_channel_aliases = None


def __getattr__(name):
    """Lazy load CmdAddCom, CmdDelCom, CmdCemit when first accessed."""
    global _cmd_channel_aliases

    if name in ('CmdAddCom', 'CmdDelCom', 'CmdCemit'):
        if _cmd_channel_aliases is None:
            _cmd_channel_aliases = _create_cmd_channel_alias()

        if name == 'CmdAddCom':
            return _cmd_channel_aliases[0]
        elif name == 'CmdDelCom':
            return _cmd_channel_aliases[1]
        elif name == 'CmdCemit':
            return _cmd_channel_aliases[2]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")