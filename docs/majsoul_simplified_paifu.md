# Mahjong Soul Simplified Paifu Mapping

本页说明雀魂牌谱链接、解码后的雀魂记录与 `majsoul_std` simplified paifu 之间的对应关系。

雀魂链接解析和记录映射是来源适配规则，不改变 simplified paifu 的通用结构。

## 牌谱链接

雀魂牌谱链接通过 `paipu` query parameter 标识牌谱。

```text
https://game.maj-soul.com/1/?paipu=261001-7c1f7669-7c88-428f-be52-594120ef58d7_a94003061
```

解析结果：

| 字段 | 示例 | 含义 |
| --- | --- | --- |
| `paipu_id` | `261001-7c1f7669-7c88-428f-be52-594120ef58d7_a94003061` | 链接中的完整 `paipu` 参数。 |
| `record_uuid` | `261001-7c1f7669-7c88-428f-be52-594120ef58d7` | 下划线前的牌谱记录 UUID，用于请求完整记录。 |
| `account_suffix` | `a94003061` | 下划线后的账号视角后缀；只用于来源标识，不参与局面重放。 |
| `date_prefix` | `261001` | `record_uuid` 中第一个连字符前的前缀。 |

仅解析链接不能得到完整牌谱。生成 simplified paifu 需要先通过雀魂记录接口取得并解码完整 game record。

## 解码记录

解码后的雀魂记录包含 `uuid`、`head` 和 `actions`。`actions` 是按时间顺序排列的记录对象列表，常见名称包括：

| 雀魂记录 | 用途 |
| --- | --- |
| `.lq.RecordNewRound` | 开始一个小局，提供起始分数、手牌、牌山和起局元信息。 |
| `.lq.RecordDealTile` | 普通摸牌或岭上补牌。 |
| `.lq.RecordDiscardTile` | 切牌，并可能携带可鸣牌、荣和或立直等操作入口。 |
| `.lq.RecordChiPengGang` | 吃、碰或明杠。 |
| `.lq.RecordAnGangAddGang` | 暗杠或加杠。 |
| `.lq.RecordHule` | 和牌结束。 |
| `.lq.RecordNoTile` | 荒牌流局。 |
| `.lq.RecordLiuJu` | 中途流局。 |

每个 `.lq.RecordNewRound` 对应一个 simplified paifu 小局对象。整场牌谱转换结果是这些小局对象按出现顺序组成的列表。

## 风位映射

雀魂使用原始座位号 `0`、`1`、`2`、`3`。Simplified paifu 使用当前小局风位 `E`、`S`、`W`、`N`。

`RecordNewRound.ju` 是当前场风内的 0-based 小局编号。庄家座位为：

```text
dealer_seat = ju % 4
```

风位映射为：

```text
dealer_seat -> E
(dealer_seat + 1) % 4 -> S
(dealer_seat + 2) % 4 -> W
(dealer_seat + 3) % 4 -> N
```

所有 `scores`、`initial_hands`、决策执行者和和牌者都应转换成风位表示。

## metainfo 映射

`RecordNewRound` 到 `metainfo` 的字段映射：

| simplified paifu 字段 | 雀魂字段 | 说明 |
| --- | --- | --- |
| `wind` | `chang` | 0-based 场风编号，`0` 至 `3` 分别映射为 `E`、`S`、`W`、`N`。缺省时按 `0` 处理。 |
| `round` | `ju` | 0-based 小局编号，写入时加 1。缺省时按 `0` 处理。 |
| `honba` | `ben` | 本场数。缺省时为 `0`。 |
| `kyotaku` | `liqibang` | 场供立直棒数量。缺省时为 `0`。 |
| `scores` | `scores` | 按风位映射重排。 |

`rule` 固定写为 `majsoul_std`。

## tiles 映射

`RecordNewRound.tiles0`、`tiles1`、`tiles2`、`tiles3` 是四个原始座位的起手牌。写入 `initial_hands` 时应先转换到风位，并按通用牌排序规则排序。

雀魂亲家起手字段通常已经包含 14 张牌。若从 `paishan` 生成起手牌，则第 `52` 张是亲家第 14 张起手牌，不应写入 `wall`。

从 `RecordNewRound.paishan` 生成 `majsoul_std` simplified paifu 时，采用以下拆分：

| 范围 | simplified paifu 字段 | 含义 |
| --- | --- | --- |
| `0:52` | `initial_hands` | 四家 13 张起手牌。 |
| `52` | `initial_hands.E` | 亲家第 14 张起手牌。 |
| `53:122` | `wall` | 剩余普通摸牌序列。 |
| `122:136` | 王牌区域 | 用于生成 `rinshan`、`dora_indicators`、`ura_indicators`。 |

王牌区域按 14 张列表 `dead_wall` 表示时，映射为：

```text
rinshan = [dead_wall[13], dead_wall[12], dead_wall[11], dead_wall[10]]
dora_indicators = [dead_wall[9], dead_wall[7], dead_wall[5], dead_wall[3], dead_wall[1]]
ura_indicators = [dead_wall[8], dead_wall[6], dead_wall[4], dead_wall[2], dead_wall[0]]
```

`wall`、`rinshan`、`dora_indicators` 和 `ura_indicators` 保持来源顺序，不排序。

## decisions 映射

`decisions` 只记录决策结果，不记录可由 replay 推导出的中间状态。

### discard

`.lq.RecordDiscardTile` 转为 `discard`。

```json
{
    "type": "discard",
    "tile": "1s",
    "from": "hand"
}
```

`tile` 来自雀魂 `tile` 字段。`from` 按当前 replay 状态判断：

| 条件 | `from` |
| --- | --- |
| 切出刚取得的摸牌或岭上牌 | `draw` |
| 切出原有手牌 | `hand` |
| 亲家第一巡从 14 张起手牌切牌 | `hand` |

### chi / pon / open_kan

`.lq.RecordChiPengGang` 转为 `chi`、`pon` 或 `open_kan`。

若 `tiles` 和 `froms` 长度相同：

```text
hands = [tile for tile, from_seat in zip(tiles, froms) if from_seat == seat]
tile = first tile where from_seat != seat
from = wind mapped from seat
```

示例：

```json
{
    "type": "chi",
    "from": "E",
    "hands": ["1p", "2p"],
    "tile": "3p"
}
```

`type` 可按组合形状确定：顺子为 `chi`，刻子为 `pon`，四张明杠为 `open_kan`。

### closed_kan / added_kan

`.lq.RecordAnGangAddGang` 转为 `closed_kan` 或 `added_kan`。

```json
{
    "type": "closed_kan",
    "hands": ["9p", "9p", "9p", "9p"]
}
```

雀魂 `type = 2` 表示暗杠，写为 `closed_kan`。其它加杠记录写为 `added_kan`，并用 `hands` 记录从手牌加入的牌。

### pass

如果 `.lq.RecordDiscardTile` 携带 `operations`，但下一条有效记录不是鸣牌、杠或和牌，则该 `call_decision` 的结果写为 `pass`。

```json
{
    "type": "pass"
}
```

如果弃牌后没有 `operations`，说明 replay 不会生成 `call_decision`，不写 `pass`。

### ron / tsumo

`.lq.RecordHule` 转为 `tsumo` 或 `ron`。

若所有 `hules` 都带 `zimo = true`，写为：

```json
{
    "type": "tsumo"
}
```

否则写为：

```json
{
    "type": "ron",
    "winners": ["S", "W"]
}
```

`winners` 由 `hules[].seat` 转换为风位，支持双响和三响。

### draw_game

`.lq.RecordNoTile` 和 `.lq.RecordLiuJu` 转为 `draw_game`。

```json
{
    "type": "draw_game"
}
```

流局类型和听牌结算由 replay 根据当前局面和规则推导。