"""Tenhou mjlog (XML) access: log links, download, tile numbers and meld codes."""
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..common import fail

LOG_URL = "https://tenhou.net/0/log/?{}"
LOG_ID = re.compile(r"(?P<time>\d{10})gm-(?P<type>[0-9a-f]{4})-(?P<lobby>\d{4})-(?P<hash>[0-9a-f]{8})")
RED_FIVES = {16: "0m", 52: "0p", 88: "0s"}

# GO.type bits.
GO_HUMAN = 0x01
GO_NO_AKA = 0x02
GO_NO_KUITAN = 0x04
GO_HANCHAN = 0x08
GO_SANMA = 0x10
GO_TOKUJOU = 0x20
GO_FAST = 0x40
GO_JOUKYUU = 0x80


def parse_log_link(link):
    """Split a Tenhou log link (or bare log ID) into the parts described in tenhou_std.md."""
    query = parse_qs(urlparse(link.strip()).query)
    log_id = query["log"][0] if "log" in query else link.strip()
    match = LOG_ID.fullmatch(log_id)
    if match is None:
        fail(f"not a Tenhou log link or ID: {link!r}")
    viewer = query.get("tw", [None])[0]
    return {
        "log_id": log_id,
        "time": match["time"],
        "game_type": int(match["type"], 16),
        "lobby": match["lobby"],
        "hash": match["hash"],
        "viewer": int(viewer) if viewer is not None else None,
    }


def paifu_file_name(link):
    """File name used for the Paifu of a log, e.g. 2021032221_8f79bed9.json."""
    parts = parse_log_link(link)
    return f"{parts['time']}_{parts['hash']}.json"


def fetch_log(link, timeout=30):
    """Download the mjlog XML of a log link or ID. Tenhou needs no login."""
    log_id = parse_log_link(link)["log_id"]
    request = urllib.request.Request(LOG_URL.format(log_id), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    if not data.lstrip().startswith(b"<mjloggm"):
        fail(f"{log_id}: the server did not return a mjlog: {data[:80]!r}")
    return data


def load_mjlog(source):
    """Parse a mjlog given as XML text/bytes, a path, or an already parsed Element."""
    if isinstance(source, ET.Element):
        return source
    if isinstance(source, os.PathLike) or (isinstance(source, str) and not source.lstrip().startswith("<")):
        source = Path(source).read_bytes()
    try:
        root = ET.fromstring(source)
    except ET.ParseError as error:
        fail(f"cannot parse mjlog XML: {error}")
    if root.tag != "mjloggm":
        fail(f"not a mjlog: root element is {root.tag}")
    return root


def tile_name(number):
    """Tenhou tile number (0-135, four per kind) -> Paifu tile ID."""
    if number in RED_FIVES:
        return RED_FIVES[number]
    kind = number // 4
    if kind >= 27:
        return f"{kind - 26}z"
    return f"{kind % 9 + 1}{'mps'[kind // 9]}"


def tile_list(text):
    return [int(x) for x in text.split(",")] if text else []


def decode_meld(code):
    """Decode N.m into (type, tiles, called, offset).

    tiles are all Tenhou tile numbers of the meld after the call, called is the tile taken from another
    player (or added to a pon), offset is the relative position of the discarder (1 right, 2 across, 3 left; 0 for a closed kan).
    """
    offset = code & 3
    if code & 0x04:
        t = code >> 10
        position, t = t % 3, t // 3
        base = t // 7 * 9 + t % 7
        tiles = [(base + i) * 4 + ((code >> (3 + 2 * i)) & 3) for i in range(3)]
        return "chi", tiles, tiles[position], offset
    if code & 0x18:
        t = code >> 9
        position, kind = t % 3, t // 3
        unused = kind * 4 + ((code >> 5) & 3)
        tiles = [kind * 4 + i for i in range(4) if kind * 4 + i != unused]
        if code & 0x08:
            return "pon", tiles, tiles[position], offset
        return "added_kan", sorted(tiles + [unused]), unused, offset
    if code & 0x20:
        fail("nukidora is a three-player meld and is not supported")
    called = code >> 8
    kind = called // 4
    tiles = [kind * 4 + i for i in range(4)]
    return ("closed_kan" if offset == 0 else "open_kan"), tiles, called, offset
