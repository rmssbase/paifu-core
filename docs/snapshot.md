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
  }
}
```

`type = "init"` 时不带 `latest_action`。其它类型必须带 `latest_action`。

## Snapshot 类型

| `type` | 是否有 `latest_action` | 含义 |
| --- | --- | --- |
| `init` | 否 | 牌局刚刚开始，还没有任何人开始打牌；各家手牌都是 13 张，亲家尚未摸牌。 |
| `discard_decision` | 是 | 轮到某个玩家作出自身行动决策，包括切牌、暗杠、自摸等。 |
| `call_decision` | 是 | 轮到一个或多个其它玩家判断是否鸣牌、荣和或抢杠。 |
| `final` | 是 | 牌局已经结束，要么有人和牌，要么流局。 |

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
| `kan` | `player` | 玩家完成杠相关动作后进入自身决策；若直接表达补牌后的状态，优先使用 `replacement`。 |

普通摸牌示例：

```json
{
  "type": "discard_decision",
  "latest_action": {
    "type": "draw",
    "player": "E",
    "card": "5m"
  }
}
```

岭上补牌示例：

```json
{
  "type": "discard_decision",
  "latest_action": {
    "type": "replacement",
    "player": "S",
    "card": "7s"
  }
}
```

吃牌后示例：

```json
{
  "type": "discard_decision",
  "latest_action": {
    "type": "chi",
    "player": "S"
  }
}
```

碰牌后示例：

```json
{
  "type": "discard_decision",
  "latest_action": {
    "type": "pon",
    "player": "W"
  }
}
```

### call_decision

`call_decision` 表示某个玩家刚打出牌，或刚加杠，并且至少存在其他玩家可以鸣牌、荣和或抢杠。如果无人可鸣、无人可荣，不生成该 snapshot。

允许的 `latest_action.type`：

| 值 | 必填字段 | 含义 |
| --- | --- | --- |
| `discard` | `player`, `card` | 玩家刚打出一张牌，其他玩家需要判断是否 `chi`、`pon`、`kan` 或 `ron`。 |
| `added_kan` | `player`, `card` | 玩家刚加杠，其他玩家需要判断是否抢杠 `ron`。 |

打牌后示例：

```json
{
  "type": "call_decision",
  "latest_action": {
    "type": "discard",
    "player": "E",
    "card": "3p"
  }
}
```

加杠后示例：

```json
{
  "type": "call_decision",
  "latest_action": {
    "type": "added_kan",
    "player": "S",
    "card": "4m"
  }
}
```

### final

`final` 表示牌局已经结束。允许自摸、荣和和流局。

允许的 `latest_action.type`：

| 值 | 必填字段 | 含义 |
| --- | --- | --- |
| `tsumo` | `player`, `card`, `yaku` | 自摸结束。 |
| `ron` | `player`, `card`, `yaku` | 荣和结束；`player` 可为单个玩家或玩家列表。 |
| `draw_game` | `draw_game_type` | 流局结束；不带 `player`。 |

自摸示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "tsumo",
    "player": "W",
    "card": "2s",
    "yaku": []
  }
}
```

带偶然役的自摸示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "tsumo",
    "player": "E",
    "card": "7p",
    "yaku": ["ippatsu"]
  }
}
```

单人荣和示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "ron",
    "player": "N",
    "card": "9m",
    "yaku": []
  }
}
```

多人荣和示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "ron",
    "player": ["S", "W"],
    "card": "5p",
    "yaku": [
      ["ippatsu"],
      []
    ]
  }
}
```

荒牌流局示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "draw_game",
    "draw_game_type": "exhaustive",
    "tenpai_players": ["E", "N"]
  }
}
```

途中流局示例：

```json
{
  "type": "final",
  "latest_action": {
    "type": "draw_game",
    "draw_game_type": "four_winds"
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
added_kan
tsumo
ron
```

`chi` 和 `pon` 不带 `card`，因为它们接收的是前一个 `call_decision` 中的弃牌。`draw_game` 不带 `card`。

### `yaku`

`yaku` 只用于 `tsumo` 和 `ron`。

单人自摸或单人荣和时，`yaku` 是字符串列表：

```json
["ippatsu", "double_riichi"]
```

多人荣和时，`yaku` 是列表的列表，并与 `player` 列表按顺序一一对应：

```json
{
  "player": ["S", "W"],
  "yaku": [
    ["ippatsu"],
    ["double_riichi"]
  ]
}
```

`yaku` 只记录不能仅靠 snapshot 中的手牌、牌河和局面信息稳定推断出的偶然役或过程役。建议 v1 支持：

```text
double_riichi
ippatsu
rinshan
chankan
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

## 完整示例

下面示例只展示本规范已经约定的决策类型和前置动作字段。后续可在此基础上补充手牌、牌河、副露、分数、宝牌等局面字段。

```json
[
  {
    "type": "init"
  },
  {
    "type": "discard_decision",
    "latest_action": {
      "type": "draw",
      "player": "E",
      "card": "5m"
    }
  },
  {
    "type": "call_decision",
    "latest_action": {
      "type": "discard",
      "player": "E",
      "card": "3p"
    }
  },
  {
    "type": "discard_decision",
    "latest_action": {
      "type": "pon",
      "player": "W"
    }
  },
  {
    "type": "call_decision",
    "latest_action": {
      "type": "added_kan",
      "player": "W",
      "card": "3p"
    }
  },
  {
    "type": "final",
    "latest_action": {
      "type": "ron",
      "player": "S",
      "card": "3p",
      "yaku": ["chankan"]
    }
  }
]
```
