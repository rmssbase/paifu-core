# Terminology

本页整理日麻通用术语在 paifu-core 中使用的英文或罗马音名称，适合在阅读或编写 paifu-core 数据前统一命名。

## 命名原则

名称一律使用英语 snake_case，不混入中文拼音。只有下列日麻术语保留罗马音，因为它们在日麻语境中比英文译名更常用：

| 罗马音 | 中文 |
| --- | --- |
| `chi` | 吃 |
| `pon` | 碰 |
| `kan` | 杠 |
| `tsumo` | 自摸 |
| `ron` | 荣和 |
| `riichi` | 立直 |
| `tsumogiri` | 摸切 |
| `honba` | 本场 |
| `kyotaku` | 场供 |
| `dora` | 宝牌 |
| `ura` | 里宝牌 |
| `aka` | 赤宝牌 |
| `rinshan` | 岭上牌 |
| `yaku` | 役 |

这些罗马音可以与英语组合成名称，例如 `riichi_declaration`、`tsumogiri_indices`、`dora_indicators`、`double_riichi`。除此之外的名称都使用英语，例如听牌者记为 `ready_players`。

其它约定：

| 类别 | 约定 | 示例 | 备注 |
| --- | --- | --- | --- |
| 摸牌与流局 | 摸牌用 `deal`，流局用 `draw` | `deal`, `draw` | 两者不混用。 |
| 单复数 | 可能包含多个元素的列表字段用复数名 | `players`, `hands`, `melds`, `ready_players` | 即使列表只有一个元素也用复数名；单个值用单数名，例如 `player`、`tile`。 |
| 玩家风位 | 作为 key 用全称，作为 value 用字母 | key：`east`；value：`E` | 见下一节。 |
| 牌 | 使用紧凑牌 ID | `1m`, `0p`, `7z` | `0m`/`0p`/`0s` 表示红五。 |

## 玩家风位

| key | value | 中文 | 备注 |
| --- | --- | --- | --- |
| `east` | `E` | 东家 | 本小局的亲家。 |
| `south` | `S` | 南家 | 亲家的下家。 |
| `west` | `W` | 西家 | 亲家的对家。 |
| `north` | `N` | 北家 | 亲家的上家。 |

以玩家为索引的对象（如各家点数、各家手牌）用全称作 key；在值中引用玩家时（如动作执行者、牌的来源、听牌者列表）用单个字母。

```json
{
    "scores": {"east": 26700, "south": 9600, "west": 36100, "north": 27600},
    "ready_players": ["E", "W"]
}
```

场风也用 `E`、`S`、`W`、`N` 表示，例如南四局的场风为 `S`；它表示场风，不指某位玩家。

## 牌

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `1m` 至 `9m` | 一万至九万 | manzu。 |
| `0m` | 红五万 | red five manzu。 |
| `1p` 至 `9p` | 一筒至九筒 | pinzu。 |
| `0p` | 红五筒 | red five pinzu。 |
| `1s` 至 `9s` | 一索至九索 | souzu。 |
| `0s` | 红五索 | red five souzu。 |
| `1z` | 东 | ton / east。 |
| `2z` | 南 | nan / south。 |
| `3z` | 西 | sha / west。 |
| `4z` | 北 | pei / north。 |
| `5z` | 白 | haku / white dragon。 |
| `6z` | 发 | hatsu / green dragon。 |
| `7z` | 中 | chun / red dragon。 |

牌列表在顺序无关时，按 `m`、`p`、`s`、`z` 分组排序；每组内按数字从小到大排序。红五 `0m`、`0p`、`0s` 与对应的五同序，并排在普通 `5m`、`5p`、`5s` 之前。

示例：

```json
["1m", "0m", "5m", "9m", "2p", "0p", "5p", "1s", "0s", "5s", "1z", "7z"]
```

## 动作术语

| 仓库内名称 | 中文 | 分类 | 备注 |
| --- | --- | --- | --- |
| `deal` | 摸牌 | 英语 | 普通从牌山摸牌。不使用 `draw`，以免与流局混淆。 |
| `replacement` | 岭上补牌 | 英语 | 杠后从岭上牌取得补牌。 |
| `discard` | 打牌 / 切牌 | 英语 | 从手牌切出一张牌。 |
| `riichi_declaration` | 立直宣言牌 | 罗马音 + 英语 | 与 `discard` 等价，但明确表示该弃牌是立直宣言牌。 |
| `chi` | 吃 | 罗马音 | 日语：chii。仓库内使用更常见的 `chi`。 |
| `pon` | 碰 | 罗马音 | 日语：pon。 |
| `kan` | 杠 | 罗马音 | 日语：kan。 |
| `added_kan` | 加杠 | 英语 + 罗马音 | 从已碰的刻子加成杠。 |
| `open_kan` | 大明杠 | 英语 + 罗马音 | 鸣别人打出的牌开杠。 |
| `closed_kan` | 暗杠 | 英语 + 罗马音 | 使用自己手牌开暗杠。 |
| `tsumo` | 自摸 | 罗马音 | 日语：tsumo。 |
| `ron` | 荣和 | 罗马音 | 日语：ron。 |
| `draw` | 流局 | 英语 | 未由和牌结束的局，具体原因见流局术语。 |

## 玩家局面术语

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `hand` | 手牌 | 当前手牌列表。 |
| `river` | 牌河 | 弃牌列表，下标从 `0` 开始。 |
| `tsumogiri_indices` | 摸切下标 | `river` 中摸切牌的下标列表。 |
| `called_indices` | 被鸣走下标 | `river` 中被鸣走牌的下标列表。 |
| `riichi` | 立直状态 | 是否已经立直成立。 |
| `riichi_declaration_index` | 立直宣言牌下标 | 立直宣言牌在 `river` 中的下标。 |
| `melds` | 副露 | 按发生顺序排列的副露列表。 |

## 局面计数术语

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `dora_indicators` | 宝牌指示牌 | 当前已翻开的宝牌指示牌列表。 |
| `ura_indicators` | 里宝牌指示牌 | 里宝牌通常称为 ura dora；字段记录已翻开的里宝牌指示牌列表。 |
| `remaining_tiles` | 剩余可摸牌数 | 不包括王牌。 |
| `honba` | 本场 | 连庄或流局累积的本场数。 |
| `kyotaku` | 场供 | 桌上已成立的立直棒数量；每根 1000 点。 |

## 宝牌术语

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `dora` | 宝牌 | 通用宝牌名称。 |
| `ura_dora` / `ura` | 里宝牌 | `ura_dora` 为完整概念名，`ura` 为简写；两种都可使用。 |
| `aka_dora` / `aka` | 赤宝牌 | `aka_dora` 为完整概念名，`aka` 为简写；两种都可使用。在牌 ID 中用 `0m`、`0p`、`0s` 表示红五。 |

## 流局术语

流局本身记为 `draw`，下表是流局类型的名称。

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `exhaustive` | 荒牌流局 | 牌山摸尽后流局。 |
| `four_winds` | 四风连打 | 四家第一巡打出同一种风牌导致流局。 |
| `four_riichi` | 四家立直 | 四家全部立直导致流局。 |
| `four_kans` | 四杠散了 | 多个玩家合计开出四个杠导致流局。 |
| `three_ron` | 三家和了流局 | 仅用于采用三家和了算流局的规则。 |
| `nine_terminals` | 九种九牌 | 起手幺九牌种类达到规则要求时宣告流局。 |

荒牌流局时听牌的玩家记为 `ready_players`，是风位字母列表。

## 役种术语

役种名称使用英语 snake_case。下表覆盖雀魂和天凤常规四人日麻规则中的役种名称；宝牌、里宝牌、红宝牌是番数加成，不作为役种名称记录。

### 一番役

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `riichi` | 立直 | 门前听牌宣言。 |
| `one_shot` | 一发 | 立直后一巡内和牌。 |
| `fully_concealed_self_draw` | 门前清自摸和 | 门前自摸。 |
| `all_simples` | 断幺九 | 可开门，取决于规则是否允许食断。 |
| `no_points_hand` | 平和 | 无符型和牌。 |
| `pure_double_sequence` | 一杯口 | 同色同顺两组，门前限定。 |
| `seat_wind` | 自风牌 | 自风刻子或杠子。 |
| `prevalent_wind` | 场风牌 | 场风刻子或杠子。 |
| `white_dragon` | 白 | 白板刻子或杠子。 |
| `green_dragon` | 发 | 发刻子或杠子。 |
| `red_dragon` | 中 | 中刻子或杠子。 |
| `after_a_kan` | 岭上开花 | 杠后补牌自摸。 |
| `robbing_a_kan` | 抢杠 | 抢加杠荣和；规则允许时也包括用国士无双抢暗杠。 |
| `last_tile_draw` | 海底摸月 | 牌山最后一张自摸。 |
| `last_discard` | 河底捞鱼 | 牌山摸尽前最后打牌荣和。 |

### 二番役

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `double_riichi` | 两立直 | 第一巡立直。 |
| `seven_pairs` | 七对子 | 七组对子。 |
| `all_triplets` | 对对和 | 四组刻子或杠子。 |
| `three_closed_triplets` | 三暗刻 | 三组暗刻或暗杠。 |
| `three_color_sequences` | 三色同顺 | 三门同数字顺子。 |
| `three_color_triplets` | 三色同刻 | 三门同数字刻子或杠子。 |
| `straight` | 一气通贯 | 同门 123、456、789。 |
| `terminal_or_honor_in_each_set` | 混全带幺九 | 每组面子和雀头都含幺九牌或字牌。 |
| `all_terminals_and_honors` | 混老头 | 只使用幺九牌和字牌。 |
| `three_kans` | 三杠子 | 三组杠子。 |
| `little_three_dragons` | 小三元 | 两组三元牌刻子或杠子，加一组三元牌雀头。 |

### 三番役及以上

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `twice_pure_double_sequence` | 二杯口 | 两组一杯口，门前限定。 |
| `terminal_in_each_set` | 纯全带幺九 | 每组面子和雀头都含幺九牌，且不含字牌。 |
| `half_flush` | 混一色 | 一种数牌加字牌。 |
| `full_flush` | 清一色 | 只使用一种数牌。 |

### 特殊满贯

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `all_terminal_and_honor_discards` | 流し满贯 | 只打出幺九牌和字牌且未被鸣牌。 |

### 役满

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `thirteen_orphans` | 国士无双 | 十三幺。 |
| `thirteen_orphans_thirteen_wait` | 国士无双十三面 | 可按规则计为双倍役满。 |
| `four_closed_triplets` | 四暗刻 | 四组暗刻或暗杠。 |
| `four_closed_triplets_single_wait` | 四暗刻单骑 | 可按规则计为双倍役满。 |
| `big_three_dragons` | 大三元 | 三组三元牌刻子或杠子。 |
| `little_four_winds` | 小四喜 | 三组风牌刻子或杠子，加一组风牌雀头。 |
| `big_four_winds` | 大四喜 | 四组风牌刻子或杠子，可按规则计为双倍役满。 |
| `all_honors` | 字一色 | 只使用字牌。 |
| `all_green` | 绿一色 | 只使用绿色牌。 |
| `all_terminals` | 清老头 | 只使用一九数牌。 |
| `nine_gates` | 九莲宝灯 | 门前清一色特定形。 |
| `true_nine_gates` | 纯正九莲宝灯 | 九面听九莲宝灯，可按规则计为双倍役满。 |
| `four_kans` | 四杠子 | 四组杠子。 |
| `heavenly_hand` | 天和 | 亲家配牌和牌。 |
| `hand_of_earth` | 地和 | 子家第一巡摸牌和牌。 |
| `hand_of_man` | 人和 | 规则相关；用于支持启用人和的规则集。 |
