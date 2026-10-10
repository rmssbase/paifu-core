# Paifu Format

Paifu 是 paifu-core 约定的压缩牌谱格式，面向大规模保存、重放和统计分析。它的命名和局面语义建立在以下两份文档之上：

- [terminology.md](terminology.md)：牌 ID、风位、动作名、役种名和牌列表排序规则。
- [snapshot.md](snapshot.md)：标准局面格式 Snapshot，以及 `init`、`discard_decision`、`call_decision`、`final` 四种决策点。

## 设计目的：只记录最小事实

一个小局通常包含上百个 Snapshot 决策点，每个 Snapshot 都完整写出四家手牌、牌河、副露和场况。如果逐个保存，相邻 Snapshot 之间绝大部分内容是重复的。

但在给定规则下，一个小局的全部进程只由三类事实决定：

1. 起局场况：场风、局数、本场、场供、各家点数。
2. 牌序：起手牌、牌山的摸牌顺序、岭上牌、宝牌和里宝牌指示牌。
3. 每个决策点上玩家的选择。

其余信息都可以按规则推导出来，例如谁在什么时候摸到哪张牌、何时翻开新宝牌、某张弃牌能否被鸣、和了的役种和点数、流局类型和听牌罚符。Paifu 因此只保存这三类事实，用重放（replay）还原出完整的 Snapshot 序列。这样既能把体积压缩到完整局面序列的很小一部分，也避免冗余字段之间互相矛盾。

## 顶层结构

一个 Paifu 对象固定包含两个顶层字段，顺序为 `rule`、`rounds`。`rounds` 是小局对象列表，按发生顺序排列；只有一个小局时也写成单元素列表，因此一个小局和一整场牌局的格式完全一致。同一场牌局的所有小局使用同一规则，所以 `rule` 只在顶层写一次。

每个小局对象固定包含三个字段，顺序为 `metainfo`、`tiles`、`decisions`：

```json
{
    "rule": "majsoul_std",
    "rounds": [
        {
            "metainfo": {
                "wind": "S",
                "round": 4,
                "honba": 2,
                "kyotaku": 0,
                "scores": {"east": 26700, "south": 9600, "west": 36100, "north": 27600}
            },
            "tiles": {
                "initial_hands": {
                    "east": ["3m", "3m", "6m", "8m", "1p", "2p", "4p", "0p", "6p", "1s", "1z", "2z", "2z", "7z"],
                    "south": ["4m", "1p", "3p", "5p", "6p", "9p", "3s", "8s", "8s", "8s", "9s", "1z", "7z"],
                    "west": ["1m", "0m", "6m", "6m", "8m", "1p", "2p", "3p", "3p", "4p", "6p", "9s", "1z"],
                    "north": ["5m", "6m", "9m", "3p", "9p", "9p", "7s", "3z", "5z", "6z", "6z", "7z", "7z"]
                },
                "wall": ["7p", "4p", "3m", "2s"],
                "rinshan": ["2p", "7s", "2s", "1z"],
                "dora_indicators": ["2m", "1m", "4s", "6s", "6z"],
                "ura_indicators": ["7m", "7m", "4s", "8p", "6s"]
            },
            "decisions": [
                {"type": "discard", "tile": "7z", "from": "hand"},
                {"type": "pon", "player": "N", "hands": ["7z", "7z"], "tile": "7z"},
                {"type": "discard", "tile": "3z", "from": "hand"},
                {"type": "discard", "tile": "7p", "from": "deal"},
                {"type": "chi", "player": "S", "hands": ["5p", "6p"], "tile": "7p"},
                {"type": "discard", "tile": "9p", "from": "hand"},
                {"type": "pass"}
            ]
        }
    ]
}
```

示例只有一个小局，`wall` 和 `decisions` 也只截取开头几项。真实 Paifu 必须保存完整的牌序，`decisions` 一直记录到小局结束。

`rounds` 中相邻两个小局必须衔接：后一小局的 `honba`、`kyotaku` 与前一小局 Snapshot `final` 的值相同；场风和局数按连庄或轮庄推进；`scores` 也与前一小局 `final` 相同，但换庄时风位整体顺移，前一小局的南家成为后一小局的东家，其余依此类推。

这是南四局二本场，东家是亲家。这段 `decisions` 的重放过程是：

1. 重放构造出 `init`：东家持 14 张，第一条 decision 是东家手切 `7z`（中）。北家手里有两张中，可以碰，于是生成 `call_decision`。
2. 第二条 decision 回答这个 `call_decision`：北家用两张 `7z` 碰东家的 `7z`。北家碰后不摸牌，直接进入切牌决策。
3. 第三条 decision 是北家手切 `3z`。没有人能对 `3z` 鸣牌或荣和，因此不生成 `call_decision`，也不需要 `pass`。
4. 北家的下家是东家。东家从 `wall[0]` 摸到 `7p`，这一步没有选择余地，不写入 `decisions`。第四条 decision 是东家把刚摸到的 `7p` 摸切。南家有 `5p`、`6p` 可以吃，生成 `call_decision`。
5. 第五条 decision：南家用 `5p`、`6p` 吃 `7p`，进入切牌决策。
6. 第六条 decision：南家手切 `9p`。北家有两张 `9p` 可以碰，生成 `call_decision`。
7. 第七条 decision 是 `pass`：北家选择不碰。
8. 轮到西家，从 `wall[1]` 摸到 `4p`，进入下一个决策点……

## rule

`rule` 指明重放使用的规则，决定牌山拆分、宝牌翻开时机、可执行的操作、流局条件和结算方式。目前支持的取值，都指四人段位场半庄规则：

| 值 | 含义 |
| --- | --- |
| `majsoul_std` | 雀魂四人段位场规则，见 [game_protocol/majsoul_std.md](game_protocol/majsoul_std.md)。 |
| `tenhou_std` | 天凤四人段位场规则，见 [game_protocol/tenhou_std.md](game_protocol/tenhou_std.md)。 |

Paifu 不带 `version` 字段。

## metainfo

每个小局的 `metainfo` 只记录起局时的场况，含义与 Snapshot 的同名字段一致。字段顺序固定为 `wind`、`round`、`honba`、`kyotaku`、`scores`。

| 字段 | 含义 |
| --- | --- |
| `wind` | 场风，允许 `E`、`S`、`W`、`N`。 |
| `round` | 当前场风内第几小局，允许 `1` 至 `4`。 |
| `honba` | 起局本场数。 |
| `kyotaku` | 起局场供立直棒根数。 |
| `scores` | 起局各家点数。 |

Snapshot `metainfo` 中的 `dora_indicators`、`ura_indicators`、`remaining_tiles` 都可以由 `tiles` 和重放进度推导，因此不在这里记录。点数守恒与 Snapshot 相同：

```text
sum(scores.values()) + kyotaku * 1000 == 4 * 起始点数
```

## tiles

`tiles` 记录重放需要的全部牌序。字段顺序固定为 `initial_hands`、`wall`、`rinshan`、`dora_indicators`、`ura_indicators`。

| 字段 | 含义 |
| --- | --- |
| `initial_hands` | 起手牌，以 `east`、`south`、`west`、`north` 为键。亲家 14 张，其余三家各 13 张，即 Snapshot `init` 中的手牌。 |
| `wall` | 普通摸牌序列，`wall[0]` 是开局后第一次 `deal` 摸到的牌。亲家的第 14 张起手牌已在 `initial_hands` 中，不放入 `wall`。 |
| `rinshan` | 岭上牌序列，第一次开杠后的 `replacement` 摸 `rinshan[0]`。 |
| `dora_indicators` | 宝牌指示牌序列，按翻开顺序排列；开局翻开 `dora_indicators[0]`，之后每次开杠按规则翻开下一张。 |
| `ura_indicators` | 里宝牌指示牌序列，与 `dora_indicators` 一一对应。 |

`initial_hands` 是顺序无关列表，按牌列表排序规则排列。其余四个字段是顺序相关列表，按重放消耗或翻开的顺序保存，不排序。为了减小体积并便于人工扫描，牌列表在 JSON 中写成单行数组。

`wall`、`rinshan`、`dora_indicators`、`ura_indicators` 应保存规则下完整的牌序，即使该小局实际没有用到全部牌。这样 Paifu 记录的是整副牌的排列，而不只是本局看到的部分。

## decisions

`decisions` 是决策结果的列表。重放从 `metainfo` 和 `tiles` 构造出 Snapshot `init`，然后每遇到一个决策点就按顺序消费一条 decision，直到小局结束。摸牌、摸岭上牌、翻宝牌这类没有选择余地的过程不写入 `decisions`。

每种决策点能接受的 decision：

| Snapshot 决策点 | 可接受的 decision |
| --- | --- |
| `init` | `discard`、`riichi_declaration`、`closed_kan`、`tsumo`、`draw` |
| 摸牌或摸岭上牌后的 `discard_decision` | `discard`、`riichi_declaration`、`closed_kan`、`added_kan`、`tsumo`、`draw` |
| 吃、碰后的 `discard_decision` | `discard` |
| 弃牌后的 `call_decision` | `chi`、`pon`、`open_kan`、`ron`、`pass`；规则把三家和了算作流局时还可以是 `draw` |
| 加杠后的 `call_decision` | `ron`、`pass` |
| 暗杠后的 `call_decision`（仅限允许国士无双抢暗杠的规则） | `ron`、`pass` |

一个 `call_decision` 无论涉及几位可操作的玩家，都只对应一条 decision，记录最终生效的结果。

Paifu 不保存役种、符数、结算点数、流局类型等结果，这些都由重放根据 `rule`、牌序和决策推导。

### 谁在执行 decision

decision 一般不写执行者，因为重放知道当前轮到谁：`init` 和 `discard_decision` 中只有一位玩家在决策。只有回答 `call_decision` 的 decision 需要写明执行者，因为可能有多位玩家可以操作：`chi`、`pon`、`open_kan` 用 `player` 写一位玩家，`ron` 用 `players` 写一位或多位玩家。

### discard

当前玩家切出一张牌。

| 字段 | 含义 |
| --- | --- |
| `tile` | 切出的牌。红五必须写成 `0m`、`0p`、`0s`。 |
| `from` | 这张牌的来源：`deal` 表示摸切，即切出刚摸到的牌（普通摸牌或岭上牌）；`hand` 表示手切，即切出原有手牌。 |

南家摸到 `7p`，手里原本也有一张 `7p`。两种切法的 `tile` 都是 `7p`，只能靠 `from` 区分。切出刚摸到的那张是摸切：

```json
{"type": "discard", "tile": "7p", "from": "deal"}
```

留下刚摸的牌、切出原有的那张是手切：

```json
{"type": "discard", "tile": "7p", "from": "hand"}
```

重放据此生成 Snapshot 的 `tsumogiri_indices`。亲家在 `init` 的第一次切牌，以及吃、碰后的切牌，都没有刚摸到的牌，`from` 一律为 `hand`。

### riichi_declaration

当前玩家宣告立直并打出立直宣言牌。字段与 `discard` 完全相同。

西家摸到 `3s` 后听牌，宣告立直并把 `3s` 摸切作为宣言牌：

```json
{"type": "riichi_declaration", "tile": "3s", "from": "deal"}
```

重放随后生成 `latest_action` 为 `riichi_declaration` 的局面。宣言牌没有被荣和时，立直成立，西家扣 1000 点，场供增加 1 根；被荣和时立直不成立。两立直、一发等过程役由重放根据立直时机判断，不额外记录。

### chi / pon

有玩家吃或碰上一张弃牌。

| 字段 | 含义 |
| --- | --- |
| `player` | 执行吃或碰的玩家，使用 `E`、`S`、`W`、`N`。被鸣的弃牌来自谁由重放得知，不记录。 |
| `hands` | 该玩家从自己手牌中拿出的牌，按牌列表排序规则排列。 |
| `tile` | 被鸣走的弃牌。 |

东家摸切 `7p`，南家（东家的下家）用手里的 `5p`、`6p` 吃：

```json
{"type": "chi", "player": "S", "hands": ["5p", "6p"], "tile": "7p"}
```

东家打出 `7z`（中），北家用手里两张中碰：

```json
{"type": "pon", "player": "N", "hands": ["7z", "7z"], "tile": "7z"}
```

`hands` 和 `tile` 必须分开记录，以区分不同的吃法。比如南家手里有 `2p`、`3p`、`4p`，东家打出 `3p`、`4p` 都可能被吃，以下是两个不同的决策：

```json
{"type": "chi", "player": "S", "hands": ["2p", "3p"], "tile": "4p"}
```

```json
{"type": "chi", "player": "S", "hands": ["2p", "4p"], "tile": "3p"}
```

同理，手里同时有 `5p` 和 `0p` 时，`hands` 要写明用的是哪一张，因为这决定了红宝牌留在手里还是进入副露。

### open_kan

大明杠。字段含义与 `chi`、`pon` 相同，`hands` 是从自己手牌中拿出的三张牌。

南家打出 `8s`，西家用手里三张 `8s` 大明杠。杠后的岭上摸牌和新宝牌翻开由重放自动完成：

```json
{"type": "open_kan", "player": "W", "hands": ["8s", "8s", "8s"], "tile": "8s"}
```

### closed_kan / added_kan

暗杠和加杠由当前玩家在自己的决策点执行，不涉及上一张弃牌，因此没有 `player` 和 `tile`，只用 `hands` 记录从手牌中拿出的牌。

暗杠，`hands` 是四张牌。手里有一张红五时，红五也写在 `hands` 里：

```json
{"type": "closed_kan", "hands": ["0p", "5p", "5p", "5p"]}
```

加杠，`hands` 是加到已有碰上的那一张牌。例如之前碰过 `7p`，现在摸到第四张 `7p` 加杠：

```json
{"type": "added_kan", "hands": ["7p"]}
```

加杠后若有人可以抢杠，重放会生成 `call_decision`，下一条 decision 为 `ron` 或 `pass`；若无人可以抢杠，重放直接让该玩家摸岭上牌。暗杠一般不能被抢；只有规则允许国士无双抢暗杠（如 `majsoul_std`）且有人能用国士无双荣和这张牌时，暗杠后才会生成 `call_decision`。

### ron

一位或多位玩家荣和上一张弃牌或被抢的杠牌。`players` 列出所有荣和的玩家，支持一炮多响。三家同时荣和按规则处理：`majsoul_std` 三家都和牌；`tenhou_std` 记为三家和了流局，此时写 `ron` 列出三家或直接写 `draw` 都可以，重放结果相同。和牌牌就是该 `call_decision` 中的那张牌，不重复记录。

北家打出的牌被西家荣和：

```json
{"type": "ron", "players": ["W"]}
```

东家打出的牌同时被南家和西家荣和（一炮双响）：

```json
{"type": "ron", "players": ["S", "W"]}
```

### tsumo

当前玩家自摸和牌。自摸的玩家就是当前决策者，和牌牌就是他刚摸到的牌，都由重放确定，不重复记录。

```json
{"type": "tsumo"}
```

天和时亲家没有刚摸到的牌（`initial_hands` 不区分哪一张是第 14 张），重放按高点法在 14 张中选和牌牌：先比打点，打点相同时优先能算双倍役满的解释（即使规则不计双倍役满，例如 `tenhou_std`），再比番数、符数，仍相同时取排序最前的牌。例如天和国士无双一律记为国士无双十三面，天和四暗刻一律记为四暗刻单骑，各规则下选出的和牌牌相同，但可能与平台记录的实际第 14 张不同。

### pass

重放生成了 `call_decision`，但所有可操作的玩家都选择不鸣牌、不荣和。

南家打出 `9p`，北家可以碰但没有碰，其他人也没有操作：

```json
{"type": "pass"}
```

若一张弃牌或加杠无人可以操作，重放不会生成 `call_decision`，也就不记录 `pass`。

### draw

小局以流局结束。

```json
{"type": "draw"}
```

`draw` 有两种出现方式：

- 九种九牌是玩家的主动选择。例如亲家在 `init` 时手里有九种以上幺九牌并宣告流局，`decisions` 的第一条就是 `draw`。
- 荒牌流局、四风连打、四家立直、四杠散了、三家和了（仅 `tenhou_std`）是规则自动触发的流局，不是玩家选择。重放走到这类流局时，Paifu 仍以一条 `draw` 结尾，使每个小局都以明确的结束记录收尾，便于校验。例如牌山最后一张被切出、无人荣和后，最后一条是 `draw`。

流局类型、听牌玩家和点数变化都由重放推导。

## 结束记录

每个小局的 `decisions` 以且仅以 `tsumo`、`ron` 或 `draw` 中的一条结尾。重放在消费完这条记录后生成 Snapshot `final`，此时 `decisions` 应恰好被消费完。
