import copy
import json
import os
from collections import Counter
from pathlib import Path


class PaifuError(ValueError):
    pass


WINDS = ("E", "S", "W", "N")
WIND_KEYS = ("east", "south", "west", "north")
WIND_TO_KEY = dict(zip(WINDS, WIND_KEYS))
KEY_TO_WIND = dict(zip(WIND_KEYS, WINDS))

SUITS = "mpsz"
TILE_IDS = tuple(f"{n}{s}" for s in "mps" for n in range(10)) + tuple(f"{n}z" for n in range(1, 8))
TILE_SET = frozenset(TILE_IDS)

HONOR_START = 27
DRAGON_KINDS = frozenset((31, 32, 33))
WIND_KINDS = frozenset((27, 28, 29, 30))
YAOCHU_KINDS = frozenset((0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33))
GREEN_KINDS = frozenset((19, 20, 21, 23, 25, 32))


def fail(message):
    raise PaifuError(message)


def check(condition, message):
    if not condition:
        raise PaifuError(message)


def tile_kind(tile):
    number = int(tile[0])
    suit = SUITS.index(tile[1])
    if suit == 3:
        return HONOR_START + number - 1
    return suit * 9 + (5 if number == 0 else number) - 1


def kind_to_tile(kind):
    if kind >= HONOR_START:
        return f"{kind - HONOR_START + 1}z"
    return f"{kind % 9 + 1}{SUITS[kind // 9]}"


def is_red(tile):
    return tile[0] == "0"


def tile_sort_key(tile):
    number = int(tile[0])
    return (SUITS.index(tile[1]), 5 if number == 0 else number, 0 if number == 0 else 1)


def sort_tiles(tiles):
    return sorted(tiles, key=tile_sort_key)


def is_sorted_tiles(tiles):
    keys = [tile_sort_key(t) for t in tiles]
    return keys == sorted(keys)


def kinds_counts(tiles):
    counts = [0] * 34
    for tile in tiles:
        counts[tile_kind(tile)] += 1
    return counts


def dora_kind(indicator_kind):
    if indicator_kind < HONOR_START:
        base = indicator_kind // 9 * 9
        return base + (indicator_kind - base + 1) % 9
    if indicator_kind in WIND_KINDS:
        return 27 + (indicator_kind - 27 + 1) % 4
    return 31 + (indicator_kind - 31 + 1) % 3


def wind_kind(wind):
    return HONOR_START + WINDS.index(wind)


def full_tile_counter():
    counter = Counter()
    for suit in "mps":
        for number in range(1, 10):
            counter[f"{number}{suit}"] = 3 if number == 5 else 4
        counter[f"0{suit}"] = 1
    for number in range(1, 8):
        counter[f"{number}z"] = 4
    return counter


def remove_tiles(hand, tiles):
    rest = list(hand)
    for tile in tiles:
        if tile not in rest:
            return None
        rest.remove(tile)
    return rest


def load_json_input(data):
    if isinstance(data, os.PathLike):
        return _parse_json_text(Path(data).read_text(encoding="utf-8"))
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError as error:
            if os.path.isfile(data):
                return _parse_json_text(Path(data).read_text(encoding="utf-8"))
            fail(f"cannot parse JSON: {error}")
    if isinstance(data, (dict, list)):
        return copy.deepcopy(data)
    fail(f"unsupported input type: {type(data).__name__}")


def _parse_json_text(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        fail(f"cannot parse JSON: {error}")


def expect_dict(value, path):
    check(isinstance(value, dict), f"{path} must be an object")
    return value


def expect_list(value, path):
    check(isinstance(value, list), f"{path} must be a list")
    return value


def expect_keys(obj, path, required, optional=()):
    expect_dict(obj, path)
    missing = [key for key in required if key not in obj]
    check(not missing, f"{path} is missing fields: {', '.join(missing)}")
    allowed = set(required) | set(optional)
    unknown = [key for key in obj if key not in allowed]
    check(not unknown, f"{path} has unknown fields: {', '.join(unknown)}")


def expect_int(value, path, minimum=None, maximum=None):
    check(isinstance(value, int) and not isinstance(value, bool), f"{path} must be an integer")
    if minimum is not None:
        check(value >= minimum, f"{path} must be at least {minimum}")
    if maximum is not None:
        check(value <= maximum, f"{path} must be at most {maximum}")
    return value


def expect_bool(value, path):
    check(isinstance(value, bool), f"{path} must be a boolean")
    return value


def expect_tile(value, path):
    check(isinstance(value, str) and value in TILE_SET, f"{path} is not a valid tile ID: {value!r}")
    return value


def expect_tiles(value, path, sorted_required=False):
    expect_list(value, path)
    for i, tile in enumerate(value):
        expect_tile(tile, f"{path}[{i}]")
    if sorted_required:
        check(is_sorted_tiles(value), f"{path} must be in canonical tile order")
    return value


def expect_wind(value, path):
    check(isinstance(value, str) and value in WINDS, f"{path} must be one of E, S, W, N: {value!r}")
    return value


def expect_winds(value, path, allow_empty=True):
    expect_list(value, path)
    for i, wind in enumerate(value):
        expect_wind(wind, f"{path}[{i}]")
    check(len(set(value)) == len(value), f"{path} must not repeat a player")
    if not allow_empty:
        check(value, f"{path} must not be empty")
    return value


def expect_indices(value, path, length):
    expect_list(value, path)
    for i, index in enumerate(value):
        expect_int(index, f"{path}[{i}]", 0, length - 1)
    check(all(a < b for a, b in zip(value, value[1:])), f"{path} must be strictly increasing")
    return value


def expect_scores(value, path):
    expect_keys(value, path, WIND_KEYS)
    for key in WIND_KEYS:
        expect_int(value[key], f"{path}.{key}")
    return {key: value[key] for key in WIND_KEYS}
