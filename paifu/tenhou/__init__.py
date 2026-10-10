"""Tenhou (天鳳) support: the tenhou_std rule set and conversion of Tenhou mjlogs to Paifu."""

from .converter import convert, convert_file
from .mjlog import decode_meld, fetch_log, paifu_file_name, parse_log_link, tile_name
from .rules import TENHOU_STD
from .wall import walls

__all__ = [
    "TENHOU_STD",
    "convert",
    "convert_file",
    "decode_meld",
    "fetch_log",
    "paifu_file_name",
    "parse_log_link",
    "tile_name",
    "walls",
]
