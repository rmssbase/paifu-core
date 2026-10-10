"""Convert Tenhou mjlogs to formatted Paifu JSON.

    python -m paifu.tenhou SRC DST

SRC is a mjlog XML file, a directory of *.xml mjlogs, a text file of log links (one per line, downloaded from
tenhou.net), or a single log link / ID. DST is the output directory; a single XML file or link may also be
written to a DST ending in .json. Output files are named like 2021032221_8f79bed9.json.
"""
import argparse
import sys
import time
from pathlib import Path

from ..common import PaifuError
from ..jsonfmt import write_json
from .converter import convert
from .mjlog import LOG_ID, fetch_log, paifu_file_name, parse_log_link


def _jobs(src):
    """Yield (output name, local XML path or None, log ID to download or None)."""
    path = Path(src)
    if path.is_dir():
        for xml in sorted(path.glob("*.xml")):
            yield _output_name(xml.stem), xml, None
    elif path.suffix == ".xml":
        yield _output_name(path.stem), path, None
    elif path.is_file():
        seen = set()
        for line in path.read_text(encoding="utf-8").split():
            log_id = parse_log_link(line)["log_id"]
            if log_id not in seen:
                seen.add(log_id)
                yield paifu_file_name(log_id), None, log_id
    else:
        log_id = parse_log_link(src)["log_id"]
        yield paifu_file_name(log_id), None, log_id


def _output_name(stem):
    return paifu_file_name(stem) if LOG_ID.fullmatch(stem) else f"{stem}.json"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m paifu.tenhou", description=__doc__.strip().splitlines()[0])
    parser.add_argument("src")
    parser.add_argument("dst", type=Path)
    parser.add_argument("--no-verify", action="store_true", help="skip cross-checking the replay against the mjlog")
    parser.add_argument("--save-xml", type=Path, metavar="DIR", help="also keep downloaded mjlogs in DIR as LOG_ID.xml")
    parser.add_argument("--skip-existing", action="store_true", help="do not convert logs whose output already exists")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds to wait between downloads (default 0.5)")
    args = parser.parse_args(argv)

    jobs = list(_jobs(args.src))
    single_file = len(jobs) == 1 and args.dst.suffix == ".json"
    if not single_file:
        args.dst.mkdir(parents=True, exist_ok=True)
    if args.save_xml:
        args.save_xml.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name, xml_path, log_id in jobs:
        dst = args.dst if single_file else args.dst / name
        if args.skip_existing and dst.exists():
            continue
        try:
            if log_id is None:
                xml = xml_path.read_bytes()
            else:
                xml = fetch_log(log_id)
                if args.save_xml:
                    (args.save_xml / f"{log_id}.xml").write_bytes(xml)
                time.sleep(args.delay)
            write_json(dst, convert(xml, verify=not args.no_verify))
        except (PaifuError, OSError) as error:
            failures += 1
            print(f"FAILED {name}: {error}", file=sys.stderr)
    print(f"converted {len(jobs) - failures}/{len(jobs)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
