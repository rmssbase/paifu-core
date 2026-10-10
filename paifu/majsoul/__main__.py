"""Convert dumped Mahjong Soul records to formatted Paifu JSON.

    python -m paifu.majsoul SRC DST

SRC is a record file or a directory of *.json records; DST is the output file or directory (same file names).
"""
import argparse
import sys
from pathlib import Path

from ..common import PaifuError
from .converter import convert_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m paifu.majsoul", description=__doc__.strip().splitlines()[0])
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path)
    parser.add_argument("--no-verify", action="store_true", help="skip cross-checking the replay against the record")
    args = parser.parse_args(argv)

    if args.src.is_dir():
        args.dst.mkdir(parents=True, exist_ok=True)
        jobs = [(path, args.dst / path.name) for path in sorted(args.src.glob("*.json"))]
    else:
        jobs = [(args.src, args.dst)]
    failures = 0
    for src, dst in jobs:
        try:
            convert_file(src, dst, verify=not args.no_verify)
        except PaifuError as error:
            failures += 1
            print(f"FAILED {src.name}: {error}", file=sys.stderr)
    print(f"converted {len(jobs) - failures}/{len(jobs)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
