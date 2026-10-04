# Simplified Paifu Format

Simplified paifu 是 paifu-core 面向大规模研究和统计分析约定的压缩牌谱格式。它只记录 replay 必需的最小事实，不重复保存每个决策点的完整局面。

每个 simplified paifu 对象表示一个小局。多个小局使用对象列表，按牌局发生顺序排列。

## 顶层结构

每个小局对象包含固定四个顶层字段：`rule`、`metainfo`、`tiles`、`decisions`。

```json
{
    "rule": "majsoul_std",
    "metainfo": {
        "wind": "S",
        "round": 4,
        "honba": 2,
        "kyotaku": 0,
        "scores": {
            "E": 26700,
            "S": 9600,
            "W": 36100,
            "N": 27600
        }
    },
    "tiles": {
        "initial_hands": {
            "E": ["3m", "3m", "6m", "8m", "1p", "2p", "4p", "0p", "6p", "1s", "1z", "2z", "2z", "7z"],
            "S": ["4m", "1p", "3p", "5p", "6p", "9p", "3s", "8s", "8s", "8s", "9s", "1z", "7z"],
            "W": ["1m", "0m", "6m", "6m", "8m", "1p", "2p", "3p", "3p", "4p", "6p", "9s", "1z"],
            "N": ["5m", "6m", "9m", "3p", "9p", "9p", "7s", "3z", "5z", "6z", "6z", "7z", "7z"]
        },
        "wall": ["7p", "4p", "3m", "2s"],
        "rinshan": ["2p", "7s", "2s", "1z"],
        "dora_indicators": ["2m", "1m", "4s", "6s", "6z"],
        "ura_indicators": ["7m", "7m", "4s", "8p", "6s"]
    },
    "decisions": [
        {
            "type": "discard",
            "tile": "1s",
            "from": "hand"
        },
        {
            "type": "pon",
            "from": "N",
            "hands": ["7z", "7z"],
            "tile": "7z"
        },
        {
            "type": "tsumo"
        }
    ]
}
```

示例中的 `wall` 只截取前几张用于说明。真实 simplified paifu 应保存完整可重放的小局牌序。

`rule = "majsoul_std"` 表示雀魂四人标准规则。格式不带 `version` 字段。

## metainfo

`metainfo` 与 snapshot 中的同名字段保持相近含义，但 simplified paifu 只记录起局状态。字段顺序建议固定为 `wind`、`round`、`honba`、`kyotaku`、`scores`。

| 字段 | 含义 |
| --- | --- |
| `wind` | 起局场风，允许 `E`、`S`、`W`、`N`。 |
| `round` | 当前场风内第几小局，允许 `1` 至 `4`。南四局表示为 `"wind": "S", "round": 4`。 |
| `honba` | 起局本场数。 |
| `kyotaku` | 起局场供立直棒数量，按根数记录。 |
| `scores` | 起局各家点数。 |

四家分数之和加上场供点数应保持守恒。默认 25000 点起局时，应满足：

```text
sum(scores.values()) + kyotaku * 1000 == 100000
```

## tiles

`tiles` 记录 replay 需要的初始牌和牌序。字段顺序建议固定为 `initial_hands`、`wall`、`rinshan`、`dora_indicators`、`ura_indicators`。

| 字段 | 含义 |
| --- | --- |
| `initial_hands` | 起手牌。亲家 14 张，其它三家 13 张。 |
| `wall` | 普通摸牌序列。亲家起手第 14 张不放入 `wall`。 |
| `rinshan` | 岭上牌序列。第一次杠后补牌使用 `rinshan[0]`。 |
| `dora_indicators` | 宝牌指示牌序列，按翻开顺序排列。 |
| `ura_indicators` | 里宝牌指示牌序列，按翻开顺序排列。 |

`initial_hands` 是顺序无关列表，必须按通用牌排序规则排列。牌列表在 JSON 中必须写成单行数组，减少文件体积并方便人工扫描。

`wall`、`rinshan`、`dora_indicators` 和 `ura_indicators` 是顺序相关列表，不排序。它们应按 replay 消耗或翻开的顺序保存。

## decisions

`decisions` 是决策结果对象列表。Replay 从 `metainfo` 和 `tiles` 生成 snapshot 决策点，再按顺序消费 `decisions`。因此每个 decision 应对应 replay 过程中实际产生的一个决策点。

Simplified paifu 不保存结算结果、役种、符数或最终分数；这些信息由 replay 按 `rule`、牌序和决策结果推导。

### discard

`discard` 表示当前玩家切出一张牌。

```json
{
    "type": "discard",
    "tile": "5p",
    "from": "hand"
}
```

| 字段 | 含义 |
| --- | --- |
| `tile` | 切出的牌。 |
| `from` | 允许 `hand` 或 `draw`。`hand` 表示从手牌切出；`draw` 表示切刚取得的普通摸牌或岭上牌。 |

亲家的第一巡切牌来自 14 张起手牌，因此 `from` 使用 `hand`。

### chi / pon

`chi` 和 `pon` 表示有人鸣走上一张弃牌。

```json
{
    "type": "chi",
    "from": "E",
    "hands": ["1p", "2p"],
    "tile": "3p"
}
```

| 字段 | 含义 |
| --- | --- |
| `from` | 谁鸣走这张牌，使用 `E`、`S`、`W`、`N`。 |
| `hands` | 鸣牌者从自己手牌拿出的牌。 |
| `tile` | 被鸣走的上一张弃牌。 |

`hands` 和 `tile` 必须分开记录，以区分不同吃牌形状。例如 `hands = ["2p", "3p"], tile = "4p"` 与 `hands = ["2p", "4p"], tile = "3p"` 是不同决策。

### kan

杠的决策类型沿用 `open_kan`、`closed_kan`、`added_kan`。

`open_kan` 与 `chi`、`pon` 一样，使用 `hands` 表示自己手牌中的三张牌，`tile` 表示被鸣走的上一张弃牌。

```json
{
    "type": "open_kan",
    "from": "S",
    "hands": ["7z", "7z", "7z"],
    "tile": "7z"
}
```

`closed_kan` 和 `added_kan` 不接收上一张弃牌，直接记录自己使用的牌：

```json
{
    "type": "closed_kan",
    "hands": ["9p", "9p", "9p", "9p"]
}
```

```json
{
    "type": "added_kan",
    "hands": ["7p"]
}
```

### ron

`ron` 表示一个或多个玩家荣和上一张弃牌。

```json
{
    "type": "ron",
    "winners": ["S", "W"]
}
```

`winners` 支持双响和三响。和牌牌由前一个 `call_decision` 的弃牌确定，不重复记录。

### tsumo

`tsumo` 表示当前玩家自摸和牌。

```json
{
    "type": "tsumo"
}
```

自摸玩家和和牌牌由 replay 当前状态确定，不重复记录。

### pass

若 replay 生成了 `call_decision`，但所有可行动玩家都选择不鸣牌、不荣和，则记录 `pass`。

```json
{
    "type": "pass"
}
```

如果没有任何玩家可鸣牌或荣和，则不生成 `call_decision`，也不记录 `pass`。

### draw_game

`draw_game` 表示该小局流局。

```json
{
    "type": "draw_game"
}
```

流局类型、听牌状态和点数变化由 replay 根据规则和当前局面推导。
