# Mahjong Soul Standard (`majsoul_std`)

本页说明 Paifu 中 `rule = "majsoul_std"` 的含义，以及如何把雀魂牌谱转换成 Paifu。Paifu 的结构和字段定义见 [paifu.md](../paifu.md)，本页只描述雀魂特有的来源格式和映射规则，不改变 Paifu 的通用结构。

## 规则含义

`majsoul_std` 表示雀魂四人对局的标准规则。重放 `majsoul_std` 的 Paifu 时，牌山拆分、宝牌翻开、可执行操作、流局条件和结算方式都按雀魂规则处理。与 Paifu 格式直接相关的要点：

| 项目 | 约定 |
| --- | --- |
| 人数 | 四人。 |
| 牌数 | 136 张，`0m`、`0p`、`0s` 各一张红五。 |
| 起始点数 | 25000，点数守恒等式右侧为 `100000`。 |
| 王牌 | 14 张，其中岭上牌 4 张、宝牌指示牌 5 张、里宝牌指示牌 5 张。 |
| 普通牌山 | 配牌后剩余 69 张，即 Paifu `wall` 的长度。 |

## 雀魂牌谱的组成

转换一场雀魂牌谱需要两步：先从牌谱链接得到牌谱 ID，再通过雀魂的牌谱接口取得并解码完整记录。只解析链接不能得到牌谱内容。

### 牌谱链接

雀魂牌谱链接用 `paipu` 参数标识牌谱：

```text
https://game.maj-soul.com/1/?paipu=261001-7c1f7669-7c88-428f-be52-594120ef58d7_a94003061
```

| 字段 | 示例 | 含义 |
| --- | --- | --- |
| `paipu_id` | `261001-7c1f7669-7c88-428f-be52-594120ef58d7_a94003061` | 链接中完整的 `paipu` 参数。 |
| `record_uuid` | `261001-7c1f7669-7c88-428f-be52-594120ef58d7` | 下划线前的部分，即牌谱记录 UUID，用于请求完整记录。 |
| `account_suffix` | `a94003061` | 下划线后的部分，表示分享者的账号视角，只用于标识来源，不影响牌谱内容。 |
| `date_prefix` | `261001` | `record_uuid` 第一个连字符前的前缀。 |

### 解码记录

解码后的雀魂记录包含 `uuid`、`head` 和 `actions`。`head` 是整场对局的元信息（玩家、规则、开始时间等），`actions` 是按时间顺序排列的记录列表。每条记录有一个类型名和对应的数据：

| 雀魂记录 | 含义 | 转换时用到的字段 |
| --- | --- | --- |
| `.lq.RecordNewRound` | 开始一个小局。 | `chang`, `ju`, `ben`, `liqibang`, `scores`, `tiles0`–`tiles3`, `paishan` |
| `.lq.RecordDealTile` | 普通摸牌或摸岭上牌。 | `seat`, `tile`（仅用于校验） |
| `.lq.RecordDiscardTile` | 切牌，包括立直宣言牌。 | `seat`, `tile`, `moqie`, `is_liqi`, `is_wliqi`, `operations` |
| `.lq.RecordChiPengGang` | 吃、碰或大明杠。 | `seat`, `tiles`, `froms` |
| `.lq.RecordAnGangAddGang` | 暗杠或加杠。 | `seat`, `type`, `tiles` |
| `.lq.RecordHule` | 和牌，小局结束。 | `hules[].seat`, `hules[].zimo` |
| `.lq.RecordNoTile` | 荒牌流局，小局结束。 | 无 |
| `.lq.RecordLiuJu` | 途中流局，小局结束。 | 无 |

每条 `.lq.RecordNewRound` 开始一个 Paifu 小局对象，直到下一条 `.lq.RecordNewRound` 或记录结束。整场牌谱转换为这些小局对象按出现顺序组成的列表。

雀魂的牌 ID 与 Paifu 相同（`1m`、`0p`、`7z` 等），可以直接使用。

## 座位与风位

雀魂用固定的座位号 `0`、`1`、`2`、`3` 表示玩家，整场不变；Paifu 用当前小局的风位 `E`、`S`、`W`、`N`，每次换庄都会变化。

`RecordNewRound.ju` 是当前场风内从 `0` 开始的小局编号，庄家座位为：

```text
dealer_seat = ju % 4
```

座位到风位的映射：

```text
dealer_seat           -> E
(dealer_seat + 1) % 4 -> S
(dealer_seat + 2) % 4 -> W
(dealer_seat + 3) % 4 -> N
```

`scores`、`initial_hands`、决策执行者、鸣牌来源和和牌者都要按此映射从座位号转换成风位。例如南二局（`chang = 1, ju = 1`）的庄家是座位 `1`，座位 `0` 是北家。

## metainfo 映射

`RecordNewRound` 到 Paifu `metainfo` 的映射：

| Paifu 字段 | 雀魂字段 | 说明 |
| --- | --- | --- |
| `wind` | `chang` | 从 `0` 开始的场风编号，`0` 至 `3` 分别映射为 `E`、`S`、`W`、`N`。缺省为 `0`。 |
| `round` | `ju` | 从 `0` 开始的小局编号，写入时加 1。缺省为 `0`。 |
| `honba` | `ben` | 本场数。缺省为 `0`。 |
| `kyotaku` | `liqibang` | 场供立直棒根数。缺省为 `0`。 |
| `scores` | `scores` | 按座位排列的点数数组，转换为以 `east`、`south`、`west`、`north` 为键的对象。 |

`rule` 固定写为 `"majsoul_std"`。

示例：

```json
{
    "chang": 1,
    "ju": 3,
    "ben": 2,
    "scores": [9600, 36100, 27600, 26700]
}
```

`ju = 3` 时庄家是座位 `3`，因此座位 `3`、`0`、`1`、`2` 依次是东、南、西、北家。`liqibang` 缺省，按 `0` 处理：

```json
{
    "wind": "S",
    "round": 4,
    "honba": 2,
    "kyotaku": 0,
    "scores": {
        "east": 26700,
        "south": 9600,
        "west": 36100,
        "north": 27600
    }
}
```

## tiles 映射

### initial_hands

`RecordNewRound.tiles0` 至 `tiles3` 是四个座位的起手牌。雀魂中亲家的起手牌已经是 14 张，与 Paifu 中亲家 14 张起手牌一致，开局后的第一条记录就是亲家的 `RecordDiscardTile`（或暗杠、和牌、流局），没有摸牌记录。写入 `initial_hands` 时先转换到风位，再按牌列表排序规则排序。

### 由 paishan 拆分牌序

`RecordNewRound.paishan` 是整副 136 张牌的排列，以牌 ID 首尾相接的字符串表示。按下标拆分为：

| 下标范围 | Paifu 字段 | 含义 |
| --- | --- | --- |
| `0:52` | `initial_hands` | 四家各 13 张起手牌。 |
| `52` | `initial_hands.east` | 亲家的第 14 张起手牌，不写入 `wall`。 |
| `53:122` | `wall` | 69 张普通摸牌序列，`wall[0]` 即 `paishan[53]`。 |
| `122:136` | 王牌 | 14 张，用于生成 `rinshan`、`dora_indicators`、`ura_indicators`。 |

把王牌记为 `dead_wall = paishan[122:136]`，映射为：

```text
rinshan         = [dead_wall[13], dead_wall[12], dead_wall[11], dead_wall[10]]
dora_indicators = [dead_wall[9], dead_wall[7], dead_wall[5], dead_wall[3], dead_wall[1]]
ura_indicators  = [dead_wall[8], dead_wall[6], dead_wall[4], dead_wall[2], dead_wall[0]]
```

`wall`、`rinshan`、`dora_indicators`、`ura_indicators` 保持上述顺序，不排序，并且总是写满 69、4、5、5 张，与该小局实际用到多少张无关。

`RecordDealTile` 不写入 Paifu。转换时可以用它校验：每条普通摸牌记录的 `tile` 应等于重放从 `wall` 取出的下一张，每条岭上摸牌记录的 `tile` 应等于 `rinshan` 的下一张。

## decisions 映射

转换时需要同步重放：按 Paifu 规则维护当前局面，才能判断某张切牌是否摸切、某个时刻是否生成 `call_decision`。雀魂记录与 Paifu decision 的对应关系：

| 雀魂记录 | Paifu decision |
| --- | --- |
| `RecordDiscardTile`，`is_liqi` 和 `is_wliqi` 都不为真 | `discard` |
| `RecordDiscardTile`，`is_liqi` 或 `is_wliqi` 为真 | `riichi_declaration` |
| `RecordChiPengGang` | `chi`、`pon` 或 `open_kan` |
| `RecordAnGangAddGang` | `closed_kan` 或 `added_kan` |
| `RecordHule` | `tsumo` 或 `ron` |
| `RecordNoTile`、`RecordLiuJu` | `draw` |
| 重放生成了 `call_decision`，但下一条记录不是鸣牌、杠或和牌 | `pass` |
| `RecordDealTile` | 不写入 |

### discard

```json
{
    "seat": 3,
    "tile": "7z",
    "moqie": false
}
```

转换为：

```json
{"type": "discard", "tile": "7z", "from": "hand"}
```

`tile` 直接取雀魂的 `tile`。`from` 由雀魂的 `moqie`（摸切）决定，并应与重放状态一致：

| 情况 | `from` |
| --- | --- |
| `moqie` 为真，切出刚摸到的普通摸牌或岭上牌 | `deal` |
| `moqie` 为假，切出原有手牌 | `hand` |
| 亲家第一次切牌，或吃、碰后的切牌 | `hand` |

### riichi_declaration

`is_liqi` 为真表示立直宣言牌；`is_wliqi` 为真表示两立直的宣言牌，两立直由重放根据时机判断，Paifu 中同样写为 `riichi_declaration`。

```json
{
    "seat": 1,
    "tile": "3s",
    "moqie": true,
    "is_liqi": true
}
```

转换为：

```json
{"type": "riichi_declaration", "tile": "3s", "from": "deal"}
```

`from` 的判断方式与 `discard` 相同。

### chi / pon / open_kan

`RecordChiPengGang` 的 `tiles` 是组成副露的全部牌，`froms` 与 `tiles` 等长，给出每张牌来自哪个座位。等于执行者 `seat` 的是自己手牌中拿出的牌，其余那一张是被鸣的弃牌：

```text
hands  = sorted(tile for tile, from_seat in zip(tiles, froms) if from_seat == seat)
tile   = 唯一一张 from_seat != seat 的牌
player = seat 映射得到的风位
```

`type` 按副露形状确定：顺子为 `chi`，三张相同为 `pon`，四张相同为 `open_kan`。

```json
{
    "seat": 0,
    "tiles": ["5p", "6p", "7p"],
    "froms": [0, 0, 3]
}
```

若座位 `0` 是南家，转换为：

```json
{"type": "chi", "player": "S", "hands": ["5p", "6p"], "tile": "7p"}
```

碰和大明杠同理：

```json
{"type": "pon", "player": "N", "hands": ["7z", "7z"], "tile": "7z"}
```

```json
{"type": "open_kan", "player": "W", "hands": ["8s", "8s", "8s"], "tile": "8s"}
```

### closed_kan / added_kan

`RecordAnGangAddGang.type = 2` 表示暗杠，写为 `closed_kan`；其它值表示加杠，写为 `added_kan`。雀魂的 `tiles` 只给出杠的牌种，Paifu 的 `hands` 需要结合重放中的当前手牌确定具体用到的牌（包括是否含红五）：

- `closed_kan`：`hands` 是从手牌中拿出的四张牌。
- `added_kan`：`hands` 是从手牌中加到已有碰上的那一张牌。

```json
{"type": "closed_kan", "hands": ["0p", "5p", "5p", "5p"]}
```

```json
{"type": "added_kan", "hands": ["7p"]}
```

### pass

`pass` 由重放判断：重放在某张弃牌或加杠之后生成了 `call_decision`，而雀魂的下一条记录不是 `RecordChiPengGang`、`RecordHule`，就写一条 `pass`。

```json
{"type": "pass"}
```

雀魂 `RecordDiscardTile.operations` 列出了这张弃牌给其他玩家的可选操作，可以用来校验：`operations` 非空时重放应生成 `call_decision`，为空时不应生成，也不写 `pass`。

### tsumo / ron

`RecordHule.hules` 列出每位和牌者。所有和牌者的 `zimo` 都为真时写为 `tsumo`：

```json
{"type": "tsumo"}
```

否则写为 `ron`，`players` 由 `hules[].seat` 按出现顺序转换为风位，支持双响和三响：

```json
{"type": "ron", "players": ["S", "W"]}
```

雀魂记录中的役种、符数和点数变化不写入 Paifu，可用于校验重放的结算结果。

### draw

`RecordNoTile`（荒牌流局）和 `RecordLiuJu`（九种九牌、四风连打、四杠散了、四家立直等途中流局）都写为：

```json
{"type": "draw"}
```

九种九牌对应玩家在决策点的主动宣告；其它流局是重放自动触发的，Paifu 仍以这条 `draw` 结尾。流局类型、听牌玩家和点数变化由重放推导，雀魂记录中的对应字段可用于校验。

## 完整示例

以下雀魂记录片段（南四局，`ju = 3`，座位 `3` 为亲家；每条记录写成类型名加数据的示意结构，省略无关字段）：

```json
[
    {"name": ".lq.RecordDiscardTile", "data": {"seat": 3, "tile": "7z", "moqie": false}},
    {"name": ".lq.RecordChiPengGang", "data": {"seat": 2, "tiles": ["7z", "7z", "7z"], "froms": [2, 2, 3]}},
    {"name": ".lq.RecordDiscardTile", "data": {"seat": 2, "tile": "3z", "moqie": false}},
    {"name": ".lq.RecordDealTile", "data": {"seat": 3, "tile": "7p"}},
    {"name": ".lq.RecordDiscardTile", "data": {"seat": 3, "tile": "7p", "moqie": true}},
    {"name": ".lq.RecordChiPengGang", "data": {"seat": 0, "tiles": ["5p", "6p", "7p"], "froms": [0, 0, 3]}},
    {"name": ".lq.RecordDiscardTile", "data": {"seat": 0, "tile": "9p", "moqie": false}},
    {"name": ".lq.RecordDealTile", "data": {"seat": 1, "tile": "4p"}}
]
```

座位 `3`、`0`、`1`、`2` 依次映射为 `E`、`S`、`W`、`N`。最后一条切牌 `9p` 之后北家可以碰，重放生成了 `call_decision`，但下一条记录是西家摸牌，因此补一条 `pass`。转换得到的 `decisions` 开头为：

```json
[
    {"type": "discard", "tile": "7z", "from": "hand"},
    {"type": "pon", "player": "N", "hands": ["7z", "7z"], "tile": "7z"},
    {"type": "discard", "tile": "3z", "from": "hand"},
    {"type": "discard", "tile": "7p", "from": "deal"},
    {"type": "chi", "player": "S", "hands": ["5p", "6p"], "tile": "7p"},
    {"type": "discard", "tile": "9p", "from": "hand"},
    {"type": "pass"}
]
```

这正是 [paifu.md](../paifu.md) 顶层结构示例中的 `decisions`。
