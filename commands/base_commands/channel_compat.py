"""
Compatibility module for Evennia 5.0 channel commands.

In Evennia 5.0, the old separate channel commands (CmdCdestroy, CmdChannelCreate, etc.)
were consolidated into a single CmdChannel command with subcommands.

This module provides compatibility wrappers for legacy code using a factory pattern
that creates proper command classes when Evennia is ready.
"""
from django.conf import settings


def _get_command_class():
    """Lazy import to avoid circular import during Evennia initialization."""
    from evennia.utils.utils import class_from_module
    return class_from_module(settings.COMMAND_DEFAULT_CLASS)


# Cache for created command classes
_command_classes = {}


def _create_command_class(name, key, aliases, locks, help_category, func_impl, docstring=None):
    """
    Factory function to create a proper command class that inherits from Evennia's Command.

    Args:
        name: Class name
        key: Command key
        aliases: List of aliases
        locks: Lock string
        help_category: Help category
        func_impl: The func method implementation
        docstring: Optional docstring

    Returns:
        A proper Command subclass
    """
    if name in _command_classes:
        return _command_classes[name]

    CommandBase = _get_command_class()

    class_dict = {
        'key': key,
        'aliases': list(aliases) if aliases else [],
        'locks': locks,
        'help_category': help_category,
        '__doc__': docstring or f"{key} command",
        'func': func_impl,
    }

    # Create the class - this will trigger Evennia's Command metaclass
    cls = type(name, (CommandBase,), class_dict)
    _command_classes[name] = cls
    return cls


# Define command implementations
def _cmd_cdestroy_func(self):
    """Destroy a channel."""
    caller = self.caller
    args = self.args.strip()

    if not args:
        caller.msg("Usage: @cdestroy <channelname>")
        return

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


def _cmd_channel_create_func(self):
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


def _cmd_channels_func(self):
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


def _cmd_clock_func(self):
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


def _cmd_cboot_func(self):
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


def _cmd_cdesc_func(self):
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


def _cmd_allcom_func(self):
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


def _cmd_cwho_func(self):
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


# Use __getattr__ to lazily create command classes when accessed
def __getattr__(name):
    """Lazy load command classes when first accessed."""

    command_specs = {
        'CmdCdestroy': {
            'key': '@cdestroy',
            'aliases': ['cdestroy'],
            'locks': 'cmd:perm(Builder)',
            'help_category': 'Comms',
            'func': _cmd_cdestroy_func,
            'doc': 'Destroy a channel. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdChannelCreate': {
            'key': '@ccreate',
            'aliases': ['ccreate', 'channelcreate'],
            'locks': 'cmd:perm(Builder)',
            'help_category': 'Comms',
            'func': _cmd_channel_create_func,
            'doc': 'Create a new channel. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdChannels': {
            'key': '@channels',
            'aliases': ['channels', '@clist', 'clist', 'comlist'],
            'locks': 'cmd:all()',
            'help_category': 'Comms',
            'func': _cmd_channels_func,
            'doc': 'List all channels. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdClock': {
            'key': '@clock',
            'aliases': ['clock', 'channellock'],
            'locks': 'cmd:perm(Builder)',
            'help_category': 'Comms',
            'func': _cmd_clock_func,
            'doc': 'Lock a channel. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdCBoot': {
            'key': '@cboot',
            'aliases': ['cboot', 'channelboot'],
            'locks': 'cmd:perm(Builder)',
            'help_category': 'Comms',
            'func': _cmd_cboot_func,
            'doc': 'Boot a user from a channel. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdCdesc': {
            'key': '@cdesc',
            'aliases': ['cdesc', 'channeldesc'],
            'locks': 'cmd:perm(Builder)',
            'help_category': 'Comms',
            'func': _cmd_cdesc_func,
            'doc': 'Set channel description. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdAllCom': {
            'key': 'allcom',
            'aliases': ['allchannels'],
            'locks': 'cmd:all()',
            'help_category': 'Comms',
            'func': _cmd_allcom_func,
            'doc': 'Turn all channels on or off. Compatibility wrapper for Evennia 5.0.'
        },
        'CmdCWho': {
            'key': '@cwho',
            'aliases': ['cwho', 'channelwho'],
            'locks': 'cmd:all()',
            'help_category': 'Comms',
            'func': _cmd_cwho_func,
            'doc': 'Show who is on a channel. Compatibility wrapper for Evennia 5.0.'
        },
    }

    if name in command_specs:
        spec = command_specs[name]
        return _create_command_class(
            name,
            spec['key'],
            spec['aliases'],
            spec['locks'],
            spec['help_category'],
            spec['func'],
            spec['doc']
        )

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")