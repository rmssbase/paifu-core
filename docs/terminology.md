# Terminology

本文档只约定日麻通用术语在 paifu-core 标准格式中的名称。Snapshot 字段、字段结构和字段取值约束见 [snapshot.md](snapshot.md)。

## 命名原则

| 类别 | 仓库内约定 | 示例 | 备注 |
| --- | --- | --- | --- |
| 吃、碰、杠、自摸、荣和 | 使用罗马音 | `chi`, `pon`, `kan`, `tsumo`, `ron` | 保留日麻语境中最常见的写法。 |
| 其它通用动作与状态 | 使用英语 | `draw`, `discard`, `replacement`, `draw_game` | 不混入中文拼音。 |
| 役种 | 使用英语 snake_case | `double_riichi`, `ippatsu`, `chankan` | 备注中可补充常见日语/罗马音。 |
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
| `replacement` | 岭上补牌 | 英语 | 杠后从岭上牌取得补牌；罗马音：rinshan。 |
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
| `four_winds` | 四风连打 | 罗马音：suufon renda。 |
| `four_riichi` | 四家立直 | 罗马音：suucha riichi。 |
| `four_kans` | 四杠散了 | 罗马音：suukan sanra。 |
| `three_ron` | 三家和了流局 | 仅用于采用三家和了算流局的规则。 |
| `nine_terminals` | 九种九牌 | 罗马音：kyuushu kyuuhai。 |

## 役种术语

役种名称使用英语 snake_case。下表先记录当前约定中已经出现的役种；完整役种表可在后续扩展。

| 仓库内名称 | 中文 | 备注 |
| --- | --- | --- |
| `double_riichi` | 两立直 | 罗马音：daburu riichi。 |
| `ippatsu` | 一发 | 罗马音：ippatsu。 |
| `rinshan` | 岭上开花 | 罗马音：rinshan kaihou。 |
| `chankan` | 抢杠 | 罗马音：chankan。 |
| `riichi` | 立直 | 罗马音：riichi。 |
| `tanyao` | 断幺九 | 罗马音：tanyao。 |
| `pinfu` | 平和 | 罗马音：pinfu。 |
| `yakuhai` | 役牌 | 英语也常称 value tiles。 |
| `haitei` | 海底摸月 | 罗马音：haitei raoyue。 |
| `houtei` | 河底捞鱼 | 罗马音：houtei raoyui。 |
