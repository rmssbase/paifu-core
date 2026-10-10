"""Mahjong Soul (雀魂) support: the majsoul_std rule set and conversion of Mahjong Soul records to Paifu."""

from .converter import convert, convert_file, parse_paipu_link
from .proto import decode_game_record
from .rules import MAJSOUL_STD

__all__ = ["MAJSOUL_STD", "convert", "convert_file", "decode_game_record", "parse_paipu_link"]
