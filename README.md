# paifu-core

library for standardized Riichi Mahjong log formats, compression rules, and a Python replayer that produces snapshot objects for research workflows.

## Layout

| Path | Content |
| --- | --- |
| `paifu/` | Platform-independent core: Paifu / Snapshot formats, the replayer, shared rules (`rules.py`), hand analysis and scoring. |
| `paifu/majsoul/` | Mahjong Soul: the `majsoul_std` rule set and conversion from Mahjong Soul records to Paifu. |
| `paifu/tenhou/` | Tenhou: the `tenhou_std` rule set. |
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

Batch conversion of Mahjong Soul records (output files keep the input names):

```text
python -m paifu.majsoul RAW_DIR PAIFU_DIR
```

Requires Python 3.10+, no third-party dependencies.
