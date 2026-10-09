import json
from pathlib import Path

INDENT = 4
INLINE_KEYS = frozenset({"scores", "latest_action"})
ITEM_PER_LINE_KEYS = frozenset({"decisions", "melds"})


def format_json(obj, indent=INDENT, inline_keys=INLINE_KEYS, item_per_line_keys=ITEM_PER_LINE_KEYS):
    """Format JSON with `indent`; scalar lists stay on one line, and lists under `item_per_line_keys` put one item per line."""
    return _format(_unwrap(obj), None, 0, indent, inline_keys, item_per_line_keys)


def format_paifu(obj, indent=INDENT):
    return format_json(obj, indent)


def format_snapshot(obj, indent=INDENT):
    return format_json(obj, indent)


def write_json(path, obj, indent=INDENT):
    Path(path).write_text(format_json(obj, indent) + "\n", encoding="utf-8")


def _unwrap(obj):
    if hasattr(obj, "Dump"):
        return obj.Dump()
    return obj


def _inline(value):
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _is_scalar(value):
    return not isinstance(value, (dict, list))


def _is_flat_list(value):
    if all(_is_scalar(v) for v in value):
        return True
    return all(isinstance(v, list) and all(_is_scalar(x) for x in v) for v in value)


def _format(value, key, level, indent, inline_keys, item_keys):
    if _is_scalar(value) or key in inline_keys:
        return _inline(value)
    pad = " " * (indent * (level + 1))
    end = " " * (indent * level)
    if isinstance(value, list):
        if not value or _is_flat_list(value):
            return _inline(value)
        if key in item_keys:
            items = [_inline(v) for v in value]
        else:
            items = [_format(v, None, level + 1, indent, inline_keys, item_keys) for v in value]
        return "[\n" + ",\n".join(pad + item for item in items) + "\n" + end + "]"
    if not value:
        return "{}"
    items = [f"{pad}{_inline(k)}: {_format(v, k, level + 1, indent, inline_keys, item_keys)}" for k, v in value.items()]
    return "{\n" + ",\n".join(items) + "\n" + end + "}"
