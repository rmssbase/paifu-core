# Snapshot Format

Snapshot 是 paifu-core 约定的标准局面格式，用于描述四人日麻一个小局中的某个时刻。它不限定来源，可以由牌谱回放、人工标注、模拟器或其它系统生成。

Snapshot 只表示两类时刻：牌局边界（开局、结束），或者一个明确的决策入口（某位玩家需要作出选择的时刻）。它不是逐事件的日志，两个 Snapshot 之间发生的摸牌、翻宝牌等过程不单独记录。

## 基本约定

### 玩家

玩家一律用当前小局的风位表示。以玩家为索引的对象用全称作 key，在值中引用玩家时用单个字母：

| key | value | 含义 |
| --- | --- | --- |
| `east` | `E` | 东家，即本小局的亲家。 |
| `south` | `S` | 南家。 |
| `west` | `W` | 西家。 |
| `north` | `N` | 北家。 |

例如各家点数写作 `{"east": 25000, "south": 25000, "west": 25000, "north": 25000}`，而动作执行者写作 `"player": "E"`。

可能包含多个元素的列表字段使用复数名，例如 `melds`、`ready_players`，即使只有一个元素也是如此；单个值使用单数名，例如 `player`、`tile`。

### 牌

牌使用两字符的紧凑 ID：数字加花色字母。

| ID | 含义 |
| --- | --- |
| `1m` 至 `9m` | 一万至九万。 |
| `1p` 至 `9p` | 一筒至九筒。 |
| `1s` 至 `9s` | 一索至九索。 |
| `1z` 至 `7z` | 东、南、西、北、白、发、中。 |
| `0m`、`0p`、`0s` | 红五万、红五筒、红五索。 |

手牌这类顺序无关的牌列表，按 `m`、`p`、`s`、`z` 分组，组内按数字从小到大排列；红五与对应的五同序，并排在普通五之前：

```json
["1m", "0m", "5m", "9m", "2p", "0p", "5p", "1s", "0s", "5s", "1z", "7z"]
```

牌河、宝牌指示牌这类按发生顺序记录的列表不排序。

### 动作名称

| 名称 | 含义 |
| --- | --- |
| `deal` | 从牌山普通摸牌。 |
| `replacement` | 开杠后摸岭上牌。 |
| `discard` | 切牌。 |
| `riichi_declaration` | 打出立直宣言牌。 |
| `chi` / `pon` | 吃 / 碰。 |
| `open_kan` / `closed_kan` / `added_kan` | 大明杠 / 暗杠 / 加杠。 |
| `tsumo` / `ron` | 自摸 / 荣和。 |
| `draw` | 流局。 |

## 顶层结构

每个 Snapshot 是一个 JSON 对象，顶层字段按以下顺序排列：

| 字段 | 是否必需 | 含义 |
| --- | --- | --- |
| `type` | 必需 | Snapshot 类型，见下一节。 |
| `latest_action` | 除 `init` 外必需 | 进入该局面前的最后一个动作。 |
| `metainfo` | 必需 | 场况信息：局号、宝牌、剩余牌数、本场、场供、分数。 |
| `players` | 必需 | 四家的手牌、牌河和副露。 |

本页的 JSON 示例都是片段：只保留与该例说明相关的字段，其余字段省略。真实的 Snapshot 必须包含上表中的全部必需字段。

## Snapshot 类型

| `type` | 是否有 `latest_action` | 含义 |
| --- | --- | --- |
| `init` | 否 | 小局刚配牌完毕。亲家持有 14 张牌，其余三家各 13 张；轮到亲家作第一次决策。 |
| `discard_decision` | 是 | 轮到某位玩家对自己的手牌作决策，例如切牌、立直、暗杠、加杠、自摸、宣告九种九牌。 |
| `call_decision` | 是 | 有人刚打出一张牌、刚加杠，或在允许国士无双抢暗杠的规则下刚暗杠，至少一位其他玩家可以吃、碰、杠、荣和或抢杠。 |
| `final` | 是 | 小局已经结束，有人和牌或流局，并已完成点数结算。 |

`init` 本身就是亲家的第一个决策点，可选择的操作与 `discard_decision` 相同。亲家的第 14 张牌在配牌时已经发给亲家，因此开局没有摸牌动作，`init` 也没有 `latest_action`。亲家正常切牌后，若无人可以鸣牌或荣和，下一个 Snapshot 就是南家摸牌后的 `discard_decision`。

`call_decision` 只在确实有人可以操作时出现。若一张弃牌无人可吃、碰、杠或荣和，局面直接进入下家摸牌后的 `discard_decision`。

### init 示例

南四局开局，东家（亲家）配到 14 张牌，南、西、北家各 13 张，四家的牌河和副露都还是空的。此时没有任何动作发生过，所以没有 `latest_action`；接下来由东家直接决定切哪张牌，或者立直、暗杠、自摸（天和）、宣告九种九牌。

```json
{
    "type": "init",
    "metainfo": {"wind": "S", "round": 4, "remaining_tiles": 69},
    "players": {
        "east": {"hand": ["3m", "3m", "6m", "8m", "1p", "2p", "4p", "0p", "6p", "1s", "1z", "2z", "2z", "7z"]},
        "south": {"hand": ["4m", "1p", "3p", "5p", "6p", "9p", "3s", "8s", "8s", "8s", "9s", "1z", "7z"]},
        "west": {"hand": ["1m", "0m", "6m", "6m", "8m", "1p", "2p", "3p", "3p", "4p", "6p", "9s", "1z"]},
        "north": {"hand": ["5m", "6m", "9m", "3p", "9p", "9p", "7s", "3z", "5z", "6z", "6z", "7z", "7z"]}
    }
}
```

`remaining_tiles` 为 69：136 张牌减去王牌 14 张和四家起手共 53 张。

## metainfo

`metainfo` 记录场况信息，字段顺序固定为 `wind`、`round`、`dora_indicators`、`ura_indicators`、`remaining_tiles`、`honba`、`kyotaku`、`scores`。

| 字段 | 含义 |
| --- | --- |
| `wind` | 场风，允许 `E`、`S`、`W`、`N`。 |
| `round` | 当前场风内第几小局，允许 `1` 至 `4`。南四局表示为 `"wind": "S", "round": 4`。 |
| `dora_indicators` | 已翻开的宝牌指示牌，按翻开顺序排列。来源不知道时可省略。 |
| `ura_indicators` | 已翻开的里宝牌指示牌，按翻开顺序排列。里宝牌只在立直者和牌时翻开，其它时刻通常为空列表。来源不知道时可省略。 |
| `remaining_tiles` | 剩余可普通摸牌的张数，不包括王牌。 |
| `honba` | 本场数。`final` 中表示下一小局应使用的本场数，其它类型表示当前小局的本场数。 |
| `kyotaku` | 场供立直棒的根数，每根 1000 点。`final` 中表示下一小局应继承的场供，其它类型表示当前桌上的场供。 |
| `scores` | 各家当前点数，整数。 |

下面是东四局中盘的一份完整 `metainfo`。宝牌指示牌有两张，说明这一局已经有人开过一次杠；南家已经立直成立，点数从 25000 扣到 24000，桌上多了 1 根场供；普通牌山还剩 23 张可摸。

```json
{
    "wind": "E",
    "round": 4,
    "dora_indicators": ["4m", "1z"],
    "ura_indicators": [],
    "remaining_tiles": 23,
    "honba": 0,
    "kyotaku": 1,
    "scores": {"east": 25000, "south": 24000, "west": 25000, "north": 25000}
}
```

### remaining_tiles

`remaining_tiles` 只统计普通摸牌还能摸的张数，不包括王牌区域（岭上牌和宝牌指示牌所在的 14 张）。四人 136 张牌时，配牌后亲家 14 张、其余三家 39 张，王牌 14 张，因此 `init` 的 `remaining_tiles` 为 `69`。

开杠后的岭上牌来自王牌，但为了让王牌保持 14 张，每次开杠都会让普通牌山的可摸张数减少 1。因此若开杠前 `remaining_tiles` 为 1，摸岭上牌后它变为 0，此后若无人和牌就会荒牌流局。

### 立直棒与点数守恒

立直棒按实时扣除处理：立直宣言牌打出后，若该牌没有被荣和，立直即成立，该玩家立即扣 1000 点，`kyotaku` 增加 1。若立直宣言牌被荣和，立直不成立，不扣点，`kyotaku` 也不增加。

四家点数之和加上场供点数始终守恒。默认 25000 点起局时：

```text
sum(scores.values()) + kyotaku * 1000 == 100000
```

使用其它起始点数时，右侧为 `4 * 起始点数`。本场只影响和牌时的额外支付，不改变点数总和，不计入该等式。

上面的 `metainfo` 示例中，`25000 + 24000 + 25000 + 25000 + 1 * 1000 = 100000`。

### final 中的 metainfo

`final` 的 `metainfo` 表示结算之后的状态。其中 `wind` 和 `round` 描述刚结束的这一小局，`honba`、`kyotaku` 和 `scores` 则是下一小局开局时应使用的值：

- `wind` 和 `round`：刚结束的这一小局，不推进到下一局。
- `honba`：下一小局的本场数。例如亲家连庄或流局时加 1，子家和牌时归零。
- `kyotaku`：下一小局继承的场供。和牌时场供被和牌者收走，归零；流局时场供保留，数值不变。
- `scores`：结算后的点数，也就是下一小局的起始点数。

因此，若有下一小局，它的 `init` 中 `honba`、`kyotaku`、`scores` 与本局 `final` 相同。

## players

`players` 固定包含 `east`、`south`、`west`、`north` 四个键，分别对应东、南、西、北家。在其它字段的值中引用玩家时，仍使用 `E`、`S`、`W`、`N`。

每个玩家对象包含：

| 字段 | 含义 |
| --- | --- |
| `hand` | 当前闭合手牌，顺序无关，按牌列表排序规则排列。 |
| `river` | 牌河，按打出顺序排列，下标从 `0` 开始。 |
| `tsumogiri_indices` | `river` 中摸切牌的下标列表。摸切指打出刚摸到的那张牌。 |
| `called_indices` | `river` 中被其他玩家鸣走的牌的下标列表。 |
| `riichi` | 立直是否已经成立。 |
| `riichi_declaration_index` | 立直宣言牌在 `river` 中的下标；仅在 `riichi` 为 `true` 且宣言牌仍在牌河中时出现。 |
| `melds` | 副露列表，按发生顺序从早到晚排列。 |

`hand` 是进入该 Snapshot 时玩家可用于决策的闭合手牌：

- 摸牌或摸岭上牌后，`hand` 已经包含刚摸到的牌；刚摸到的是哪一张由 `latest_action.tile` 给出。
- 吃、碰、杠后，组成副露的牌已经从 `hand` 中移除。同一张实体牌不会同时出现在 `hand` 和 `melds` 中。

被鸣走的牌允许保留在 `river` 中并记入 `called_indices`，也允许直接从 `river` 中移除；移除时无需在 `called_indices` 中记录。

`riichi_declaration_index` 只指实际的立直宣言牌。若宣言牌被鸣走，之后打出的下一张横置牌不算宣言牌。

下面是一位已经立直的玩家。他依次打出了 6 张牌：第 0 张 `9m` 是手切；第 1 张 `1z` 是摸切；第 2 张 `7p` 被别人鸣走，但仍留在牌河中；第 3 张 `3s` 手切；第 4 张 `4m` 摸切；第 5 张 `8p` 是立直宣言牌，立直已经成立。他门前没有副露，手牌 13 张：`123m`、`567p`、`234s` 三组顺子加白、发各一对，听白和发的双碰。

```json
{
    "hand": ["1m", "2m", "3m", "5p", "6p", "7p", "2s", "3s", "4s", "5z", "5z", "6z", "6z"],
    "river": ["9m", "1z", "7p", "3s", "4m", "8p"],
    "tsumogiri_indices": [1, 4],
    "called_indices": [2],
    "riichi": true,
    "riichi_declaration_index": 5,
    "melds": []
}
```

### 副露

副露对象必须有 `type` 和 `tiles`。`type` 允许 `chi`、`pon`、`open_kan`、`closed_kan`、`added_kan`。`tiles` 是组成该副露的全部牌。

除 `closed_kan` 外，副露还必须有：

| 字段 | 含义 |
| --- | --- |
| `called_tile` | 从其他玩家处鸣来的那张牌。 |
| `from` | 这张牌来自哪一家，使用 `E`、`S`、`W`、`N`。 |

`added_kan` 由先前的碰加一张手牌而成。它的 `called_tile` 和 `from` 沿用最初碰的那张牌及其来源，而不是加杠时从手牌加入的牌。

下面是东家的 `melds`，按发生顺序排列：

1. 吃了北家（东家的上家）打出的 `3m`，组成 `2m3m4m`。
2. 碰了西家打出的 `7p`，之后又摸到第四张 `7p` 加杠，所以记为 `added_kan`，`called_tile` 和 `from` 仍是当初碰的那张 `7p` 和西家。
3. 用手里的四张 `9p` 暗杠，暗杠没有鸣来的牌，所以没有 `called_tile` 和 `from`。

```json
[
    {"type": "chi", "tiles": ["2m", "3m", "4m"], "called_tile": "3m", "from": "N"},
    {"type": "added_kan", "tiles": ["7p", "7p", "7p", "7p"], "called_tile": "7p", "from": "W"},
    {"type": "closed_kan", "tiles": ["9p", "9p", "9p", "9p"]}
]
```

碰和大明杠的写法与吃相同，例如碰南家的白、大明杠西家的 `8s`：

```json
{"type": "pon", "tiles": ["5z", "5z", "5z"], "called_tile": "5z", "from": "S"}
```

```json
{"type": "open_kan", "tiles": ["8s", "8s", "8s", "8s"], "called_tile": "8s", "from": "W"}
```

## latest_action

`latest_action` 是进入该 Snapshot 前的最后一个动作，只保留理解当前决策所需的最小信息。不同 Snapshot 类型允许的动作不同。

### discard_decision

| `latest_action.type` | 必填字段 | 含义 |
| --- | --- | --- |
| `deal` | `player`, `tile` | 玩家普通摸牌后进入决策。 |
| `replacement` | `player`, `tile` | 玩家开杠后摸岭上牌，进入决策。 |
| `chi` | `player` | 玩家吃牌后进入切牌决策。 |
| `pon` | `player` | 玩家碰牌后进入切牌决策。 |

**摸牌后。** 东家切牌后无人鸣牌，轮到南家从牌山摸牌，摸到 `7p`。南家的 `hand` 此时已经包含这张 `7p`，共 14 张；`latest_action.tile` 指明哪一张是刚摸的，南家若随后切出它就是摸切。南家可以切牌、立直、暗杠、加杠或自摸。

```json
{
    "type": "discard_decision",
    "latest_action": {"type": "deal", "player": "S", "tile": "7p"}
}
```

**碰牌后。** 东家打出 `7z`（中），北家碰。北家跳过南家、西家直接取得行动权，碰后不摸牌，只能切牌。`latest_action` 只说明是北家碰了牌，不带 `tile`：碰的是哪张、来自谁，可以从北家 `melds` 的最后一项读出。吃牌后的局面写法相同，`type` 改为 `chi`。

```json
{
    "type": "discard_decision",
    "latest_action": {"type": "pon", "player": "N"},
    "players": {
        "north": {
            "melds": [{"type": "pon", "tiles": ["7z", "7z", "7z"], "called_tile": "7z", "from": "E"}]
        }
    }
}
```

**开杠后摸岭上牌。** 西家用手里的四张 `9p` 暗杠，然后从王牌摸岭上牌，摸到 `2p`，接着由西家继续决策。本例按暗杠后立即翻开新宝牌指示牌的规则，进入该局面时已经翻开第二张指示牌 `1z`；`remaining_tiles` 因开杠比杠前少 1。

```json
{
    "type": "discard_decision",
    "latest_action": {"type": "replacement", "player": "W", "tile": "2p"},
    "metainfo": {"dora_indicators": ["4m", "1z"], "remaining_tiles": 40},
    "players": {
        "west": {
            "melds": [{"type": "closed_kan", "tiles": ["9p", "9p", "9p", "9p"]}]
        }
    }
}
```

### call_decision

| `latest_action.type` | 必填字段 | 含义 |
| --- | --- | --- |
| `discard` | `player`, `tile` | 玩家刚切出一张牌，其他玩家判断是否吃、碰、大明杠或荣和。 |
| `riichi_declaration` | `player`, `tile` | 玩家刚打出立直宣言牌，其他玩家判断是否吃、碰、大明杠或荣和。 |
| `added_kan` | `player`, `tile` | 玩家刚加杠，其他玩家判断是否抢杠荣和。`tile` 是加杠时加入的牌。 |
| `closed_kan` | `player`, `tile` | 玩家刚暗杠，有其他玩家可以用国士无双抢暗杠。仅出现在允许国士无双抢暗杠的规则中。`tile` 是暗杠的牌之一，有普通五时取普通五而不取红五。 |

`call_decision` 本身不记录谁可以操作、可以做什么；这些由各家手牌和规则判断。它只保证至少有一位其他玩家有可选的操作。

**普通切牌后。** 东家（亲家）打出 `7z`（中），并且至少有一位其他玩家可以对这张牌鸣牌或荣和，例如北家手里有两张中可以碰。若所有人都放弃，局面进入南家摸牌后的 `discard_decision`；若北家碰，进入上一节“碰牌后”的局面。

```json
{
    "type": "call_decision",
    "latest_action": {"type": "discard", "player": "E", "tile": "7z"}
}
```

**立直宣言牌打出后。** 南家宣告立直，打出宣言牌 `7p`，有其他玩家可以对它鸣牌或荣和。此时立直还没有成立：南家的 `riichi` 仍为 `false`，点数仍是 25000，`kyotaku` 也没有增加。

```json
{
    "type": "call_decision",
    "latest_action": {"type": "riichi_declaration", "player": "S", "tile": "7p"},
    "metainfo": {"kyotaku": 0, "scores": {"east": 25000, "south": 25000, "west": 26000, "north": 24000}},
    "players": {
        "south": {"riichi": false}
    }
}
```

之后分两种情况：

- 无人荣和这张牌（包括有人吃、碰、大明杠）：立直成立，下一个 Snapshot 中南家 `riichi` 为 `true`，点数变为 24000，`kyotaku` 变为 1。
- 有人荣和这张牌：立直不成立，南家不扣点，直接进入 `final`。

**加杠后。** 西家把第四张 `7p` 加到已有的碰上，有其他玩家可以用这张 `7p` 抢杠荣和。若无人抢杠，西家接着摸岭上牌，进入 `replacement` 后的 `discard_decision`。若一开始就无人能抢杠，不会生成这个 `call_decision`。

```json
{
    "type": "call_decision",
    "latest_action": {"type": "added_kan", "player": "W", "tile": "7p"}
}
```

### final

| `latest_action.type` | 必填字段 | 含义 |
| --- | --- | --- |
| `tsumo` | `player`, `tile`, `yaku` | 自摸结束。`tile` 是和牌牌。 |
| `ron` | `players`, `tile`, `yaku` | 荣和结束。`tile` 是和牌牌；`players` 是荣和者列表，单人荣和时也写成列表。 |
| `draw` | `draw_type` | 流局结束，不带 `player` 和 `tile`。荒牌流局时还需带 `ready_players`。 |

**自摸。** 东一局，东家立直后一发自摸 `3p`。`yaku` 只写一发：立直、门前清自摸和等役可以从局面推断，不写。结算后的 `metainfo` 中，立直者和牌翻开了里宝牌指示牌 `8p`；东家收走场供，下一局没有场供可继承，`kyotaku` 为 0；亲家和牌连庄，下一局是东一局一本场，所以 `honba` 为 1。

```json
{
    "type": "final",
    "latest_action": {"type": "tsumo", "player": "E", "tile": "3p", "yaku": ["one_shot"]},
    "metainfo": {
        "ura_indicators": ["8p"],
        "honba": 1,
        "kyotaku": 0,
        "scores": {"east": 39000, "south": 21000, "west": 20000, "north": 20000}
    }
}
```

**荣和。** 北家打出的 `2s` 被西家荣和，西家没有需要记录的过程役。荣和者只有一位，`players` 仍写成列表；`yaku` 是与 `players` 按顺序对应的列表的列表，西家对应空列表。

```json
{
    "type": "final",
    "latest_action": {"type": "ron", "players": ["W"], "tile": "2s", "yaku": [[]]}
}
```

**一炮双响。** 东家打出的 `5p` 被南家和西家同时荣和。南家是一发荣和，西家没有需要记录的过程役。

```json
{
    "type": "final",
    "latest_action": {"type": "ron", "players": ["S", "W"], "tile": "5p", "yaku": [["one_shot"], []]}
}
```

**荒牌流局。** 南二局牌山摸尽，东家和西家听牌，南家和北家没听。`remaining_tiles` 为 0；流局时场供保留给下一局，`kyotaku` 仍为 1；亲家（东家）听牌连庄，下一局是南二局一本场，所以 `honba` 为 1。

```json
{
    "type": "final",
    "latest_action": {"type": "draw", "draw_type": "exhaustive", "ready_players": ["E", "W"]},
    "metainfo": {"remaining_tiles": 0, "honba": 1, "kyotaku": 1}
}
```

**途中流局。** 东家在 `init` 时宣告九种九牌，小局立即结束，没有人摸过牌，`remaining_tiles` 仍为 69。流局后本场加 1，下一局是东一局一本场，所以 `honba` 为 1。途中流局不需要 `ready_players`。

```json
{
    "type": "final",
    "latest_action": {"type": "draw", "draw_type": "nine_terminals"},
    "metainfo": {"remaining_tiles": 69, "honba": 1}
}
```

## 字段约束

### player / players

`player` 是单个玩家，取值为 `E`、`S`、`W`、`N`，除 `ron` 和 `draw` 外的动作都用它表示执行者。

`players` 只用于 `ron`，是荣和者列表，支持一炮多响；单人荣和时也是只含一个元素的列表。

`draw` 既不带 `player` 也不带 `players`。

### tile

以下动作必须带 `tile`：

```text
deal
replacement
discard
riichi_declaration
added_kan
tsumo
ron
```

`chi` 和 `pon` 不带 `tile`，被鸣的牌就是前一个 `call_decision` 中的弃牌，鸣牌结果可从 `players` 的副露中读出。`draw` 不带 `tile`。

### yaku

`yaku` 只用于 `tsumo` 和 `ron`，没有过程役时写空列表：

- `tsumo` 只有一位和牌者，`yaku` 是役名字符串列表。
- `ron` 的 `yaku` 是列表的列表，与 `players` 按顺序一一对应，单人荣和时外层列表也只有一个元素。

自摸，两立直后一发：

```json
{"player": "E", "yaku": ["double_riichi", "one_shot"]}
```

南家、西家双响，南家一发，西家两立直：

```json
{"players": ["S", "W"], "yaku": [["one_shot"], ["double_riichi"]]}
```

`yaku` 只记录无法从和牌时的手牌、牌河和场况稳定推断的过程役，目前支持：

| 名称 | 含义 |
| --- | --- |
| `double_riichi` | 两立直。 |
| `one_shot` | 一发。 |
| `after_a_kan` | 岭上开花。 |
| `robbing_a_kan` | 抢杠。 |

普通手役、立直，以及可由 `remaining_tiles` 等信息推断的海底摸月、河底捞鱼等役不写入 `yaku`。

### draw_type

`draw_type` 只用于 `latest_action.type = "draw"`，允许值为：

| 值 | 含义 |
| --- | --- |
| `exhaustive` | 荒牌流局，牌山摸尽。 |
| `four_winds` | 四风连打。 |
| `four_riichi` | 四家立直。 |
| `four_kans` | 四杠散了。 |
| `three_ron` | 三家和了，仅用于把三家荣和算作流局的规则。 |
| `nine_terminals` | 九种九牌。 |

### ready_players

`ready_players` 只用于 `draw_type = "exhaustive"`，表示荒牌流局时听牌的玩家列表，可以为空列表（四家都没听）或包含全部四家（四家都听）：

```json
[]
```

```json
["E", "S", "W", "N"]
```
