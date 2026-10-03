# Snapshot Format

Snapshot 是 paifu-core 面向研究流程约定的标准局面格式。它不限定来源，可以来自牌谱回放、人工标注、模拟器或其它系统。

Snapshot 不是完整牌谱事件，也不是 OCR 证据格式。它只表示牌局边界或一个明确的决策入口。

## 顶层结构

每个 snapshot 顶层必须有 `type` 字段。

```json
{
    "type": "discard_decision",
    "latest_action": {
        "type": "draw",
        "player": "E",
        "card": "5m"
    },
    "metainfo": {
        "wind": "E",
        "round": 1,
        "dora_indicators": ["4m"],
        "ura_indicators": [],
        "remaining_tiles": 70,
        "honba": 0,
        "kyotaku": 0,
        "scores": {
            "E": 25000,
            "S": 25000,
            "W": 25000,
            "N": 25000
        }
    }
}
```

`type = "init"` 时不带 `latest_action`。其它类型必须带 `latest_action`。`metainfo` 放在 `type` 和 `latest_action` 之后，用于记录局号、宝牌指示牌、里宝牌指示牌、分数、本场和场供。`players` 与 `metainfo` 同级，用于记录四家手牌、牌河和副露。

## Snapshot 类型

| `type` | 是否有 `latest_action` | 含义 |
| --- | --- | --- |
| `init` | 否 | 牌局刚刚开始，还没有任何人开始打牌；各家手牌都是 13 张，亲家尚未摸牌。 |
| `discard_decision` | 是 | 轮到某个玩家作出自身行动决策，包括切牌、暗杠、自摸等。 |
| `call_decision` | 是 | 轮到一个或多个其它玩家判断是否鸣牌、荣和或抢杠。 |
| `final` | 是 | 牌局已经结束，要么有人和牌，要么流局。 |

## metainfo

`metainfo` 记录局面元信息。字段顺序建议固定为 `wind`、`round`、`dora_indicators`、`ura_indicators`、`remaining_tiles`、`honba`、`kyotaku`、`scores`。

```json
{
    "metainfo": {
        "wind": "E",
        "round": 4,
        "dora_indicators": ["4m", "1z"],
        "ura_indicators": ["8p"],
        "remaining_tiles": 23,
        "honba": 0,
        "kyotaku": 1,
        "scores": {
            "E": 25000,
            "S": 24000,
            "W": 25000,
            "N": 25000
        }
    }
}
```

| 字段 | 含义 |
| --- | --- |
| `wind` | 场风，允许 `E`、`S`、`W`、`N`。 |
| `round` | 当前场风内第几小局，允许 `1` 至 `4`。东四局表示为 `"wind": "E", "round": 4`。 |
| `dora_indicators` | 已知的宝牌指示牌列表。来源知道就填写，不知道可省略。 |
| `ura_indicators` | 已知的里宝牌指示牌列表。来源知道就填写，不知道可省略。 |
| `remaining_tiles` | 剩余可普通摸牌数量，不包括王牌。 |
| `honba` | 本场数。除 `final` 外表示当前小局本场数；`final` 中表示下一小局 `init` 应继承的本场数。 |
| `kyotaku` | 场供立直棒数量，按根数记录，每根 1000 点。 |
| `scores` | 各家当前点数，使用点数整数，不带分数单位。 |

`remaining_tiles` 不包括王牌、岭上牌和宝牌指示牌区域。杠后补牌来自王牌，但为了维持王牌结构，会消耗未来普通摸牌余量；因此若开杠前 `remaining_tiles` 为 1，杠后补牌结算后应进入荒牌流局状态。

`final.metainfo` 表示已经结算完的状态。`final.metainfo.wind` 和 `final.metainfo.round` 仍表示刚结束的这一小局；`final.metainfo.honba` 表示下一小局 `init` 应使用的本场数。和牌结算后被收走的场供不再计入 `kyotaku`；流局后保留的场供继续计入 `kyotaku`。

立直棒采用雀魂和天凤的实时语义：立直成立时，该玩家分数立即扣 1000 点，`kyotaku` 增加 1。若立直宣言牌被荣和，立直不成立，不扣 1000 点，也不增加 `kyotaku`。

四家分数之和加上场供点数应保持守恒。默认 25000 点起局时，应满足：

```text
sum(scores.values()) + kyotaku * 1000 == 100000
```

若规则使用其它起始点数，则右侧应为 `player_count * starting_score`。本场棒不改变点数总和，不计入该等式。

## players

`players` 使用固定四个键：`east`、`south`、`west`、`north`。这些键表示玩家对象位置；所有属性值中引用玩家时仍使用 `E`、`S`、`W`、`N`。

每个玩家对象包含：

| 字段 | 含义 |
| --- | --- |
| `hand` | 当前手牌列表。 |
| `river` | 牌河列表，下标从 `0` 开始。 |
| `tsumogiri_indices` | `river` 中摸切牌的下标列表。 |
| `called_indices` | `river` 中被鸣走牌的下标列表。 |
| `riichi` | 是否已经立直成立。 |
| `riichi_declaration_index` | 立直宣言牌在 `river` 中的下标；仅在 `riichi` 为 `true` 时出现。 |
| `melds` | 副露列表，按发生顺序从早到晚排列。 |

`called_indices` 只索引当前 `river` 中存在的牌。snapshot 允许被鸣走的牌不在 `river` 中出现；这种情况下不需要在 `called_indices` 中记录它。

`hand` 表示进入 snapshot 时玩家当前可用于决策的闭合手牌。摸牌和岭上补牌后，`hand` 包含刚取得的牌；吃、碰、杠后，组成副露的手牌已经从 `hand` 中移除。snapshot 中同一张实体牌不会同时出现在 `hand` 和 `melds` 中。

`riichi_declaration_index` 只指实际立直宣言牌。若宣言牌被鸣走，下一巡打出的横置牌不算宣言牌。对于只能识别横置牌的 OCR 来源，允许用可见横置牌近似，因此这类 snapshot 可能丢失宣言牌被鸣走的细节。

玩家对象示例：

```json
{
    "hand": ["1m", "2m", "3m", "5p", "6p", "7p", "2s", "3s", "4s", "5z", "5z", "6z", "7z"],
    "river": ["9m", "1z", "7p", "3s", "4m", "8p"],
    "tsumogiri_indices": [1, 4],
    "called_indices": [2],
    "riichi": false,
    "melds": []
}
```

### 副露

副露对象必须有 `type` 和 `tiles`。允许的 `type`：

```text
chi
pon
open_kan
closed_kan
added_kan
```

除 `closed_kan` 外，副露还必须有：

| 字段 | 含义 |
| --- | --- |
| `called_tile` | 鸣来的牌。 |
| `from` | 该牌来自哪一家，使用 `E`、`S`、`W`、`N`。 |

`added_kan` 是单独的副露类型。它的 `called_tile` 和 `from` 指最初碰这组副露时鸣来的牌和来源玩家，不指加杠时从自己手牌加入的牌。

副露示例：

```json
[
    {
        "type": "chi",
        "tiles": ["2m", "3m", "4m"],
        "called_tile": "3m",
        "from": "W"
    },
    {
        "type": "closed_kan",
        "tiles": ["9p", "9p", "9p", "9p"]
    },
    {
        "type": "added_kan",
        "tiles": ["7p", "7p", "7p", "7p"],
        "called_tile": "7p",
        "from": "E"
    }
]
```

## latest_action

`latest_action` 表示进入该 snapshot 前的上一个操作。它不是完整事件日志，只保留决策语义所需的最小上下文。

### discard_decision

`discard_decision` 表示轮到某个玩家从当前手牌状态中作决策。暗杠、自摸等完全来自自身判断的选择，都属于这个决策点。

允许的 `latest_action.type`：

| 值 | 必填字段 | 含义 |
| --- | --- | --- |
| `draw` | `player`, `card` | 玩家普通摸牌后进入自身决策。 |
| `replacement` | `player`, `card` | 玩家岭上补牌后进入自身决策。 |
| `chi` | `player` | 玩家吃牌后进入切牌决策。 |
| `pon` | `player` | 玩家碰牌后进入切牌决策。 |

### call_decision

`call_decision` 表示某个玩家刚打出牌，或刚加杠，并且至少存在其他玩家可以鸣牌、荣和或抢杠。如果无人可鸣、无人可荣，不生成该 snapshot。

允许的 `latest_action.type`：

| 值 | 必填字段 | 含义 |
| --- | --- | --- |
| `discard` | `player`, `card` | 玩家刚打出一张牌，其他玩家需要判断是否 `chi`、`pon`、`kan` 或 `ron`。 |
| `riichi_declaration` | `player`, `card` | 玩家刚打出立直宣言牌，其他玩家需要判断是否 `chi`、`pon`、`kan` 或 `ron`；若该牌被荣和，立直不成立。 |
| `added_kan` | `player`, `card` | 玩家刚加杠，其他玩家需要判断是否抢杠 `ron`。 |

立直宣言牌后示例：

```json
{
    "type": "call_decision",
    "latest_action": {
        "type": "riichi_declaration",
        "player": "S",
        "card": "7p"
    },
    "metainfo": {
        "wind": "E",
        "round": 4,
        "dora_indicators": ["4m"],
        "ura_indicators": [],
        "remaining_tiles": 23,
        "honba": 0,
        "kyotaku": 0,
        "scores": {
            "E": 25000,
            "S": 25000,
            "W": 26000,
            "N": 24000
        }
    }
}
```

此时立直尚未成立，因此分数还未扣 1000 点，`kyotaku` 也尚未增加。

### final

`final` 表示牌局已经结束。允许自摸、荣和和流局。

允许的 `latest_action.type`：

| 值 | 必填字段 | 含义 |
| --- | --- | --- |
| `tsumo` | `player`, `card`, `yaku` | 自摸结束。 |
| `ron` | `player`, `card`, `yaku` | 荣和结束；`player` 可为单个玩家或玩家列表。 |
| `draw_game` | `draw_game_type` | 流局结束；不带 `player`。 |

多人荣和示例：

```json
{
    "type": "final",
    "latest_action": {
        "type": "ron",
        "player": ["S", "W"],
        "card": "5p",
        "yaku": [
            ["one_shot"],
            []
        ]
    }
}
```

## 字段约束

### `player`

玩家使用风位表示，允许值为：

```text
E
S
W
N
```

除 `ron` 外，`player` 都是单个玩家。`ron` 可以是单个玩家，也可以是玩家列表，用于一炮多响。`draw_game` 不带 `player`。

### `card`

牌使用紧凑牌 ID，允许值为：

```text
1m..9m, 0m
1p..9p, 0p
1s..9s, 0s
1z..7z
```

以下动作必须带 `card`：

```text
draw
replacement
discard
riichi_declaration
added_kan
tsumo
ron
```

`chi` 和 `pon` 不带 `card`，因为它们接收的是前一个 `call_decision` 中的弃牌。`draw_game` 不带 `card`。

### `yaku`

`yaku` 只用于 `tsumo` 和 `ron`。

单人自摸或单人荣和时，`yaku` 是字符串列表：

```json
[
    "one_shot",
    "double_riichi"
]
```

多人荣和时，`yaku` 是列表的列表，并与 `player` 列表按顺序一一对应：

```json
{
    "player": ["S", "W"],
    "yaku": [
        ["one_shot"],
        ["double_riichi"]
    ]
}
```

`yaku` 只记录不能仅靠 snapshot 中的手牌、牌河和局面信息稳定推断出的偶然役或过程役。建议 v1 支持：

```text
double_riichi
one_shot
after_a_kan
robbing_a_kan
```

普通手役、立直状态以及可由局面推断的海底/河底等役，不写入 `latest_action.yaku`。

### `draw_game_type`

`draw_game_type` 只用于 `latest_action.type = "draw_game"`，允许值为：

```text
exhaustive
four_winds
four_riichi
four_kans
three_ron
nine_terminals
```

`draw_game_type = "exhaustive"` 时，应带 `tenpai_players`。

### `tenpai_players`

`tenpai_players` 只用于荒牌流局，表示听牌玩家列表。允许为空列表。

```json
[]
```

```json
["E", "S", "W", "N"]
```

详细覆盖用例放在后续 tests 文档中维护，本文件只记录格式约束和少量代表性示例。
