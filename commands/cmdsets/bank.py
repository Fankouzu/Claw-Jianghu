"""
Commands for banking.
银号相关命令。
"""

from django.utils.translation import gettext as _
from evennia.commands.cmdset import CmdSet
from evennia.utils import evtable
from commands.base import ArxCommand
from world.crafting.models import OwnedMaterial
from world.dominion import setup_utils
from world.dominion.models import AccountTransaction, AssetOwner


class BankCmdSet(CmdSet):
    """CmdSet for a market."""

    key = "BankCmdSet"
    priority = 101
    duplicates = False
    no_exits = False
    no_objs = False

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        Note that it can also take other cmdsets as arguments, which will
        be used by the character default cmdset to add all of these onto
        the internal cmdset stack. They will then be able to removed or
        replaced as needed.
        """
        self.add(CmdBank())


class CmdBank(ArxCommand):
    """
    bank
    Usage:
        bank
        bank/deposit  <amount>[=<account holder name>]
        bank/withdraw <amount>[=<account holder name>]
        bank/depositmats <type>,<amt>=<account holder name>
        bank/withdrawmats <type>,<amt>=<account holder name>
        bank/withdrawres <type>,<amt>=<account holder name>
        bank/depositres <type>,<amt>=<account holder name>
        bank/payments
        bank/payments <sender>,<amt>=<receiver>
        bank/endpayment <#>
        bank/adjustpayment <#>=<new amount>

    Used to interact with your bank account. You may deposit or
    withdraw money from your own account or any organization for
    which you have 'withdraw' permissions. You may deposit or
    withdraw materials from an organization's vault. You may also
    set up or end weekly payments to or from another entity.
    """

    key = "bank"
    aliases = ["+bank"]
    locks = "cmd:all()"
    help_category = "Bank"

    def match_account(self, all_accounts, matchstr=None):
        """Get the account matching self.rhs"""
        name = matchstr or self.rhs or ""
        name = name.lower()
        matches = [ob for ob in all_accounts if str(ob.owner).lower() == name]
        if not matches:
            self.msg(
                _("未找到匹配。请选择： %s")
                % ", ".join(str(ob.owner) for ob in all_accounts)
            )
            return
        return matches[0]

    @staticmethod
    def get_debt_table(debts):
        x = 0
        table = evtable.EvTable(
            "{w编号{n",
            "{w收款方{n",
            "{w金额{n",
            "{w剩余期数{n",
            width=60,
            align="r",
        )
        for debt in debts:
            x += 1
            time = _("永久") if debt.repetitions_left == -1 else debt.repetitions_left
            table.add_row(
                debt.id, debt.receiver, "{:,}".format(debt.weekly_amount), time
            )
        return table

    @staticmethod
    def check_money(account, amt):
        debits = 0
        for debt in account.debts.all():
            debits += debt.weekly_amount
        debits += amt
        return account.vault - debits

    def inform_owner(self, owner, verb, amt, attr_type="silver", mat_str="silver"):
        attr_name = "min_%s_for_inform" % attr_type
        if amt >= getattr(owner, attr_name):
            preposition = _("存入") if "deposit" in verb.lower() else _("取出")
            msg = _("%s 已从 %s 的账户中%s %s %s。") % (
                self.caller, owner, verb, amt, mat_str
            )
            owner.inform(msg, category="Bank Transaction")

    def func(self):
        """Execute command."""
        caller = self.caller
        try:
            dompc = caller.player.Dominion
        except AttributeError:
            dompc = setup_utils.setup_dom_for_char(caller)
        org_accounts = [
            member.organization.assets
            for member in dompc.memberships.filter(deguilded=False)
        ]
        all_accounts = [dompc.assets] + org_accounts
        if (
            "payments" in self.switches
            or "endpayment" in self.switches
            or "adjustpayment" in self.switches
            or "payment" in self.switches
        ):
            debts = list(dompc.assets.debts.all())
            for acc in org_accounts:
                if acc.can_be_viewed_by(caller) and acc.debts.all():
                    debts += list(acc.debts.all())
            if not self.args:
                caller.msg(str(self.get_debt_table(debts)), options={"box": True})
                return
            if "endpayment" in self.switches or "adjustpayment" in self.switches:
                try:
                    if "endpayment" in self.switches:
                        debts += list(dompc.assets.incomes.all())
                    val = int(self.lhs)
                    debt = AccountTransaction.objects.get(
                        id=val, id__in=(ob.id for ob in debts)
                    )
                except (ValueError, AccountTransaction.DoesNotExist):
                    caller.msg(_("无效编号，请选择："))
                    caller.msg(str(self.get_debt_table(debts)), options={"box": True})
                    return
                if "endpayment" in self.switches:
                    debt.delete()
                    caller.msg(_("定期支付已取消。"))
                    return
                try:
                    amt = int(self.rhs)
                    if amt <= 0:
                        raise ValueError
                except ValueError:
                    caller.msg(_("请输入正数作为新金额。"))
                    return
                check = self.check_money(debt.sender, (amt - debt.weekly_amount))
                if check < 0:
                    caller.msg(_("余额不足，还需 %s 银两。") % (-check))
                    return
                debt.weekly_amount = amt
                debt.save()
                caller.msg(_("每周支付金额已改为 %s。") % amt)
                return
            # set up a new payment
            try:
                sender = self.match_account(all_accounts, self.lhslist[0])
                if not sender:
                    return
                if not sender.access(caller, "withdraw"):
                    caller.msg(_("你没有权限设置定期支付。"))
                    return
                amt = int(self.lhslist[1])
                if amt <= 0:
                    raise ValueError
                try:
                    receiver = AssetOwner.objects.get(
                        player__player__username__iexact=self.rhs
                    )
                except AssetOwner.DoesNotExist:
                    receiver = AssetOwner.objects.get(
                        organization_owner__name__iexact=self.rhs
                    )
                if sender == receiver:
                    caller.msg(_("付款方和收款方不能相同。"))
                    return
            except (ValueError, IndexError):
                caller.msg(_("金额必须为正数。"))
                return
            except (AssetOwner.DoesNotExist, AssetOwner.MultipleObjectsReturned):
                caller.msg(_("未找到该名称的玩家或帮派。"))
                return
            check = self.check_money(sender, amt)
            if check < 0:
                caller.msg(
                    _("余额不足，还需 %s 银两才能设置定期支付。")
                    % (-check)
                )
                return
            sender.debts.create(
                receiver=receiver, weekly_amount=amt, repetitions_left=-1
            )
            caller.msg(
                _("已设置每周定期支付： %s 每周支付 %s 银两给 %s。")
                % (sender, amt, receiver)
            )
            return
        if not self.args:
            msg = "{w账户{n".center(60)
            msg += "\n"
            actable = evtable.EvTable(
                "{w户主{n",
                "{w余额{n",
                "{w净收入{n",
                "{w材料{n",
                "{w经济{n",
                "{w社会{n",
                "{w军事{n",
                width=78,
                border="cells",
            )

            for account in all_accounts:
                if not account.can_be_viewed_by(self.caller):
                    continue
                mats = ", ".join(
                    str(mat) for mat in account.owned_materials.filter(amount__gte=1)
                )
                actable.add_row(
                    str(account.owner),
                    str(account.vault),
                    str(account.net_income),
                    mats,
                    account.economic,
                    account.social,
                    account.military,
                )
                actable.reformat_column(0, width=14)
                actable.reformat_column(1, width=11)
                actable.reformat_column(2, width=10)
                actable.reformat_column(3, width=21)
                actable.reformat_column(4, width=8)
                actable.reformat_column(5, width=7)
                actable.reformat_column(6, width=7)
                incomes = account.incomes.all()
                debts = account.debts.all()
                if incomes:
                    msg += ("{w%s 收入{n" % str(account)).center(60)
                    msg += "\n"
                    table = evtable.EvTable(
                        "{w付款方{n",
                        "{w金额{n",
                        "{w剩余期数{n",
                        width=60,
                        align="r",
                    )
                    for inc in incomes:
                        time = (
                            _("永久")
                            if inc.repetitions_left == -1
                            else inc.repetitions_left
                        )
                        table.add_row(
                            inc.sender, "{:,}".format(inc.weekly_amount), time
                        )
                    msg += str(table)
                    msg += "\n"
                if debts:
                    msg += ("{w%s 定期支付{n" % str(account)).center(60)
                    msg += "\n"
                    msg += str(self.get_debt_table(debts))
                    msg += "\n"
            msg += str(actable)
            caller.msg(msg, options={"box": True})
            return
        if (
            "depositmats" in self.switches
            or "withdrawmats" in self.switches
            or "depositres" in self.switches
            or "withdrawres" in self.switches
        ):
            account = self.match_account(all_accounts)
            if not account:
                return
            if account == dompc.assets:
                caller.msg(
                    _("角色随时可取用自己的材料，存取仅用于帮派与角色之间。")
                )
                return
            usingmats = (
                "depositmats" in self.switches or "withdrawmats" in self.switches
            )
            if usingmats:
                attr_type = "materials"
            else:
                attr_type = "resources"
            if "depositmats" in self.switches or "depositres" in self.switches:
                sender = dompc.assets
                receiver = account
                verb = "deposit"
            else:
                if not account.access(caller, "withdraw"):
                    caller.msg(
                        _("你没有权限从该账户取款。")
                    )
                    return
                receiver = dompc.assets
                sender = account
                verb = "withdraw"
            try:
                matname, val = self.lhslist[0], int(self.lhslist[1])
                source = sender
                targ = receiver
                if val <= 0:
                    caller.msg(_("必须指定正数。"))
                    return
                if usingmats:
                    source = sender.owned_materials.get(type__name__iexact=matname)
                    if source.amount < val:
                        caller.msg(
                            _("你尝试%s %s %s，但仅有 %s 可用。")
                            % (verb, val, source.type.name, source.amount)
                        )
                        return
                    try:
                        targ = receiver.owned_materials.get(type__name__iexact=matname)
                    except OwnedMaterial.DoesNotExist:
                        targ = receiver.owned_materials.create(
                            type=source.type, amount=0
                        )
                    source.amount -= val
                    targ.amount += val
                    samt = source.amount
                    tamt = targ.amount
                else:
                    restypes = ("economic", "social", "military")
                    matname = matname.lower()
                    if matname not in restypes:
                        caller.msg(_("资源类型须为：%s") % ", ".join(restypes))
                        return
                    sresamt = getattr(sender, matname)
                    if sresamt < val:
                        matname += _("资源")
                        caller.msg(
                            _("你尝试%s %s %s，但仅有 %s 可用。")
                            % (verb, val, matname, sresamt)
                        )
                        return
                    tresamt = getattr(receiver, matname)
                    samt = sresamt - val
                    tamt = tresamt + val
                    setattr(sender, matname, samt)
                    setattr(receiver, matname, tamt)
                    matname += _("资源")
                source.save()
                targ.save()
                caller.msg(
                    _("你已将 %s %s 从 %s 转移至 %s。")
                    % (val, matname, sender, receiver)
                )
                if account.can_be_viewed_by(caller):
                    caller.msg(
                        _("付款方现持有 %s，收款方现持有 %s。") % (samt, tamt)
                    )
                else:
                    caller.msg(_("交易成功。"))
                self.inform_owner(account, verb, val, attr_type, matname)
            except OwnedMaterial.DoesNotExist:
                caller.msg(
                    _("未找到该材料。可用材料：%s")
                    % ", ".join(str(mat) for mat in sender.owned_materials.all())
                )
                return
            except (ValueError, IndexError):
                caller.msg(_("用法无效。"))
                return
            return
        try:
            amount = int(self.lhs)
            if amount <= 0:
                caller.msg(_("金额必须为正数。"))
                return
        except ValueError:
            caller.msg(_("金额必须为数字。"))
            return
        if not self.rhs:
            account = dompc.assets
        else:
            account = self.match_account(all_accounts)
            if not account:
                return
        if "deposit" in self.switches:
            cash = caller.item_data.currency
            if not cash:
                caller.msg(_("你身无分文，无法存入。"))
                return
            if amount > cash:
                caller.msg(
                    _("你尝试存入 %s，但仅有 %s。")
                    % (amount, cash)
                )
                return
            account.vault += amount
            caller.item_data.currency = cash - amount
            account.save()
            if account.can_be_viewed_by(caller):
                caller.msg(
                    _("你已存入 %s，新余额为 %s。")
                    % (amount, account.vault)
                )
            else:
                caller.msg(_("你已存入 %s。") % amount)
            self.inform_owner(account, "deposited", amount)
            return
        if "withdraw" in self.switches:
            if not account.access(caller, "withdraw"):
                caller.msg(_("你没有权限从该账户取款。"))
                return
            cash = caller.item_data.currency
            check = self.check_money(account, amount)
            if check < 0:
                caller.msg(
                    _("取款金额不能超过账户余额扣除定期支付义务后的数额。")
                )
                caller.msg(
                    _("你欲取款 %s，但扣除定期支付义务后仅余 %s 可用。")
                    % (amount, check + amount)
                )
                if account.debts.all():
                    caller.msg(
                        _("取消定期支付可增加可用金额。")
                    )
                    return
                return
            account.vault -= amount
            caller.item_data.currency = cash + amount
            account.save()
            caller.msg(
                _("你已取款 %s，新余额为 %s。")
                % (amount, account.vault)
            )
            self.inform_owner(account, "withdrawn", amount)
            return
        else:
            caller.msg(_("无法识别的选项。"))
            return
