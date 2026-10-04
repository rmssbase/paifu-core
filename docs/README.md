# Docs

paifu-core 的格式文档分为通用术语、局面格式、压缩牌谱格式和来源映射。下面是各文档的定位。

| 文档 | 内容 | 适用场景 |
| --- | --- | --- |
| [terminology.md](terminology.md) | 通用日麻术语、牌 ID、动作名、役种名和顺序无关牌列表的排序规则。 | 阅读其它格式前先统一命名。 |
| [snapshot.md](snapshot.md) | 标准局面 snapshot 格式，表示牌局边界或一个明确决策入口。 | 表达 replay 到某个决策点后的局面。 |
| [simplified_paifu.md](simplified_paifu.md) | 压缩牌谱 simplified paifu 格式，只保存起局事实、牌序和决策结果。 | 大规模保存、重放和统计牌谱。 |
| [majsoul_simplified_paifu.md](majsoul_simplified_paifu.md) | 雀魂牌谱链接、解码记录和 `majsoul_std` simplified paifu 的字段映射。 | 将雀魂来源转换成 simplified paifu。 |

关系概览：

```text
Mahjong Soul paipu link
  -> decoded Mahjong Soul game record
  -> majsoul_std simplified paifu
  -> replay decision points
  -> snapshot
```