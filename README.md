# paifu-core

library for standardized Riichi Mahjong log formats, compression rules, and a Python replayer that produces snapshot objects for research workflows.

## Layout

| Path | Content |
| --- | --- |
| `paifu/` | Platform-independent core: Paifu / Snapshot formats, the replayer, shared rules (`rules.py`), hand analysis and scoring. |
| `paifu/majsoul/` | Mahjong Soul: the `majsoul_std` rule set and conversion from Mahjong Soul records to Paifu. |
| `paifu/tenhou/` | Tenhou: the `tenhou_std` rule set, mjlog download, wall reproduction and conversion from Tenhou logs to Paifu. |
| `docs/` | Format and rule documentation, see [docs/README.md](docs/README.md). |

Rules shared by all platforms live in `paifu/rules.py`; platform subpackages only set what differs.

## Usage

```python
from paifu import Paifu
import paifu.majsoul

game = paifu.majsoul.convert("majsoul_record.json")  # -> Paifu
while (snapshot := game.Replay()) is not None:
    ...
```

```python
import paifu.tenhou

xml = paifu.tenhou.fetch_log("http://tenhou.net/0/?log=2021032221gm-00a9-0000-8f79bed9")  # no login needed
game = paifu.tenhou.convert(xml)  # -> Paifu
```

Batch conversion of Mahjong Soul records (output files keep the input names):

```text
python -m paifu.majsoul RAW_DIR PAIFU_DIR
```

Batch conversion of Tenhou logs from a file of links, or from a directory of downloaded mjlog XML files
(output files are named like `2021032221_8f79bed9.json`):

```text
python -m paifu.tenhou LINKS.txt PAIFU_DIR --save-xml XML_DIR
python -m paifu.tenhou XML_DIR PAIFU_DIR
```

Requires Python 3.10+, no third-party dependencies.
