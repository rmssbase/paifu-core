# Tenhou Standard (`tenhou_std`)

本页说明 Paifu 中 `rule = "tenhou_std"` 的含义，以及如何把天凤牌谱（mjlog）转换成 Paifu。Paifu 的结构和字段定义见 [paifu.md](../paifu.md)，本页只描述天凤特有的来源格式和映射规则，不改变 Paifu 的通用结构。

## 规则含义

`tenhou_std` 表示天凤四人段位场半庄规则（四南喰赤），依据 [tenhou.net/man](https://tenhou.net/man/) 的段位战规则说明。重放 `tenhou_std` 的 Paifu 时，牌山拆分、宝牌翻开、可执行操作、流局条件和结算方式都按该规则处理。

| 项目 | 约定 |
| --- | --- |
| 人数 | 四人。 |
| 牌数 | 136 张，`0m`、`0p`、`0s` 各一张红五。 |
| 起始点数 | 25000，点数守恒等式右侧为 `100000`。 |
| 王牌 | 14 张，其中岭上牌 4 张、宝牌指示牌 5 张、里宝牌指示牌 5 张。 |
| 普通牌山 | 配牌后剩余 69 张，即 Paifu `wall` 的长度。 |

影响重放和结算、并且与 [majsoul_std.md](majsoul_std.md) 不同的规则：

| 项目 | `tenhou_std` |
| --- | --- |
| 一炮多响 | 双响成立，本场和场供只给离放铳者最近的和牌者（上家取り）。三家同时荣和为途中流局 `three_ron`，连庄。 |
| 双倍役满 | 没有双倍役满，国士无双十三面、四暗刻单骑、纯正九莲宝灯、大四喜都是单倍役满；不同役满可以复合。 |
| 包牌 | 只针对大三元、大四喜。包牌者负担包括复合役满在内的全部得点，自摸由包牌者全付，荣和由包牌者与放铳者各付一半；本场由包牌者支付。 |
| 抢暗杠 | 国士无双不能抢暗杠。 |
| 杠宝牌 | 暗杠立即翻开；大明杠、加杠在打牌时或下一次摸岭上牌之前翻开，因此连续加杠时，抢杠判断发生在上一个杠的宝牌翻开之前。 |

两种规则相同的部分见 [majsoul_std.md](majsoul_std.md) 的“规则含义”。

## 天凤牌谱的组成

天凤牌谱不需要登录。由牌谱链接得到牌谱 ID 后，直接请求 mjlog 接口即可取得完整的 XML 牌谱。

### 牌谱链接

天凤牌谱链接用 `log` 参数标识牌谱，`tw` 参数是打开牌谱时的视角座位，可以省略：

```text
http://tenhou.net/0/?log=2021032221gm-00a9-0000-8f79bed9&tw=2
```

| 字段 | 示例 | 含义 |
| --- | --- | --- |
| `log_id` | `2021032221gm-00a9-0000-8f79bed9` | 链接中完整的 `log` 参数，用于请求牌谱。 |
| `time` | `2021032221` | 对局的日期和小时（`YYYYMMDDHH`）。 |
| `game_type` | `00a9` | 十六进制的对局类型，与 mjlog `GO.type` 相同，见下文。 |
| `lobby` | `0000` | 大厅编号，段位场为 `0000`。 |
| `hash` | `8f79bed9` | 牌谱的区分码。 |
| `viewer` | `2` | `tw` 参数，只影响网页显示视角，不影响牌谱内容。 |

取得牌谱：

```text
https://tenhou.net/0/log/?2021032221gm-00a9-0000-8f79bed9
```

返回 `<mjloggm ver="2.3">` 根元素的 XML。转换产物按 `time` 和 `hash` 命名，例如 `2021032221_8f79bed9.json`。

### mjlog 元素

mjlog 根元素下是按时间顺序排列的元素：

| 元素 | 含义 | 转换时用到的属性 |
| --- | --- | --- |
| `SHUFFLE` | 整场牌局的牌山随机种子。 | `seed` |
| `GO` | 对局类型。 | `type` |
| `UN` | 第一次出现时是玩家名（URL 编码）、段位、R 值、性别；之后出现表示断线玩家重连。 | 无 |
| `TAIKYOKU` | 对局开始，`oya` 为起家座位。 | 无 |
| `INIT` | 开始一个小局。 | `seed`, `ten`, `oya`, `hai0`–`hai3` |
| `T`/`U`/`V`/`W` + 牌号 | 座位 `0`/`1`/`2`/`3` 摸牌（普通摸牌或岭上牌），例如 `<T86/>`。 | 元素名（仅用于校验和摸切判断） |
| `D`/`E`/`F`/`G` + 牌号 | 座位 `0`/`1`/`2`/`3` 切牌，例如 `<D40/>`。 | 元素名 |
| `N` | 吃、碰、杠。 | `who`, `m` |
| `REACH` | 立直。`step="1"` 是宣告，紧跟着的切牌是宣言牌；`step="2"` 是立直成立，`ten` 是扣除立直棒后的各家点数。 | `who`, `step` |
| `DORA` | 翻开一张新的宝牌指示牌。 | `hai`（仅用于校验） |
| `AGARI` | 和牌。一炮多响时连续出现多个 `AGARI`。 | `who`, `fromWho` |
| `RYUUKYOKU` | 流局。 | `type` |
| `BYE` | 玩家断线。断线期间由系统代打（摸切、不鸣牌）。 | 无 |

`GO.type` 是按位组合的对局类型：`0x01` 对人战、`0x02` 无赤、`0x04` 无食断、`0x08` 半庄（否则东风）、`0x10` 三人麻将、`0x20` 特上、`0x40` 速、`0x80` 上级；`0x20` 与 `0x80` 同时出现表示凤凰卓。`tenhou_std` 只对应四人、有赤、有食断的半庄，例如 `0xa9`（`169`，凤凰卓四人南喰赤）；其它类型拒绝转换。

### 牌号

天凤用 `0` 至 `135` 的牌号区分每一张牌，每种牌 4 张：`kind = 牌号 // 4`。`kind` 的 `0`–`8` 为 `1m`–`9m`，`9`–`17` 为 `1p`–`9p`，`18`–`26` 为 `1s`–`9s`，`27`–`33` 依次为东南西北白发中，即 `1z`–`7z`。红五是每种五的第一张：牌号 `16`、`52`、`88` 分别为 `0m`、`0p`、`0s`。

因为每张牌的牌号唯一，切牌的牌号等于刚摸到的牌号时就是摸切。

## 座位与风位

天凤用固定的座位号 `0`–`3` 表示玩家，整场不变；Paifu 用当前小局的风位。`INIT.oya` 是本小局的亲家座位：

```text
wind(seat) = (seat - oya) % 4    # 0 -> E, 1 -> S, 2 -> W, 3 -> N
```

`ten`、`hai0`–`hai3`、元素名中的座位、`who`、`fromWho` 都按座位号排列或给出，转换时映射成风位。

## metainfo 映射

`INIT.seed` 是逗号分隔的六个整数：小局序号、本场、场供、两颗骰子（`0`–`5`）、开局宝牌指示牌的牌号。

| Paifu 字段 | 天凤字段 | 说明 |
| --- | --- | --- |
| `wind` | `seed[0] // 4` | `0`–`3` 分别为 `E`、`S`、`W`、`N`；`2` 及以上是西入后的延长战。 |
| `round` | `seed[0] % 4 + 1` | |
| `honba` | `seed[1]` | |
| `kyotaku` | `seed[2]` | |
| `scores` | `ten` | 以 100 点为单位、按座位排列，乘 100 后转换为以 `east` 等为键的对象。 |

`seed[0] % 4` 总等于 `oya`。`rule` 固定写为 `"tenhou_std"`。

## tiles 映射

### 由 SHUFFLE 复原牌山

`INIT` 只给出四家的 13 张起手牌，mjlog 中也只出现实际摸到的牌和翻开的宝牌。Paifu 需要完整的牌序，因此要用 `SHUFFLE.seed` 按天凤公开的牌山生成方法（[tenhou.net/stat/rand](https://tenhou.net/stat/rand/)，伪代码见其中链接的[牌山生成手順](http://blog.tenhou.net/article/30503297.html)）复原每个小局的牌山：

1. `seed` 形如 `mt19937ar-sha512-n288-base64,<Base64>`。Base64 解码得到 2496 字节，按小端序读成 624 个 32 位无符号整数，用它们作为 MT19937 的 `init_by_array` 种子。整场牌局只初始化一次。
2. 每个小局依次从 MT19937 取 288 个 32 位整数，按 32 个一组分成 9 组；每组按小端序拼成 128 字节，取 SHA-512 摘要（64 字节），再按小端序读成 16 个整数。9 组共得到 144 个整数 `rnd`。
3. `yama = [0, 1, ..., 135]`，对 `i = 0..135` 交换 `yama[i]` 与 `yama[i + rnd[i] % (136 - i)]`。
4. 骰子为 `rnd[135] % 6` 和 `rnd[136] % 6`，应与 `INIT.seed[3:5]` 一致。

第 `n` 个 `INIT` 对应第 `n` 次生成的 `yama`。天凤从 `yama` 的末尾开始配牌，骰子不影响取牌位置：

| `yama` 下标 | 用途 |
| --- | --- |
| `135` 往下 | 配牌：亲家起依次每人取 4 张，共三轮，然后每人取 1 张（亲家 `yama[87]`，南家 `yama[86]`，西家 `yama[85]`，北家 `yama[84]`）。 |
| `83` | 亲家的第 14 张起手牌，即 mjlog 中亲家的第一次摸牌。 |
| `82` 往下到 `14` | 普通摸牌序列：`wall[i] = yama[82 - i]`，共 69 张。 |
| `0:14` | 王牌。 |

王牌映射：

```text
rinshan         = [yama[1], yama[0], yama[3], yama[2]]
dora_indicators = [yama[5], yama[7], yama[9], yama[11], yama[13]]
ura_indicators  = [yama[4], yama[6], yama[8], yama[10], yama[12]]
```

`wall`、`rinshan`、`dora_indicators`、`ura_indicators` 保持上述顺序，不排序，总是写满 69、4、5、5 张。开杠后岭上摸牌会让海底提前，Paifu 的重放用 `69 - 普通摸牌数 - 岭上摸牌数` 表示剩余牌数，与天凤一致。

### initial_hands

`hai0`–`hai3` 是四个座位的 13 张起手牌。亲家的 `initial_hands` 再加上 `yama[83]`，共 14 张。写入时转换牌号、映射到风位，再按牌列表排序规则排序。

mjlog 中每个小局的第一条动作是亲家摸 `yama[83]`（例如 `<T86/>`）。这张牌已经在亲家的 `initial_hands` 中，不对应 Paifu 的摸牌。

## decisions 映射

转换时需要同步重放：按 Paifu 规则维护当前局面，才能判断某个时刻是否生成 `call_decision`。mjlog 元素与 Paifu decision 的对应关系：

| mjlog 元素 | Paifu decision |
| --- | --- |
| 切牌，之前没有同一玩家的 `REACH step="1"` | `discard` |
| 切牌，紧跟在同一玩家的 `REACH step="1"` 之后 | `riichi_declaration` |
| `N`（吃、碰、大明杠） | `chi`、`pon`、`open_kan` |
| `N`（暗杠、加杠） | `closed_kan`、`added_kan` |
| `AGARI` | `tsumo` 或 `ron` |
| `RYUUKYOKU` | `draw` |
| 重放生成了 `call_decision`，但下一条动作不是鸣牌或和牌 | `pass` |
| 摸牌、`REACH step="2"`、`DORA`、`BYE`、`UN` | 不写入 |

### discard / riichi_declaration

`<D40/>` 是座位 `0` 切出牌号 `40`（`1p`）。`tile` 取牌号对应的牌 ID；`from` 为：

| 情况 | `from` |
| --- | --- |
| 切出的牌号等于该玩家刚摸到的牌号（普通摸牌或岭上牌） | `deal` |
| 其它情况 | `hand` |
| 亲家第一次切牌，或吃、碰后的切牌 | `hand` |

亲家第一次切牌即使切出的是 `yama[83]`，按 Paifu 的约定也写 `hand`。

立直：

```xml
<REACH who="1" step="1"/><E28/><REACH who="1" ten="280,230,240,240" step="2"/>
```

转换为（座位 `1` 是南家，`28` 是 `8p`，不是刚摸到的牌）：

```json
{"type": "riichi_declaration", "tile": "8p", "from": "hand"}
```

`REACH step="2"` 不写入，立直成立由重放判断。宣言牌被荣和时没有 `step="2"`。

### N 的解码

`N.who` 是执行者座位，`N.m` 是 16 位编码的副露。`m & 3` 是放铳者相对执行者的位置（`1` 下家、`2` 对家、`3` 上家；暗杠为 `0`），放铳者座位为 `(who + (m & 3)) % 4`。

| 条件 | 类型 | 解码 |
| --- | --- | --- |
| `m & 0x04` | 吃 | `t = m >> 10`；`r = t % 3` 是被鸣牌在三张中的位置；`t //= 3`；`base = t // 7 * 9 + t % 7` 是顺子最小牌的 `kind`。第 `i` 张（`i = 0, 1, 2`）的牌号为 `(base + i) * 4 + ((m >> (3 + 2 * i)) & 3)`。 |
| `m & 0x08` | 碰 | `t = m >> 9`；`r = t % 3`；`kind = t // 3`；没有用到的那一张为 `kind * 4 + ((m >> 5) & 3)`，其余三张按牌号升序，第 `r` 张是被鸣牌。 |
| `m & 0x10` | 加杠 | 与碰相同的编码；“没有用到的那一张”就是加上去的牌。 |
| `m & 0x20` | 拔北 | 只用于三人麻将，不支持。 |
| 其它 | 暗杠（`m & 3 == 0`）或大明杠 | `m >> 8` 是一张牌号（大明杠时为被鸣牌），四张为 `kind * 4` 至 `kind * 4 + 3`。 |

转换为 Paifu decision：

- 吃、碰、大明杠：`player` 为 `who` 的风位，`tile` 为被鸣牌，`hands` 为其余的牌（排序）。被鸣牌和放铳者应与重放中上一张弃牌一致。
- 暗杠：`hands` 为四张牌（排序）。
- 加杠：`hands` 为加上去的那一张牌。

```xml
<N who="0" m="41513" />
```

`41513 & 0x08` 不为零，是碰：`t = 41513 >> 9 = 81`，`r = 0`，`kind = 27`（东）；`(41513 >> 5) & 3 = 1`，没有用到牌号 `109`；三张为 `108`、`110`、`111`，被鸣牌是 `108`；`41513 & 3 = 1`，放铳者是座位 `1`。座位 `0` 是亲家时转换为：

```json
{"type": "pon", "player": "E", "hands": ["1z", "1z"], "tile": "1z"}
```

### tsumo / ron

`AGARI.who == AGARI.fromWho` 时是自摸，写为 `{"type": "tsumo"}`；否则是荣和。一炮多响时连续出现多个 `AGARI`（`fromWho` 相同），合并为一条 `ron`，`players` 按出现顺序列出各个 `who` 的风位：

```json
{"type": "ron", "players": ["S", "W"]}
```

加杠后被抢杠时，`AGARI` 紧跟在加杠的 `N` 之后，写法相同。

天和的 `AGARI.machi` 是亲家第 14 张（`yama[83]`），`yakuman` 按这张牌区分国士无双/十三面（`47`/`48`）、四暗刻/单骑（`40`/`41`）、九莲宝灯/纯正（`45`/`46`）。Paifu 不记录哪一张是第 14 张，重放按 [paifu.md](../paifu.md#tsumo) 的高点法选和牌牌，所以这几项可能与天凤记录不同；`tenhou_std` 没有双倍役满，打点和点数变化不受影响。

### draw

`RYUUKYOKU` 写为 `{"type": "draw"}`。`RYUUKYOKU.type` 与 Paifu 流局类型的对应：

| `type` | 流局类型 | 说明 |
| --- | --- | --- |
| 无 | `exhaustive` | 荒牌流局。听牌玩家的手牌在 `hai0`–`hai3` 中亮出，没有该属性的玩家未听牌。 |
| `nm` | `exhaustive` | 荒牌流局且有人流局满贯，以流局满贯代替听牌罚符结算。 |
| `yao9` | `nine_terminals` | 九种九牌，玩家在摸牌后的决策点主动宣告。 |
| `kaze4` | `four_winds` | 四风连打。 |
| `reach4` | `four_riichi` | 四家立直，第四家的 `REACH step="2"` 之后出现。 |
| `kan4` | `four_kans` | 四杠散了。 |
| `ron3` | `three_ron` | 三家和了，紧跟在被三家荣和的切牌之后，在 `call_decision` 中写 `draw`。 |

九种九牌和三家和了之外的流局都是重放自动触发的：最后一条切牌之后若重放生成了 `call_decision`，先补一条 `pass`，再写 `draw`。

### pass

天凤牌谱不记录其他玩家可选的操作。`pass` 完全由重放判断：重放在某张弃牌或加杠之后生成了 `call_decision`，而下一条动作不是 `N`（吃、碰、大明杠）或 `AGARI`，就写一条 `pass`。

## 用于校验的字段

转换时可以用下列字段交叉校验重放结果：

| 天凤字段 | 校验内容 |
| --- | --- |
| `INIT.hai0`–`hai3`、`INIT.seed[3:6]` | 与复原的 `yama` 的配牌、骰子、开局宝牌指示牌一致。 |
| 摸牌元素的牌号 | 等于重放摸到的普通牌或岭上牌。 |
| `DORA.hai` | 每次摸牌时，已出现的宝牌指示牌与重放已翻开的一致。 |
| `REACH step="2"` 的 `ten` | 立直成立及扣除立直棒后的点数。 |
| `AGARI.ba` | 和牌时的本场和场供（场供含本局成立的立直棒）。 |
| `AGARI.doraHai`、`doraHaiUra` | 和牌时已翻开的宝牌指示牌和里宝牌指示牌。 |
| `AGARI.sc`、`RYUUKYOKU.sc` | 以 100 点为单位、按座位排列的“原点数, 变化”对；变化包含本场和场供。一炮多响时每个 `AGARI` 只给出该和牌者的变化，合计应等于重放的结算。 |
| `RYUUKYOKU.type`、`hai0`–`hai3` | 流局类型和听牌玩家。 |
| `owari` | 整场最后一个 `AGARI` 或 `RYUUKYOKU` 上的终局点数（以 100 点为单位）和顺位分，与剩余场供归一位后的点数一致。 |
| `AGARI.yaku`、`yakuman`、`ten`、`paoWho`、`hai`、`m`、`machi` | 役种与番数、役满、符数与打点、包牌者、和牌时的手牌与副露。转换时不检查，可用于更深入的核对。 |

mjlog 中 `DORA` 的位置：暗杠后紧跟在 `N` 之后、岭上摸牌之前；大明杠、加杠后在岭上摸牌之后、紧挨着下一次切牌之前（与切牌同时翻开），岭上自摸时不出现；大明杠、加杠后接着再开杠时，在新的 `N` 之后、岭上摸牌之前。

## Python 工具

`paifu.tenhou` 实现了本页的转换规则，转换时同步重放并用上述字段校验（`AGARI` 的役种、打点等除外），任何不一致都会抛出 `PaifuError`：

```python
import paifu.tenhou
from paifu import write_json

xml = paifu.tenhou.fetch_log("http://tenhou.net/0/?log=2021032221gm-00a9-0000-8f79bed9&tw=2")
paifu_obj = paifu.tenhou.convert(xml)  # 也可以传入 mjlog 文件路径
write_json(paifu.tenhou.paifu_file_name("2021032221gm-00a9-0000-8f79bed9"), paifu_obj)
```

命令行可以转换单个链接、单个 mjlog、mjlog 目录，或逐行列出链接的文本文件（会依次下载）：

```text
python -m paifu.tenhou LINKS.txt PAIFU_DIR --save-xml XML_DIR
python -m paifu.tenhou XML_DIR PAIFU_DIR
python -m paifu.tenhou "http://tenhou.net/0/?log=..." out.json
```

`paifu.tenhou.parse_log_link` 解析牌谱链接，`walls` 由 `SHUFFLE.seed` 生成各小局的 `yama`，`decode_meld` 解码 `N.m`。
