# Docs

paifu-core 的文档分为通用术语、Snapshot 局面格式、Paifu 压缩牌谱格式，以及与具体游戏规则相关的 game protocol。

| 文档 | 内容 | 适用场景 |
| --- | --- | --- |
| [terminology.md](terminology.md) | 日麻术语的仓库内名称：牌 ID、风位、动作名、役种名、流局类型和牌列表排序规则。 | 统一命名。 |
| [snapshot.md](snapshot.md) | Snapshot 格式，表示小局的开始、结束或一个明确的决策点。 | 描述某一时刻的完整局面。 |
| [paifu.md](paifu.md) | Paifu 格式，只保存起局场况、牌序和每个决策点的选择，由重放还原出 Snapshot 序列。 | 大规模保存、重放和统计牌谱。 |
| [game_protocol/majsoul_std.md](game_protocol/majsoul_std.md) | 雀魂四人段位场规则 `majsoul_std` 的含义，以及雀魂牌谱到 Paifu 的转换规则。 | 将雀魂牌谱转换成 Paifu。 |
| [game_protocol/tenhou_std.md](game_protocol/tenhou_std.md) | 天凤四人段位场规则 `tenhou_std` 的含义、与 `majsoul_std` 的差异，以及天凤牌谱（mjlog）到 Paifu 的转换规则。 | 将天凤牌谱转换成 Paifu。 |

关系概览：

```text
雀魂牌谱链接                 天凤牌谱链接
  -> 解码后的雀魂记录          -> mjlog XML（含牌山种子）
  -> Paifu (rule = majsoul_std / tenhou_std)
  -> 重放得到各个决策点
  -> Snapshot
```
