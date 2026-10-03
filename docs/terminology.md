# Terminology

本文档约定日麻通用术语在 paifu-core 标准格式中的名称。

## 命名原则

| 类别 | 仓库内约定 | 示例 | 备注 |
| --- | --- | --- | --- |
| 吃、碰、杠、自摸、荣和、立直 | 使用罗马音 | `chi`, `pon`, `kan`, `tsumo`, `ron`, `riichi` | 保留日麻语境中最常见的写法。 |
| 其它通用动作与状态 | 使用英语 | `draw`, `discard`, `replacement`, `draw_game` | 不混入中文拼音。 |
| 役种 | 通常使用英语 snake_case，立直系使用 `riichi` | `all_simples`, `riichi`, `double_riichi`, `robbing_a_kan` | `riichi` 是本仓库的固定例外。 |
| 玩家风位 | 使用风位字母 | `E`, `S`, `W`, `N` | 表示东、南、西、北家。 |
| 牌 | 使用紧凑牌 ID | `1m`, `0p`, `7z` | `0m`/`0p`/`0s` 表示红五。 |

## 玩家风位

| 仓库内名称 | 中文 | 英文 | 备注 |
| --- | --- | --- | --- |
| `E` | 东家 | east | 自风或座位为东。 |
| `S` | 南家 | south | 自风或座位为南。 |
| `W` | 西家 | west | 自风或座位为西。 |
| `N` | 北家 | north | 自风或座位为北。 |

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

## 动作术语

| 仓库内名称 | 中文 | 分类 | 备注 |
| --- | --- | --- | --- |
| `draw` | 摸牌 | 英语 | 普通从牌山摸牌。 |
| `replacement` | 岭上补牌 | 英语 | 杠后从岭上牌取得补牌。 |
| `discard` | 打牌 / 切牌 | 英语 | 从手牌切出一张牌。 |
| `chi` | 吃 | 罗马音 | 日语：chii。仓库内使用更常见的 `chi`。 |
| `pon` | 碰 | 罗马音 | 日语：pon。 |
| `kan` | 杠 | 罗马音 | 日语：kan。 |
| `added_kan` | 加杠 | 英语 + 罗马音 | 从已碰的刻子加成杠。 |
| `tsumo` | 自摸 | 罗马音 | 日语：tsumo。 |
| `ron` | 荣和 | 罗马音 | 日语：ron。 |
| `draw_game` | 流局 | 英语 | 未由和牌结束的局。 |

## 流局术语

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `exhaustive` | 荒牌流局 | 牌山摸尽后流局。 |
| `four_winds` | 四风连打 | 四家第一巡打出同一种风牌导致流局。 |
| `four_riichi` | 四家立直 | 四家全部立直导致流局。 |
| `four_kans` | 四杠散了 | 多个玩家合计开出四个杠导致流局。 |
| `three_ron` | 三家和了流局 | 仅用于采用三家和了算流局的规则。 |
| `nine_terminals` | 九种九牌 | 起手幺九牌种类达到规则要求时宣告流局。 |

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
| `robbing_a_kan` | 抢杠 | 抢加杠荣和。 |
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
