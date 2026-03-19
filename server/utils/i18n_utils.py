# i18n utility module for 江湖侠客传 (Arx/Claw-Dominion)
"""
国际化和武侠风格本地化工具模块

此模块提供翻译辅助函数，同时保留ANSI颜色代码和MUX风格格式。
所有术语采用中国武侠江湖风格。
"""

from django.utils.translation import gettext as _, ngettext, gettext_lazy


def msg_trans(message: str) -> str:
    """
    翻译消息同时保留ANSI颜色代码。

    此函数按ANSI颜色标记分割消息，翻译文本部分，
    然后重新组装，颜色代码保持不变。

    Args:
        message: 要翻译的消息字符串，可能包含 |x 颜色代码

    Returns:
        翻译后的字符串，颜色代码保留
    """
    import re

    # ANSI颜色模式，适用于Evennia/MUX风格: |x 其中x是颜色代码
    color_pattern = r'(\|[a-zA-Z0-9])'

    # 按颜色代码分割消息
    parts = re.split(color_pattern, message)

    result = []
    for part in parts:
        if re.match(color_pattern, part):
            # 这是颜色代码，保持原样
            result.append(part)
        elif part:
            # 这是文本，翻译它
            result.append(_(part))
        else:
            # 空字符串，跳过
            pass

    return ''.join(result)


def format_trans(message: str, **kwargs) -> str:
    """
    翻译消息并使用关键字参数格式化。

    Args:
        message: 要翻译的消息字符串
        **kwargs: 格式化用的关键字参数

    Returns:
        翻译并格式化后的字符串
    """
    return _(message).format(**kwargs)


def plural_trans(singular: str, plural: str, count: int) -> str:
    """
    根据数量翻译复数消息。

    Args:
        singular: 单数形式的消息
        plural: 复数形式的消息
        count: 决定使用哪种形式的数量

    Returns:
        翻译后的复数字符串
    """
    return ngettext(singular, plural, count)


# 延迟翻译，用于模型字段
lazy_trans = gettext_lazy


# ============================================
# 武侠术语映射表 - 江湖专用（符合中国古代文化）
# ============================================

WUXIA_TERMINOLOGY = {
    # 核心术语 - 江湖基石
    'Character': '侠客',
    'Player': '玩家',
    'Account': '账户',
    'Session': '会话',
    'Password': '口令',
    'Username': '名号',

    # 属性与能力 - 武学根基
    'Stat': '属性',
    'Stats': '属性',
    'Strength': '臂力',
    'Dexterity': '身法',
    'Stamina': '根骨',
    'Charm': '魅力',
    'Command': '威望',
    'Composure': '定力',
    'Intellect': '悟性',
    'Perception': '洞察',
    'Wits': '机敏',
    'Willpower': '意志',
    'Mana': '内力',
    'Luck': '福缘',
    'Health': '气血',

    # 技能与经验
    'Skill': '武功',
    'Skills': '武功',
    'Ability': '能力',
    'Abilities': '能力',
    'Level': '境界',
    'Experience': '修为',
    'XP': '修为',

    # 世界与组织 - 江山门派
    'Domain': '门派',
    'Domains': '门派',
    'Organization': '帮派',
    'Organizations': '帮派',
    'Estate': '府邸',  # 不是庄园
    'Estates': '府邸',
    'Army': '兵马',
    'Armies': '兵马',
    'Kingdom': '王朝',  # 不是王国，中国只有一个皇帝
    'City': '城池',
    'Town': '城镇',
    'Village': '村落',
    'Room': '所在',
    'Location': '方位',
    'Fealty': '门派归属',
    'Family': '家族',
    'Castle': '城寨',  # 不是城堡
    'Temple': '庙宇',

    # 物品系统 - 行囊宝物
    'Item': '物品',
    'Items': '物品',
    'Inventory': '行囊',
    'Weapon': '兵器',
    'Weapons': '兵器',
    'Armor': '护甲',
    'Armors': '护甲',
    'Potion': '丹药',
    'Potions': '丹药',
    'Material': '材料',
    'Materials': '材料',
    'Equipment': '装备',
    'Treasure': '宝物',
    'Coins': '银两',
    'Money': '银两',
    'Gold': '金锭',
    'Silver': '银两',
    'Copper': '铜钱',
    'Scroll': '秘籍',
    'Staff': '禅杖',

    # 交流系统 - 传音书信
    'Channel': '频道',
    'Channels': '频道',
    'Message': '消息',
    'Messages': '消息',
    'Journal': '札记',
    'Journals': '札记',
    'Mail': '书信',
    'Email': '信箱',
    'Chat': '闲谈',
    'Whisper': '传音',
    'Say': '道',
    'Shout': '呼喝',
    'Emote': '动作',
    'Pose': '演武',

    # 战斗系统 - 比武交锋
    'Combat': '比武',
    'Attack': '出招',
    'Defense': '防守',
    'Damage': '伤害',
    'Check': '检定',
    'Roll': '投骰',
    'Battle': '战役',
    'Duel': '决斗',
    'Tournament': '擂台赛',

    # 状态
    'Online': '在线',
    'Offline': '离线',
    'Alive': '在世',
    'Dead': '阵亡',
    'AFK': '暂离',

    # 武学 - 功法绝招
    'Magic': '武学',
    'Spell': '功法',
    'Sorcery': '妖术',
    'Witch': '妖女',
    'Wizard': '方士',
    'Cult': '邪派',
    'Enchantment': '炼器',

    # 封建等级 - 中国特色
    'King': '皇帝',  # 不是国王
    'Queen': '皇后',
    'Prince': '王爷',
    'Princess': '公主',
    'Emperor': '皇帝',
    'Empress': '皇后',
    'Duke': '国公',
    'Marquis': '侯爷',
    'Count': '伯爵',
    'Lord': '大人',  # 不是领主
    'Lady': '夫人',
    'Knight': '武士',  # 不是骑士
    'Noble': '世家',  # 不是贵族

    # 宗教与信仰 - 中国特色
    'Religion': '信仰',
    'God': '神明',
    'Goddess': '女神',
    'Priest': '方丈',  # 不是祭司
    'Priestess': '师太',
    'Monk': '僧人',
    'Church': '寺庙',  # 不是教堂
    'Shrine': '祠堂',

    # 社会阶层
    'Peasant': '百姓',  # 不是农民
    'Merchant': '商贾',
    'Scholar': '读书人',
    'Warrior': '武者',
    'Craftsman': '工匠',
    'Servant': '仆役',
    'Guard': '护卫',
    'Soldier': '军士',

    # 组织与团体
    'Guild': '帮会',  # 不是公会
    'Clan': '宗族',
    'Tribe': '部族',
    'Faction': '势力',
    'Order': '门派',  # 不是骑士团
    'Academy': '书院',

    # 时间单位
    'Hour': '时辰',
    'Minute': '刻',
    'Second': '息',

    # 称谓语 - 古风礼貌
    'Sir': '阁下',
    'Madam': '夫人',
    'Master': '师父',
    'Mistress': '主母',

    # 其他
    'Login': '入江湖',
    'Logout': '离江湖',
    'Register': '拜山门',
    'Admin': '掌门',
    'Help': '求助',
    'Quest': '任务',
    'Event': '盛事',
    'Story': '传记',
    'Secret': '秘辛',
    'Clue': '线索',
    'Flashback': '回忆',
    'Crafting': '锻造',
}


def get_wuxia_term(term: str) -> str:
    """
    获取武侠风格的术语翻译。

    Args:
        term: 要翻译的英文术语

    Returns:
        武侠风格的中文翻译，如果未找到则返回原术语
    """
    return WUXIA_TERMINOLOGY.get(term, term)


# ============================================
# 江湖风格消息格式化
# ============================================

def wuxia_say(message: str) -> str:
    """
    将普通对话转换为江湖风格。

    Args:
        message: 原始消息

    Returns:
        江湖风格的消息
    """
    # 可以添加特殊格式化逻辑
    return _(message)


def wuxia_combat_message(attacker: str, defender: str, action: str, result: str = None) -> str:
    """
    生成江湖风格的战斗消息。

    Args:
        attacker: 攻击者名号
        defender: 防御者名号
        action: 动作类型
        result: 结果描述

    Returns:
        江湖风格的战斗消息
    """
    templates = {
        'attack': _("{attacker}向{defender}出招！"),
        'hit': _("{attacker}一招命中{defender}！"),
        'miss': _("{attacker}这一招落了空。"),
        'dodge': _("{defender}闪身避过了{attacker}的攻击。"),
        'parry': _("{defender}格挡开了{attacker}的招式。"),
        'critical': _("{attacker}使出一记绝招，正中{defender}！"),
        'defeat': _("{defender}败下阵来！"),
        'victory': _("{attacker}胜了此战！"),
    }

    template = templates.get(action, _("{attacker}对{defender}使出{action}。"))

    if result:
        return template.format(attacker=attacker, defender=defender, action=action) + " " + result
    return template.format(attacker=attacker, defender=defender, action=action)


def wuxia_social_message(speaker: str, message: str, msg_type: str = 'say') -> str:
    """
    生成江湖风格的社交消息。

    Args:
        speaker: 说话者名号
        message: 消息内容
        msg_type: 消息类型 (say/shout/whisper)

    Returns:
        江湖风格的社交消息
    """
    templates = {
        'say': _("{speaker}道：「{message}」"),
        'shout': _("{speaker}高声呼喝：「{message}」"),
        'whisper': _("{speaker}向你传音入密：「{message}」"),
        'emote': _("{speaker}{message}"),
    }

    template = templates.get(msg_type, templates['say'])
    return template.format(speaker=speaker, message=message)


# ============================================
# 颜色代码常量 - 江湖配色
# ============================================

# 常用颜色代码（用于Evennia/MUX风格）
COLOR = {
    'red': '|r',      # 红色 - 警告、伤害
    'green': '|g',    # 绿色 - 成功、治疗
    'yellow': '|y',   # 黄色 - 重要提示
    'blue': '|b',     # 蓝色 - 信息
    'magenta': '|m',  # 紫色 - 魔法/武学
    'cyan': '|c',     # 青色 - 系统消息
    'white': '|w',    # 白色 - 普通
    'normal': '|n',   # 重置颜色
}

# 武侠风格配色方案
WUXIA_COLORS = {
    'combat': COLOR['red'],      # 战斗用红色
    'heal': COLOR['green'],      # 治疗用绿色
    'magic': COLOR['magenta'],   # 武学用紫色
    'info': COLOR['cyan'],       # 信息用青色
    'warning': COLOR['yellow'],  # 警告用黄色
    'success': COLOR['green'],   # 成功用绿色
}


def colored_message(message: str, color_type: str = 'info') -> str:
    """
    添加武侠风格颜色的消息。

    Args:
        message: 原始消息
        color_type: 颜色类型

    Returns:
        带颜色代码的消息
    """
    color = WUXIA_COLORS.get(color_type, COLOR['normal'])
    return f"{color}{message}{COLOR['normal']}"