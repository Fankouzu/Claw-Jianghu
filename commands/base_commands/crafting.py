"""
Crafting commands. BEHOLD THE MINIGAME.
炼制命令。
"""
from django.conf import settings
from django.db.models import Q, Prefetch
from django.utils.translation import gettext as _

from commands.base import ArxCommand
from evennia.utils import utils
from evennia.utils.utils import make_iter
from server.utils.arx_utils import validate_name, inform_staff
from server.utils.prettytable import PrettyTable
from world.crafting.models import (
    CraftingRecipe,
    OwnedMaterial,
    CraftingMaterialType,
)
from world.dominion.models import (
    AssetOwner,
    PlayerOrNpc,
)
from world.dominion.setup_utils import setup_dom_for_char
from world.stats_and_skills import do_dice_check
from world.templates.mixins import TemplateMixins

AT_SEARCH_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit(".", 1))

WIELD = "typeclasses.wearable.wieldable.Wieldable"
DECORATIVE_WIELD = "typeclasses.wearable.decorative_weapon.DecorativeWieldable"
WEAR = "typeclasses.wearable.wearable.Wearable"
PLACE = "typeclasses.places.places.Place"
BOOK = "typeclasses.readable.readable.Readable"
CONTAINER = "typeclasses.containers.container.Container"
WEARABLE_CONTAINER = "typeclasses.wearable.wearable.WearableContainer"
BAUBLE = "typeclasses.bauble.Bauble"
PERFUME = "typeclasses.consumable.perfume.Perfume"
MASK = "typeclasses.disguises.disguises.Mask"

QUALITY_LEVELS = {
    0: "{r拙劣{n",
    1: "{m平庸{n",
    2: "{c寻常{n",
    3: "{c中上{n",
    4: "{y精良{n",
    5: "{y上乘{n",
    6: "{g卓越{n",
    7: "{g绝品{n",
    8: "{g神工{n",
    9: "{454完美{n",
    10: "{553天工{n",
    11: "|355化境|n",
}


def create_weapon(recipe, roll, proj, caller, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(WIELD, proj[1], caller, caller, quality, crafter)
    return obj, quality


def create_wearable(recipe, roll, proj, caller, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(WEAR, proj[1], caller, caller, quality, crafter)
    return obj, quality


def create_decorative_weapon(recipe, roll, proj, caller, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(DECORATIVE_WIELD, proj[1], caller, caller, quality, crafter)
    return obj, quality


def create_place(recipe, roll, proj, caller, crafter):
    scaling = float(recipe.scaling)
    base = int(recipe.base_value or 2)
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(PLACE, proj[1], caller, caller, quality, crafter)
    obj.item_data.max_spots = base + int(scaling * quality)
    return obj, quality


def create_container(recipe, roll, proj, caller, crafter):
    scaling = float(recipe.scaling)
    base = int(recipe.base_value or 2)
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(CONTAINER, proj[1], caller, caller, quality, crafter)
    obj.item_data.capacity = base + int(scaling * quality)
    try:
        obj.grant_key(caller)
    except (TypeError, AttributeError, ValueError):
        import traceback

        traceback.print_exc()
    return obj, quality


def create_wearable_container(recipe, roll, proj, caller, crafter):
    scaling = float(recipe.scaling)
    base = int(recipe.base_value or 2)
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(
        WEARABLE_CONTAINER, proj[1], caller, caller, quality, crafter
    )
    obj.item_data.capacity = base + int(scaling * quality)
    try:
        obj.grant_key(caller)
    except (TypeError, AttributeError, ValueError):
        import traceback

        traceback.print_exc()
    return obj, quality


def create_generic(recipe, roll, proj, caller, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(BAUBLE, proj[1], caller, caller, quality, crafter)
    return obj, quality


def create_consumable(recipe, roll, proj, caller, typeclass, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(typeclass, proj[1], caller, caller, quality, crafter)
    return obj, quality


def create_mask(recipe, roll, proj, caller, maskdesc, crafter):
    quality = get_quality_lvl(roll, recipe.difficulty)
    obj = recipe.create_obj(MASK, proj[1], caller, caller, quality, crafter)
    obj.item_data.mask_desc = maskdesc
    return obj, quality


def get_ability_val(char, recipe):
    """
    Returns a character's highest rank in any ability used in the
    recipe.
    """
    ability_list = (recipe.ability or "").split(",")
    abilities = char.traits.abilities
    skills = char.traits.skills
    if recipe.skill == "artwork":
        return char.traits.get_skill_value("artwork")
    if ability_list == "all" or not ability_list:
        # get character's highest ability
        values = sorted(abilities.values() + [skills.get("artwork", 0)], reverse=True)
        ability = values[0]
    else:
        abvalues = []
        for abname in ability_list:
            abvalues.append(abilities.get(abname, 0))
        ability = sorted(abvalues, reverse=True)[0]
    return ability


def get_highest_crafting_skill(character):
    """Returns the highest crafting skill for character"""
    from world.traits.models import Trait

    skills = character.traits.skills
    return max(
        Trait.get_valid_skill_names(Trait.CRAFTING) + ["artwork"],
        key=lambda x: skills.get(x, 0),
    )


def do_crafting_roll(char, recipe, diffmod=0, diffmult=1.0, room=None):
    diff = int(recipe.difficulty * diffmult) - diffmod
    ability = get_ability_val(char, recipe)
    skill = recipe.skill
    if skill in ("all", "any"):
        skill = get_highest_crafting_skill(char)
    stat = "luck" if char.traits.luck > char.traits.dexterity else "dexterity"
    can_crit = False
    try:
        if char.roster.roster.name == "Active":
            can_crit = True
    except AttributeError:
        pass
    # use real name if we're not present (someone using our shop, for example). If we're here, use masked name
    real_name = char.location != room
    return do_dice_check(
        char,
        stat=stat,
        difficulty=diff,
        skill=skill,
        bonus_dice=ability,
        quiet=False,
        announce_room=room,
        can_crit=can_crit,
        use_real_name=real_name,
    )


def get_difficulty_mod(recipe, money=0, action_points=0, ability=0):
    from random import randint

    divisor = recipe.value or 0
    if divisor < 1:
        divisor = 1
    val = float(money) / float(divisor)
    # for every 10% of the value of recipe we invest, we knock 1 off difficulty
    val = int(val / 0.10) + 1
    if action_points:
        base = action_points // (14 - (2 * ability))
        val += randint(int(base), int(action_points))
    return val


def get_quality_lvl(roll, diff):
    # roll was against difficulty, so add it for comparison
    roll += diff
    if roll < diff / 4:
        return 0
    if roll < (diff * 3) / 4:
        return 1
    if roll < diff * 1.2:
        return 2
    if roll < diff * 1.6:
        return 3
    if roll < diff * 2:
        return 4
    if roll < diff * 2.5:
        return 5
    if roll < diff * 3.5:
        return 6
    if roll < diff * 5:
        return 7
    if roll < diff * 7:
        return 8
    if roll < diff * 10:
        return 9
    return 10


class CmdCraft(ArxCommand, TemplateMixins):
    """
    Crafts an object

    Usage:
        craft
        craft <recipe name>
        craft/name <name>
        craft/desc <description>
        craft/altdesc <description>
        craft/adorn <material type>=<amount>
        craft/translated_text <language>=<text>
        craft/preview [<player>]
        craft/finish [<additional silver to invest>, <action points>
        craft/abandon
        craft/refine <object>[=<additional silver to spend>, <action points>]
        craft/changename <object>=<new name>
        craft/addadorn <object>=<material type>,<amount>

    To start crafting, you must know recipes related to your crafting profession.
    Select a recipe then describe the object with /name and /desc. To add extra
    materials such as gemstones, use /adorn. No materials or silver are used
    until you are ready to /finish the project and make the roll for its quality.

    For things such as perfume, the desc is the description that appears on the
    character, not a description of the bottle. When crafting masks, the name is
    used to identify its wearer: "A Fox Mask" will bestow "Someone wearing A Fox
    Mask" upon its wearer, and the altdesc switch is used for their temporary
    description. For any desc, ascii can be enclosed in <ascii> tags that
    will note to not display them to screenreaders. Use <ascii> and <ascii/> with
    the desc between the opening and closing tags.

    If the item should contain words in a foreign tongue that you know, use
    translated_text to display what the translated words actually say.

    To finish a project, use /finish, or /abandon if you wish to stop and do
    something else. To attempt to change the quality level of a finished object,
    use /refine. Refinement cost is based on how much it took to create, and
    can never make the object worse. Use /addadorn to embellish an item with
    extra materials post-creation.

    Craft with no arguments will display the status of a current project.
    """

    key = "craft"
    locks = "cmd:all()"
    help_category = "Crafting"
    crafter = None
    crafting_switches = (
        "name",
        "desc",
        "altdesc",
        "adorn",
        "translated_text",
        "forgery",
        "finish",
        "abandon",
        "refine",
        "changename",
        "addadorn",
        "preview",
    )

    def get_refine_price(self, base):
        return 0

    def get_recipe_price(self, recipe):
        return 0

    def pay_owner(self, price, msg):
        return

    def display_project(self, proj):
        """
        Project is a list of data related to what a character
        is crafting. (recipeid, name, desc, adorns, forgerydict)
        """
        caller = self.caller
        dompc = caller.player_ob.Dominion
        recipe = CraftingRecipe.objects.get(id=proj[0])
        msg = "{w配方：{n %s\n" % recipe.name
        msg += "{w名称：{n %s\n" % proj[1]
        msg += "{w描述：{n %s\n" % proj[2]
        if len(proj) > 6 and proj[6]:
            msg += "{w伪装描述：{n %s\n" % proj[6]
        adorns, forgery = proj[3], proj[4]
        if adorns:
            msg += "{w镶嵌材料：{n %s\n" % ", ".join(
                "%s: %s" % (CraftingMaterialType.objects.get(id=mat).name, amt)
                for mat, amt in adorns.items()
            )
        if forgery:
            msg += "{w伪造：{n %s\n" % ", ".join(
                "%s 充作 %s"
                % (
                    CraftingMaterialType.objects.get(id=value).name,
                    CraftingMaterialType.objects.get(id=key).name,
                )
                for key, value in forgery.items()
            )
        try:
            translation = proj[5]
            if translation:
                msg += "{w译文：{n %s\n" % "\n\n".join(
                    "%s:\n%s" % (lang, text) for lang, text in translation.items()
                )
        except IndexError:
            pass
        caller.msg(msg)
        caller.msg("{w完成炼制需准备以下材料，使用 /finish 命令：{n")
        caller.msg(recipe.display_reqs(dompc))

    def check_max_invest(self, recipe, invest):
        if invest > recipe.value:
            self.msg(_("你最多只能投入 %s 银两。") % recipe.value)
            return
        return True

    def func(self):
        """Implement the command"""
        caller = self.caller
        if not self.crafter:
            self.crafter = caller
        crafter = self.crafter
        try:
            dompc = PlayerOrNpc.objects.get(player=caller.player)
            assets = AssetOwner.objects.get(player=dompc)
        except PlayerOrNpc.DoesNotExist:
            # dominion not set up on player
            dompc = setup_dom_for_char(caller)
            assets = dompc.assets
        except AssetOwner.DoesNotExist:
            # assets not initialized on player
            dompc = setup_dom_for_char(caller, create_dompc=False)
            assets = dompc.assets
        recipes = crafter.player_ob.Dominion.assets.crafting_recipes.all()
        if not self.args and not self.switches:
            # display recipes and any crafting project we have unfinished
            materials = assets.owned_materials.all()
            caller.msg(
                "{w已习得配方：{n %s"
                % ", ".join(recipe.name for recipe in recipes)
            )
            caller.msg(
                "{w持有材料：{n %s" % ", ".join(str(mat) for mat in materials)
            )
            project = caller.db.crafting_project
            if project:
                self.display_project(project)
            return
        # start a crafting project
        if not self.switches or "craft" in self.switches:
            try:
                recipe = recipes.get(name__iexact=self.lhs)
            except CraftingRecipe.DoesNotExist:
                caller.msg(_("寻不得名为 %s 的配方。") % self.lhs)
                return
            try:
                self.get_recipe_price(recipe)
            except ValueError:
                caller.msg(_("该配方未定义价格。"))
                return
            # proj = [id, name, desc, adorns, forgery, translation]
            proj = [recipe.id, "", "", {}, {}, {}, ""]
            caller.db.crafting_project = proj
            stmsg = "你已" if caller == crafter else "%s已" % crafter
            caller.msg("{w%s开始炼制：{n %s。" % (stmsg, recipe.name))
            caller.msg("{w完成炼制需准备以下材料，使用 /finish 命令：{n")
            caller.msg(recipe.display_reqs(dompc))
            return
        if (
            "changename" in self.switches
            or "refine" in self.switches
            or "addadorn" in self.switches
        ):
            targ = caller.search(self.lhs, location=caller)
            if not targ:
                return
            recipe = None
            try:
                recipe = targ.item_data.recipe
            except AttributeError:
                pass
            if not recipe:
                caller.msg(_("该物品无配方记录。"))
                return
            if "changename" in self.switches:
                if not self.rhs:
                    self.msg(_("用法：/changename <物品>=<新名称"))
                    return
                if not validate_name(self.rhs):
                    caller.msg(_("名称无效。"))
                    return
                if targ.tags.get("plot"):
                    self.msg(_("此物不可更名。"))
                    return
                targ.aliases.clear()
                targ.name = self.rhs
                caller.msg(_("名称已改为 %s。") % targ)
                return
            # adding adorns post-creation
            if "addadorn" in self.switches:
                try:
                    material = self.rhslist[0]
                    amt = int(self.rhslist[1])
                    if amt < 1 and not caller.check_permstring("builders"):
                        raise ValueError
                except (IndexError, ValueError, TypeError):
                    caller.msg(_("用法：/addadorn <物品>=<材料>,<数量"))
                    return
                if not recipe.allow_adorn:
                    caller.msg(
                        _("此配方不可额外添加材料。")
                    )
                    return
                try:
                    mat = CraftingMaterialType.objects.get(name__iexact=material)
                except CraftingMaterialType.DoesNotExist:
                    self.msg(
                        _("无法使用 %s，并非炼制材料。")
                        % material
                    )
                    return
                # if caller isn't a builder, check and consume their materials
                if not caller.check_permstring("builders"):
                    pmats = caller.player.Dominion.assets.owned_materials
                    try:
                        pmat = pmats.get(type=mat)
                        if pmat.amount < amt:
                            caller.msg(
                                _("你需要 %s 份 %s，但仅有 %s 份。")
                                % (amt, mat.name, pmat.amount)
                            )
                            return
                    except OwnedMaterial.DoesNotExist:
                        caller.msg(_("你没有 %s 材料。") % mat.name)
                        return
                    pmat.amount -= amt
                    pmat.save()
                targ.item_data.add_adorn(mat, amt)
                caller.msg(
                    _("%s 已镶嵌 %s 份 %s 材料。") % (targ, amt, mat)
                )
                return
            if "refine" in self.switches:
                base_cost = recipe.value / 4
                caller.msg(_("精炼基础花费为 %s 银两。") % base_cost)
                try:
                    price = self.get_refine_price(base_cost)
                except ValueError:
                    caller.msg(_("精炼价格未设定。"))
                    return
                if price:
                    caller.msg(_("精炼额外价格为 %s 银两。") % price)
                action_points = 0
                invest = 0
                if self.rhs:
                    try:
                        invest = int(self.rhslist[0])
                        if len(self.rhslist) > 1:
                            action_points = int(self.rhslist[1])
                    except ValueError:
                        caller.msg(
                            _("投入的银两和行动点必须为数字。")
                        )
                        return
                    if invest < 0 or action_points < 0:
                        caller.msg(_("数值必须为正数。"))
                        return
                if not recipe:
                    caller.msg(_("此非炼制品，无法精炼。"))
                    return
                if targ.item_data.quality_level and targ.item_data.quality_level >= 10:
                    caller.msg(_("此物已达极致，无法再提升。"))
                    return
                ability = get_ability_val(crafter, recipe)
                if ability < recipe.level:
                    err = "你欠缺" if crafter == caller else "%s欠缺" % crafter
                    caller.msg(
                        _("%s精炼此物所需的技艺。") % err
                    )
                    return
                if not self.check_max_invest(recipe, invest):
                    return
                cost = base_cost + invest + price
                # don't display a random number when they're prepping
                if caller.ndb.refine_targ != (targ, cost):
                    diffmod = get_difficulty_mod(recipe, invest)
                else:
                    diffmod = get_difficulty_mod(recipe, invest, action_points, ability)
                # difficulty gets easier by 1 each time we attempt it
                attempts = targ.item_data.get_refine_attempts_for_character(crafter)
                if attempts > 60:
                    attempts = 60
                diffmod += attempts
                if diffmod:
                    self.msg(
                        _("根据银两消耗和尝试次数，难度调整 %s。")
                        % diffmod
                    )
                if caller.ndb.refine_targ != (targ, cost):
                    caller.ndb.refine_targ = (targ, cost)
                    caller.msg(
                        _("总花费为 {w%s{n 银两。再次执行命令以确认。")
                        % cost
                    )
                    return
                if cost > caller.item_data.currency:
                    caller.msg(
                        _("需花费 %s 银两，但你仅有 %s。")
                        % (cost, caller.item_data.currency)
                    )
                    return
                if action_points and not caller.player_ob.pay_action_points(
                    action_points
                ):
                    self.msg(_("你没有足够的行动点来精炼。"))
                    return
                # pay for it
                caller.pay_money(cost)
                self.pay_owner(
                    price,
                    _("%s 在你的店铺精炼了 '%s'（%s），你获得 %s 银两。")
                    % (caller, targ, recipe.name, price),
                )

                roll = do_crafting_roll(
                    crafter, recipe, diffmod, diffmult=0.75, room=caller.location
                )
                quality = get_quality_lvl(roll, recipe.difficulty)
                old = targ.item_data.quality_level or 0
                attempts += 1
                targ.item_data.set_refine_attempts_for_character(crafter, attempts)
                self.msg(
                    _("投骰结果 %s，品质等级 %s。")
                    % (roll, QUALITY_LEVELS[quality])
                )
                if quality <= old:
                    caller.msg(
                        _("精炼失败，%s 品质仍为 %s。")
                        % (targ, QUALITY_LEVELS[old])
                    )
                    return
                caller.msg(_("新品质等级为 %s。") % QUALITY_LEVELS[quality])
                targ.item_data.quality_level = quality
                return
        proj = caller.db.crafting_project
        if not proj:
            caller.msg(_("你当前没有炼制项目。"))
            return
        if "name" in self.switches:
            if not self.args:
                caller.msg(_("取何名称？"))
                return
            if not validate_name(self.args):
                caller.msg(_("名称无效。"))
                return
            proj[1] = self.args
            caller.db.crafting_project = proj
            caller.msg(_("名称已设为 %s。") % self.args)
            return
        if "desc" in self.switches:
            if not self.args:
                caller.msg(_("如何描述？"))
                return

            if not self.can_apply_templates(self.caller, self.args):
                return

            proj[2] = self.args
            caller.db.crafting_project = proj
            caller.msg(_("描述已设为：\n%s") % self.args)
            return
        if "abandon" in self.switches:
            caller.msg(
                _("你已放弃此炼制项目，可另起炉灶。")
            )
            caller.db.crafting_project = None
            return
        if "translated_text" in self.switches:
            if not (self.lhs and self.rhs):
                caller.msg(_("用法：craft/translated_text <语言>=<文本"))
                return
            lhs = self.lhs.lower()
            if lhs not in self.caller.languages.known_languages:
                caller.msg(_("休想欺瞒，你不会说 %s。") % self.lhs)
                return
            proj[5].update({lhs: self.rhs})
            caller.db.crafting_project = proj
            self.display_project(proj)
            return
        if "altdesc" in self.switches:
            if not self.args:
                caller.msg(_("如何描述伪装？仅用于伪装配方。"))
                return
            proj[6] = self.args
            caller.msg(
                _("此仅用于伪装配方。伪装描述已设为：\n%s")
                % self.args
            )
            return
        if "adorn" in self.switches:
            if not (self.lhs and self.rhs):
                caller.msg(_("用法：craft/adorn <材料>=<数量"))
                return
            try:
                mat = CraftingMaterialType.objects.get(name__iexact=self.lhs)
                amt = int(self.rhs)
            except CraftingMaterialType.DoesNotExist:
                caller.msg(_("无名为 %s 的材料。") % self.lhs)
                return
            except CraftingMaterialType.MultipleObjectsReturned:
                caller.msg(_("匹配多个材料，请更精确。"))
                return
            except (TypeError, ValueError):
                caller.msg(_("数量必须为数字。"))
                return
            if amt < 1:
                caller.msg(_("数量必须为正数。"))
                return
            recipe = CraftingRecipe.objects.get(id=proj[0])
            if not recipe.allow_adorn:
                caller.msg(
                    _("此配方不可额外添加材料。")
                )
                return
            adorns = proj[3] or {}
            adorns[mat.id] = amt
            proj[3] = adorns
            caller.db.crafting_project = proj
            caller.msg(
                _("额外材料：%s")
                % ", ".join(
                    "%s: %s" % (CraftingMaterialType.objects.get(id=mat).name, amt)
                    for mat, amt in adorns.items()
                )
            )
            return
        if "forgery" in self.switches:
            self.msg(_("暂时停用，待日后重修。"))
            return
        if "preview" in self.switches:
            if self.args:
                viewer = self.caller.player.search(self.args)
                if not viewer:
                    return
                viewer.msg(
                    _("{c%s{n 正与你分享炼制项目的预览。")
                    % self.caller
                )
                self.msg(
                    _("你与 %s 分享了炼制项目的预览。") % viewer
                )
            else:
                viewer = self.caller.player
            name = proj[1] or "[尚未命名]"
            viewer.msg("{w%s 描述预览：{n\n%s" % (name, proj[2]))
            return
        # do rolls for our crafting. determine quality level, handle forgery stuff
        if "finish" in self.switches:
            if not proj[1]:
                caller.msg(_("你必须先为其命名。"))
                return
            if not proj[2]:
                caller.msg(_("你必须先撰写描述。"))
                return
            invest = 0
            action_points = 0
            if self.lhs:
                try:
                    invest = int(self.lhslist[0])
                    if len(self.lhslist) > 1:
                        action_points = int(self.lhslist[1])
                except ValueError:
                    caller.msg(_("投入的银两和行动点必须为数字。"))
                    return
                if invest < 0 or action_points < 0:
                    caller.msg(_("银两和行动点不可为负数。"))
                    return
            # first, check if we have all the materials required
            mats = {}
            try:
                recipe = recipes.get(id=proj[0])
            except CraftingRecipe.DoesNotExist:
                caller.msg(_("你无力完成此配方。"))
                return
            if not self.check_max_invest(recipe, invest):
                return
            if recipe.type == "disguise":
                if not proj[6]:
                    caller.msg(
                        _("此类物品需先用 craft/altdesc 设定伪装描述方可完成。")
                    )
                    return
            for mat in recipe.required_materials.all():
                mats[mat.type_id] = mats.get(mat.type_id, 0) + mat.amount
            for adorn in proj[3]:
                mats[adorn] = mats.get(adorn, 0) + proj[3][adorn]
            # replace with forgeries
            for rep in proj[4].keys():
                # rep is ID to replace
                forg = proj[4][rep]
                if rep in mats:
                    amt = mats[rep]
                    del mats[rep]
                    mats[forg] = amt
            # check silver cost
            try:
                price = self.get_recipe_price(recipe)
            except ValueError:
                caller.msg(_("该配方未定义价格。"))
                return
            cost = recipe.additional_cost + invest + price
            if cost < 0 or price < 0:
                errmsg = "For %s at %s, recipe %s, cost %s, price %s" % (
                    caller,
                    caller.location,
                    recipe.id,
                    cost,
                    price,
                )
                raise ValueError(errmsg)
            if not caller.check_permstring("builders"):
                if caller.item_data.currency < cost:
                    caller.msg(
                        _("配方本身需花费 %s 银两，你打算额外投入 %s。")
                        % (recipe.additional_cost, invest)
                    )
                    if price:
                        caller.msg(
                            _("炼制师额外收费 %s 银两。")
                            % price
                        )
                    caller.msg(
                        _("共需 %s 银两，但你仅有 %s。")
                        % (cost, caller.item_data.currency)
                    )
                    return
                pmats = caller.player.Dominion.assets.owned_materials
                # add up the total cost of the materials we're using for later
                realvalue = 0
                for mat in mats:
                    try:
                        c_mat = CraftingMaterialType.objects.get(id=mat)
                    except CraftingMaterialType.DoesNotExist:
                        inform_staff(
                            _("尝试使用不存在的材料 %s 进行炼制。")
                            % mat
                        )
                        self.msg(
                            _("所需材料似乎已不存在，已通报执事。")
                        )
                        return
                    try:
                        pmat = pmats.get(type=c_mat)
                        if pmat.amount < mats[mat]:
                            caller.msg(
                                _("你需要 %s 份 %s，但仅有 %s 份。")
                                % (mats[mat], c_mat.name, pmat.amount)
                            )
                            return
                        realvalue += c_mat.value * mats[mat]
                    except OwnedMaterial.DoesNotExist:
                        caller.msg(
                            _("你没有 %s 材料。") % c_mat.name
                        )
                        return
                # check if they have enough action points
                if not caller.player_ob.pay_action_points(2 + action_points):
                    self.msg(_("你没有足够的行动点来炼制。"))
                    return
                # pay the money
                caller.pay_money(cost)
                # we're still here, so we have enough materials. spend em all
                for mat in mats:
                    cmat = CraftingMaterialType.objects.get(id=mat)
                    pmat = pmats.get(type=cmat)
                    pmat.amount -= mats[mat]
                    pmat.save()
            # determine difficulty modifier if we tossed in more money
            ability = get_ability_val(crafter, recipe)
            diffmod = get_difficulty_mod(recipe, invest, action_points, ability)
            # do crafting roll
            roll = do_crafting_roll(crafter, recipe, diffmod, room=caller.location)
            # get type from recipe
            otype = recipe.type
            # create object
            if otype == "wieldable":
                obj, quality = create_weapon(recipe, roll, proj, caller, crafter)
            elif otype == "wearable":
                obj, quality = create_wearable(recipe, roll, proj, caller, crafter)
            elif otype == "place":
                obj, quality = create_place(recipe, roll, proj, caller, crafter)
            elif otype == "container":
                obj, quality = create_container(recipe, roll, proj, caller, crafter)
            elif otype == "decorative_weapon":
                obj, quality = create_decorative_weapon(
                    recipe, roll, proj, caller, crafter
                )
            elif otype == "wearable_container":
                obj, quality = create_wearable_container(
                    recipe, roll, proj, caller, crafter
                )
            elif otype == "perfume":
                obj, quality = create_consumable(
                    recipe, roll, proj, caller, PERFUME, crafter
                )
            elif otype == "disguise":
                obj, quality = create_mask(recipe, roll, proj, caller, proj[6], crafter)
            else:
                obj, quality = create_generic(recipe, roll, proj, caller, crafter)
            # finish stuff universal to all crafted objects
            obj.desc = proj[2]
            obj.save()

            self.apply_templates_to(obj)

            for mat_id, amount in proj[3].items():
                obj.item_data.add_adorn(mat_id, amount)
            self.pay_owner(
                price,
                _("%s 在你的店铺炼制了 '%s'（%s），你获得 %s 银两。")
                % (caller, obj, recipe.name, price),
            )
            try:
                for lang, text in proj[5].items():
                    obj.item_data.add_translation(lang, text)
            except IndexError:
                pass
            cnoun = "你" if caller == crafter else crafter
            caller.msg(_("%s炼成了 %s。") % (cnoun, obj.name))
            quality = QUALITY_LEVELS[quality]
            caller.msg(_("品质为 %s。") % quality)
            caller.db.crafting_project = None
            return


class CmdRecipes(ArxCommand):
    """
    recipes
    Usage:
        recipes [<ability or skill to filter by>]
        recipes/known
        recipes/learn <recipe name>
        recipes/info <recipe name>
        recipes/cost <recipe name>
        recipes/teach <character>=<recipe name>

    Check, learn, or teach recipes. Without an argument, recipes
    lists all recipes you know or can learn. The /info switch lists the
    requirements for learning a given recipe. Learning a recipe may or
    may not be free - cost lets you see the cost of a recipe beforehand.
    """

    key = "recipes"
    locks = "cmd:all()"
    aliases = ["recipe"]
    help_category = "Crafting"

    def display_recipes(self, recipes):
        from server.utils import arx_more

        if not recipes:
            self.msg(_("(无符合条件的配方)"))
            return
        known_list = CraftingRecipe.objects.filter(
            known_by__player__player=self.caller.player
        )
        table = PrettyTable(
            ["{w已习{n", "{w名称{n", "{w技艺{n", "{w难度{n", "{w花费{n"]
        )

        def getter(a):
            return a.ability or ""

        recipes = sorted(recipes, key=getter)
        for recipe in recipes:
            known = "{w√{n" if recipe in known_list else ""
            table.add_row(
                [
                    known,
                    str(recipe),
                    recipe.ability,
                    recipe.difficulty,
                    recipe.additional_cost,
                ]
            )
        arx_more.msg(self.caller, str(table), justify_kwargs=False)

    def func(self):
        """Implement the command"""
        caller = self.caller
        all_recipes = CraftingRecipe.objects.all()
        recipes = all_recipes.filter(known_by__player__player=caller.player)
        unknown = all_recipes.exclude(known_by__player__player=caller.player)
        if self.args and (not self.switches or "known" in self.switches):
            filters = (
                Q(name__iexact=self.args)
                | Q(skill__iexact=self.args)
                | Q(ability__iexact=self.args)
            )
            recipes = recipes.filter(filters)
            unknown = unknown.filter(filters)
        orgs = AssetOwner.objects.select_related("organization_owner").filter(
            organization_owner__isnull=False
        )
        unknown = unknown.prefetch_related(
            Prefetch("known_by", queryset=orgs, to_attr="_org_owners")
        )
        recipes = list(recipes)
        can_learn = [ob for ob in unknown if ob.can_be_learned_by(self.caller)]
        try:
            dompc = PlayerOrNpc.objects.get(player=caller.player)
        except PlayerOrNpc.DoesNotExist:
            dompc = setup_dom_for_char(caller)
        if not self.switches:
            visible = recipes + can_learn
            self.display_recipes(visible)
            return
        if "known" in self.switches:
            self.display_recipes(recipes)
            return
        if "learn" in self.switches or "cost" in self.switches:
            match = None
            if self.args:
                match = [ob for ob in can_learn if ob.name.lower() == self.args.lower()]
            if not match:
                learn_msg = (_("你无法习得 '%s'。") % self.lhs) if self.lhs else ""
                caller.msg(_("%s可习得的配方：") % learn_msg)
                self.display_recipes(can_learn)
                return
            match = match[0]
            cost = 0 if caller.check_permstring("builders") else match.additional_cost
            cost_msg = _("习得 %s 需花费 %s。") % (
                match.name,
                cost or _("免费"),
            )
            if "cost" in self.switches:
                return caller.msg(cost_msg)
            elif cost > caller.currency:
                return caller.msg(
                    _("你持有 %s 银两。%s") % (caller.currency, cost_msg)
                )
            caller.pay_money(cost)
            dompc.assets.crafting_recipes.add(match)
            coststr = _("，花费 %s 银两") % cost if cost else ""
            caller.msg(_("你已习得 %s%s。") % (match.name, coststr))
            return
        if "info" in self.switches:
            match = None
            info = list(can_learn) + list(recipes)
            if self.args:
                match = [ob for ob in info if ob.name.lower() == self.args.lower()]
            if not match:
                caller.msg(_("无此配方。可查询详情的配方："))
                self.display_recipes(info)
                return
            match = match[0]
            display = match.display_reqs(dompc, full=True)
            caller.msg(display, options={"box": True})
            return
        if "teach" in self.switches:
            match = None
            can_teach = [ob for ob in recipes if ob.access(caller, "teach")]
            if self.rhs:
                match = [ob for ob in can_teach if ob.name.lower() == self.rhs.lower()]
            if not match:
                teach_msg = (_("你无法传授 '%s'。") % self.rhs) if self.rhs else ""
                caller.msg(_("%s可传授的配方：") % teach_msg)
                self.display_recipes(can_teach)
                return
            recipe = match[0]
            character = caller.search(self.lhs)
            if not character:
                return
            if not recipe.access(character, "learn"):
                caller.msg(_("对方无法习得 %s。") % recipe.name)
                return
            try:
                dompc = PlayerOrNpc.objects.get(player=character.player)
            except PlayerOrNpc.DoesNotExist:
                dompc = setup_dom_for_char(character)
            if recipe in dompc.assets.crafting_recipes.all():
                caller.msg(_("对方已习得 %s。") % recipe.name)
                return
            dompc.assets.crafting_recipes.add(recipe)
            caller.msg(_("已传授 %s 给 %s。") % (recipe.name, character))


class CmdJunk(ArxCommand):
    """
    +junk

    Usage:
        +junk <object>

    销毁物品，回收部分炼制材料。
    """

    key = "junk"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        """Implement the command"""
        obj = self.caller.search(self.args, use_nicks=True)
        if not obj:
            return
        else:
            if len(make_iter(obj)) > 1:
                AT_SEARCH_RESULT(obj, self.caller, self.args, False)
                return
            obj = make_iter(obj)[0]
        from server.utils.exceptions import CommandError

        try:
            if obj.player_ob or obj.player:
                raise CommandError(_("你不可销毁角色。"))
            obj.junk_handler.junk(self.caller)
        except AttributeError:
            self.msg(_("只能销毁炼制品。"))
        except CommandError as err:
            self.msg(err)
