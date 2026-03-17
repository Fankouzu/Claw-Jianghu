"""
Commands that are available from the connect screen.
"""
import requests

from django.conf import settings
from evennia.accounts.models import AccountDB
from evennia.server.models import ServerConfig

from evennia.utils import create, utils, ansi
from commands.base import ArxCommand
from dns.resolver import query, NXDOMAIN


MULTISESSION_MODE = settings.MULTISESSION_MODE
CONNECTION_SCREEN_MODULE = settings.CONNECTION_SCREEN_MODULE
CONNECTION_SCREEN = ""
try:
    CONNECTION_SCREEN = ansi.parse_ansi(
        utils.string_from_module(CONNECTION_SCREEN_MODULE)
    )
except (AttributeError, TypeError, ValueError):
    pass
if not CONNECTION_SCREEN:
    CONNECTION_SCREEN = (
        "\n江湖：连接屏幕模块错误（随机选取的连接屏幕"
        "变量不是字符串）。\n输入 'help' 获取帮助。"
    )

GUEST = "typeclasses.guest.Guest"


class CmdGuestConnect(ArxCommand):
    """
    Logs in a guest character to the game.

    Will search for available already created guests to
    see if any are not currently logged in. If one is available,
    log in the player as that guest. If none are available,
    create a new guest account.
    """

    key = "guest"

    def dc_session(self, msg):
        session = self.caller
        session.msg(msg)
        session.sessionhandler.disconnect(session, "再见！正在断开连接。")

    def func(self):
        """
        Guest is a child of Player typeclass.
        """
        session = self.caller
        num_guests = 1
        playerlist = AccountDB.objects.typeclass_search(GUEST)
        guest = None
        bans = ServerConfig.objects.conf("server_bans")
        addr = session.address
        if bans and (any(tup[2].match(session.address) for tup in bans if tup[2])):
            # this is a banned IP or name!
            string = (
                "{r您已被封禁，无法从此处继续。"
                "\n如您认为此封禁有误，请邮件联系管理员。{x"
            )
            self.dc_session(string)
            return
        try:
            check_vpn = settings.CHECK_VPN
        except AttributeError:
            check_vpn = False
        if check_vpn:
            # check if IP is in our whitelist
            white_list = ServerConfig.objects.conf("white_list") or []
            if addr not in white_list:
                qname = (
                    addr[::-1]
                    + "."
                    + str(settings.TELNET_PORTS[0])
                    + "."
                    + settings.TELNET_INTERFACES[0][::-1]
                )
                try:
                    query(qname)
                    msg = "抱歉，不允许来自 TOR 的访客连接。"
                    self.dc_session(msg)
                    return
                except NXDOMAIN:
                    # not inside TOR
                    pass
                api_key = getattr(settings, "HOST_BLOCKER_API_KEY", "")
                url = "http://tools.xioax.com/networking/v2/json/%s/%s" % (
                    addr,
                    api_key,
                )
                try:
                    response = requests.get(url=url)
                    data = response.json()
                    print("Returned from xiaox: %s" % str(data))
                    if data["host-ip"]:
                        self.dc_session(
                            "抱歉，不允许来自 VPN 的访客连接。"
                        )
                        return
                    # the address was safe, add it to our white_list
                    white_list.append(addr)
                    ServerConfig.objects.conf("white_list", white_list)
                except Exception as err:
                    import traceback

                    traceback.print_exc()
                    print("Error code on trying to check VPN:", err)
        for pc in playerlist:
            if pc.is_guest():
                # add session check just to be absolutely sure we don't connect to a guest in-use
                if pc.is_connected or pc.sessions.all():
                    num_guests += 1
                else:
                    guest = pc
                    break
        # create a new guest account
        if not guest:
            session.msg("所有访客都在使用中，正在创建新访客。")
            key = "Guest" + str(num_guests)
            playerlist = [ob.key for ob in playerlist]
            while key in playerlist:
                num_guests += 1
                key = "Guest" + str(num_guests)
                # maximum loop check just in case
                if num_guests > 5000:
                    break
            guest = create.create_account(
                key,
                "guest@guest.com",
                "DefaultGuestPassword",
                typeclass=GUEST,
                is_superuser=False,
                locks=None,
                permissions="Guests",
                report_to=session,
            )
        # now connect the player to the guest account
        session.msg("正在以 %s 身份登录" % guest.key)
        session.sessionhandler.login(session, guest)


class CmdUnconnectedHelp(ArxCommand):
    """
    This is an unconnected version of the help command,
    for simplicity. It shows a pane of info.
    """

    key = "help"
    aliases = ["h", "?"]
    locks = "cmd:all()"

    def func(self):
        """Shows help"""

        string = """
您尚未登录游戏。此时可用的命令：
  {wconnect, guest, look, help, quit{n

要登录系统，您需要执行以下操作之一：

{w1){n 如果您没有账户，必须以访客身份登录。

     {wguest{n

     访客会自动进入访客频道，您可以输入 {wguest <消息>{n 寻求帮助。
     然后可以申请扮演 {w@roster{n 上的已有角色，或使用 {w@charcreate{n 命令
     创建新角色。如果您的申请获批，系统将发送邮件告知您密码。

{w2){n 如果您已有账户，请使用 'connect' 命令：

     {wconnect 小龙女 wugong32{n

     如果您的密码是 wugong32。如果您刚创建或申请了角色，
     密码会发送到您申请时使用的邮箱。

   登录后再次运行 {whelp{n 可获取更多帮助。祝您游戏愉快！

您可以使用 {wlook{n 命令再次查看连接屏幕。
"""
        self.msg(string)
