# 魔法材料名称汉化完成报告

## 汉化完成时间：2026-03-19

---

## 一、魔法材料名称对照表

| 英文名称 | 中文名称 | 品阶 |
|---------|---------|------|
| alaricite | 千年灵芝 | 一阶 |
| star iron | 天星铁 | 一阶 |
| diamondplate | 玄铁精 | 二阶 |
| iridescite | 七彩琉璃 | 二阶 |
| stygian | 幽冥石 | 二阶 |
| rubicund | 赤血砂 | 二阶 |
| steel | 精钢 | 普通材料 |

---

## 二、修改的文件

### 1. world/magic/mixins.py

**修改内容：**
- 添加 `MAGIC_MATERIALS` 字典，包含英文到中文的映射
- 添加 `get_material_tier()` 函数，支持中英文材料名称检测
- 重构 `quality_level_from_primum()` 方法
- 重构 `max_potential` 属性
- 重构 `potential` 属性

**代码示例：**
```python
# 魔法材料名称映射（英文名: (中文名, 品阶)）
MAGIC_MATERIALS = {
    # 一阶材料 / Tier 1 materials
    "alaricite": ("千年灵芝", 1),
    "star iron": ("天星铁", 1),
    # 二阶材料 / Tier 2 materials
    "diamondplate": ("玄铁精", 2),
    "iridescite": ("七彩琉璃", 2),
    "stygian": ("幽冥石", 2),
    "rubicund": ("赤血砂", 2),
}

def get_material_tier(name):
    """支持英文名称和中文名称的材料品阶检测"""
    if not name:
        return None
    lower_name = name.lower()
    for eng_name, (chi_name, tier) in MAGIC_MATERIALS.items():
        if eng_name in lower_name or chi_name in name:
            return tier
    return None
```

### 2. world/exploration/models.py

**修改内容：**
- 修改 `generate_weapon_name()` 方法，生成中文武器名称

**代码示例：**
```python
# 武器名称生成示例
# 原格式: "an ancient diamondplate sword"
# 新格式: "上古玄铁精兵器"

material_names = {
    "steel": "精钢",
    "rubicund": "赤血砂",
    "diamondplate": "玄铁精",
    "alaricite": "千年灵芝",
    "star iron": "天星铁",
    "iridescite": "七彩琉璃",
    "stygian": "幽冥石",
}
```

---

## 三、设计原则

### 双语兼容

代码同时支持英文名称和中文名称检测：

```python
# 以下两种方式都可以正确识别材料
get_material_tier("diamondplate")  # 返回 2
get_material_tier("玄铁精")         # 返回 2
get_material_tier("diamondplate ingot")  # 返回 2
get_material_tier("上等玄铁精")      # 返回 2
```

### 向后兼容

- 数据库中的英文配方名仍然可以正常工作
- 新建的中文配方名也可以被正确识别
- 战利品生成系统内部仍使用英文键名，但显示中文名称

---

## 四、测试结果

✅ **i18n测试：11个测试全部通过**

---

## 五、材料设定说明

### 一阶材料（Tier 1）
- **千年灵芝** - 稀有灵药，补气安神，延年益寿
- **天星铁** - 天外陨铁，锻造神兵的上佳材料

### 二阶材料（Tier 2）
- **玄铁精** - 百炼精钢，坚硬无比
- **七彩琉璃** - 流光溢彩，炼器珍材
- **幽冥石** - 阴气凝聚，鬼道至宝
- **赤血砂** - 炼丹材料，赤红如火

### 普通材料
- **精钢** - 常见锻造材料

---

*魔法材料汉化完成*