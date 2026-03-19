# 爪域 - 技术架构全景图

> **说明：** 本文档描述游戏的技术架构和系统设计。
> 如需了解世界观、剧情、文化设定，请参阅 [世界设定全景图](./WORLD_SETTING.md)。

## 概述

《爪域》是一款基于 Evennia 框架的架空仙侠风格文字游戏，融合了武侠江湖与仙侠玄幻元素，以东方上古神话为底蕴，构建了一个充满仙魔传说、门派纷争、王朝更迭的宏大世界。

---

## 一、系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Claw-Dominion 游戏架构                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     命令层 (Commands Layer)                          │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │   │
│  │  │ CharacterCmdSet│  │ AccountCmdSet │  │ UnloggedinCmdSet│           │   │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘            │   │
│  │          │                  │                  │                    │   │
│  │  ┌───────┴───────┐  ┌───────┴───────┐  ┌───────┴───────┐            │   │
│  │  │ CombatCmdSet  │  │ DominionCmds  │  │ SocialCmds    │            │   │
│  │  │ CraftingCmds  │  │ MagicCmds     │  │ StaffCmds     │            │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┴───────────────────────────────────┐   │
│  │                     类型类层 (Typeclasses Layer)                     │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │   Character    │  │     ArxRoom    │  │   ArxObject    │         │   │
│  │  │  (玩家侠客)     │  │   (江湖场景)    │  │   (江湖物品)    │         │   │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘         │   │
│  │          │                   │                   │                  │   │
│  │  ┌───────┴───────┐   ┌───────┴───────┐   ┌───────┴───────┐          │   │
│  │  │ UseEquipment  │   │    Places     │   │   Wearable    │          │   │
│  │  │   Mixins      │   │   Containers  │   │   Wieldable   │          │   │
│  │  │  MsgMixins    │   │   Readable    │   │   Consumable  │          │   │
│  │  │ ObjectMixins  │   │   Exits       │   │   Disguises   │          │   │
│  │  │ MagicMixins   │   │   NPCs        │   │   Gambling    │          │   │
│  │  └───────────────┘   └───────────────┘   └───────────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┴───────────────────────────────────┐   │
│  │                     世界系统层 (World Systems Layer)                 │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │   dominion/    │  │   stat_checks/ │  │   conditions/  │         │   │
│  │  │  藩镇/门派系统  │  │   属性检定系统  │  │   状态效果系统  │         │   │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘         │   │
│  │  ┌───────┴───────┐   ┌───────┴───────┐   ┌───────┴───────┐          │   │
│  │  │    magic/     │   │   crafting/   │   │    traits/    │          │   │
│  │  │   武学功法     │   │   锻造炼制     │   │   特质系统     │          │   │
│  │  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘          │   │
│  │  ┌───────┴───────┐   ┌───────┴───────┐   ┌───────┴───────┐          │   │
│  │  │    prayer/    │   │   quests/     │   │   weather/    │          │   │
│  │  │   祭祀系统     │   │   任务系统     │   │   天气系统     │          │   │
│  │  └───────────────┘   └───────────────┘   └───────────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┴───────────────────────────────────┐   │
│  │                     脚本层 (Scripts Layer)                           │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │CombatManager   │  │RecoveryScript  │  │WeeklyEvents    │         │   │
│  │  │  (比武管理器)   │  │  (恢复脚本)     │  │ (每周事件)      │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┴───────────────────────────────────┐   │
│  │                     数据持久层 (Data Persistence Layer)              │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │                    Django ORM + Evennia Models              │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、核心模块清单

### 2.1 typeclasses/ - 游戏对象类型类

| 模块 | 说明 |
|------|------|
| `characters.py` | 侠客类，继承多个 Mixin 实现复杂功能 |
| `rooms.py` | 江湖场景/地点 |
| `objects.py` | 基础物品类 |
| `mixins.py` | 核心 Mixin 类：ObjectMixins、MsgMixins、ModifierMixin 等 |
| `scripts/` | 后台脚本目录（战斗、恢复、事件） |
| `wearable/` | 穿戴/装备系统 |
| `npcs/` | NPC 实现 |
| `containers/` | 容器系统 |
| `readable/` | 可读物品（书籍、卷轴等） |
| `gambling/` | 赌博系统 |
| `disguises/` | 伪装/易容系统 |

### 2.2 world/ - 江湖世界系统

| 子系统 | 主要功能 |
|--------|----------|
| `dominion/` | 藩镇系统：门派管理、组织、兵马、经济、剧情事件 |
| `stat_checks/` | 属性检定系统：骰子检定、难度表、检定结果 |
| `conditions/` | 状态效果系统：伤势、治疗、修正值 |
| `traits/` | 特质系统：属性、武功、能力定义 |
| `crafting/` | 锻造系统：配方、材料、制造记录 |
| `magic/` | 武学功法系统：门派、亲和力、招式效果 |
| `prayer/` | 祭祀系统 |
| `quests/` | 任务系统 |
| `weather/` | 天气系统 |
| `msgs/` | 消息/语言系统 |
| `petitions/` | 请愿系统 |
| `templates/` | 模板系统 |

### 2.3 commands/ - 命令系统

| 模块 | 说明 |
|------|------|
| `default_cmdsets.py` | 主命令集入口 |
| `base_commands/` | 基础命令：通用、社交、帮助、锻造等 |
| `cmdsets/` | 情境命令集：战斗、银号、集市等 |

---

## 三、命令系统分类

### 3.1 命令集架构

```
evennia.commands.cmdset.CmdSet (基类)
    │
    ├── CharacterCmdSet (侠客命令集) - priority: 101
    │   ├── StateIndependentCmdSet (状态无关命令)
    │   ├── MobileCmdSet (移动命令)
    │   ├── OOCCmdSet (OOC命令)
    │   └── StaffCmdSet (执事命令)
    │
    ├── AccountCmdSet (账户命令集) - priority: 101
    │
    ├── UnloggedinCmdSet (未登录命令集)
    │
    └── 状态命令集:
        ├── CombatCmdSet (比武状态) - priority: 20
        ├── DeathCmdSet (死亡状态) - priority: 200
        ├── SleepCmdSet (睡眠状态) - priority: 120
        ├── BankCmdSet (银号)
        ├── MarketCmdSet (集市)
        └── RumorCmdSet (传闻)
```

### 3.2 玩家可用命令清单

| 分类 | 主要命令 |
|------|----------|
| **核心交互** | look, get, drop, give, inventory, say, whisper, shout, pose, emit |
| **移动探索** | n/s/e/w, +hangouts, +where, map, follow, ditch |
| **社交通信** | page, mail, journal, messenger, +finger, watch, calendar, afk |
| **成长系统** | xp, train, +vote |
| **锻造经济** | craft, recipes, bank, market, trade |
| **比武系统** | +fight, attack, defend, flee, ready, pass, +heal |
| **角色管理** | +sheet, +roster, +relationship, +home |
| **剧情系统** | @action, +plots, +goals, flashback |
| **组织藩镇** | +org, +domain, +army, +family, +agents |
| **执事命令** | @teleport, @dig, @create, gemit, wall, +kill, +resurrect |

---

## 四、核心数据模型

### 4.1 模型关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            核心实体关系                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐      1:1       ┌───────────────┐                    │
│  │  ObjectDB     │───────────────▶│ CharacterTrait│                    │
│  │ (Evennia基础)  │                │    Value      │                    │
│  └───────┬───────┘                └───────────────┘                    │
│          │ 1:1                                                          │
│          ▼                                                               │
│  ┌───────────────┐      1:N       ┌───────────────┐                    │
│  │CharacterHealth│───────────────▶│    Wound      │                    │
│  │    Status     │                │   (伤势)       │                    │
│  └───────────────┘                └───────────────┘                    │
│                                                                         │
│  ┌───────────────┐      M:1       ┌───────────────┐                    │
│  │  PlayerOrNpc  │◀───────────────│  AssetOwner   │                    │
│  │ (玩家/NPC实体) │                │  (资产所有者)  │                    │
│  └───────┬───────┘                └───────┬───────┘                    │
│          │                                │                             │
│          │ M:N                            │ 1:N                         │
│          ▼                                ▼                             │
│  ┌───────────────┐                ┌───────────────┐                    │
│  │ Organization  │                │    Domain     │                    │
│  │   (帮派)      │                │   (门派/封地)  │                    │
│  └───────┬───────┘                └───────┬───────┘                    │
│          │ M:N                            │ 1:N                         │
│          │                                ▼                             │
│          │                        ┌───────────────┐                    │
│          │                        │    Army       │                    │
│          │                        │   (兵马)      │                    │
│          │                        └───────────────┘                    │
│          │                                                              │
│          ▼                                                               │
│  ┌───────────────┐                ┌───────────────┐                    │
│  │  Membership   │                │    Plot       │                    │
│  │  (成员关系)    │                │  (剧情/危机)   │                    │
│  └───────────────┘                └───────┬───────┘                    │
│                                          │ M:N                         │
│                                          ▼                             │
│                                  ┌───────────────┐                    │
│                                  │ PlotAction    │                    │
│                                  │ (剧情行动)     │                    │
│                                  └───────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 关键数据模型清单

| 模块 | 主要模型 |
|------|----------|
| **角色系统** | Roster, RosterEntry, PlayerAccount, CharacterTraitValue |
| **藩镇系统** | PlayerOrNpc, Organization, AssetOwner, Domain, Army |
| **剧情系统** | Plot, PlotAction, PlotUpdate, Story, Chapter, Episode |
| **锻造系统** | CraftingRecipe, CraftingMaterialType, OwnedMaterial |
| **武学系统** | Alignment, Affinity, Spell, Casting |
| **状态系统** | RollModifier, Wound, CharacterHealthStatus, EffectTrigger |
| **消息系统** | Inform, Journal, Messenger, Rumor, Post |
| **特质系统** | Trait, CharacterTraitValue |

---

## 五、游戏机制说明

### 5.1 比武系统

**核心组件：**
- `CombatManager`: 比武管理器脚本
- `CombatantStateHandler`: 战斗者状态处理器

**战斗流程：**
```
开始比武 → Phase 1(准备) → 所有玩家确认 → Phase 2(行动)
    ↑                                              │
    └──────────────── 回合结束 ←───────────────────┘
```

**战斗命令：** +fight, attack, defend, pass, flee, +end_combat

### 5.2 属性检定系统

**检定流程：**
1. 根据 `StatCheck` 定义获取检定类型
2. 通过 `StatCombination` 计算属性/武功加值
3. 应用 `StatWeight` 权重
4. 根据双方 `CheckRank` 差异选择 `DifficultyTable`
5. 投掷 d100
6. 根据 `RollResult` 确定结果

### 5.3 藩镇系统

**三大组成部分：**

1. **经济系统** - AssetOwner, Ledger, Domain
2. **组织系统** - Organization, Membership, Reputation
3. **军事系统** - Army, Military, Orders

**周常更新：** 执行军令、调整经济

### 5.4 武学功法系统

**门派阵营：**
- **Primal（原始）**: 自然门派
- **Abyssal（深渊）**: 暗黑门派
- **Elysian（天界）**: 神圣门派

**招式效果类型：** 视觉、治疗、伤害、增益、附魔、吸收、调谐、结界

### 5.5 锻造炼制系统

**锻造流程：**
1. 学习配方 → 2. 收集材料 → 3. 锻造检定 → 4. 品质判定 → 5. 装饰镶嵌

**品质等级：** 拙劣 → 平庸 → 寻常 → 中上 → 精良 → 上乘 → 卓越 → 绝品 → 神工 → 完美 → 天工 → 化境

---

## 六、Web 界面模块

| URL路径 | 功能 |
|---------|------|
| `/` | 首页 |
| `/character/` | 侠客系统（角色卡、画廊、场景、线索、行动） |
| `/dom/` | 藩镇系统（日历、危机、地图、效忠关系） |
| `/topics/` | 帮助主题（命令、配方、组织、知识） |
| `/news/` | 新闻公告 |
| `/support/` | 工单支持 |
| `/webclient/` | WebSocket 客户端 |

---

## 七、关键文件路径索引

| 功能模块 | 关键文件 |
|----------|----------|
| 侠客定义 | `typeclasses/characters.py` |
| Mixin类 | `typeclasses/mixins.py` |
| 比武脚本 | `typeclasses/scripts/combat/combat_script.py` |
| 属性检定 | `world/stat_checks/models.py` |
| 藩镇系统 | `world/dominion/models.py` |
| 武学功法 | `world/magic/models.py` |
| 状态效果 | `world/conditions/models.py` |
| 锻造炼制 | `world/crafting/models.py` |
| 特质系统 | `world/traits/models.py` |
| 命令集 | `commands/default_cmdsets.py` |
| 剧情系统 | `world/dominion/plots/models.py` |
| 角色模型 | `web/character/models.py` |

---

## 八、技术栈总结

| 层级 | 技术 |
|------|------|
| 游戏框架 | Evennia (Python MUD/MUX 框架) |
| 数据库 | Django ORM + SQLite/PostgreSQL |
| 核心模式 | Mixin 多重继承、Handler 封装、Command Set 动态加载 |
| 缓存机制 | SharedMemoryModel 内存缓存 |
| 国际化 | Django i18n (gettext) |
| Web | Django Templates + WebSocket |

---

## 九、汉化状态

| 阶段 | 状态 | 完成内容 |
|------|------|----------|
| 基础设施 | ✅ | Django i18n 配置、翻译文件、测试套件 |
| 核心命令 | ✅ | general, social, overrides, help, combat |
| 游戏系统 | ✅ | conditions, stat_checks, magic, crafting, dominion |
| 辅助命令 | ✅ | bboards, rolling, xp, crafting, jobs, bank, market |
| Web界面 | ✅ | base, index, login, sheet 模板 |
| **翻译条目** | **1096条** | django.po 文件 |