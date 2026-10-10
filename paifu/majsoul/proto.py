import base64

from ..common import PaifuError, fail
from .liqi_schema import SCHEMA

VARINT_TYPES = frozenset({"int32", "int64", "uint32", "uint64", "bool", "enum"})
SIGNED_TYPES = frozenset({"int32", "int64"})


def decode_message(type_name, buffer):
    """Decode protobuf bytes as `type_name` from SCHEMA; unknown fields are skipped, absent fields stay absent."""
    fields = SCHEMA[type_name]
    result = {}
    pos = 0
    end = len(buffer)
    while pos < end:
        key, pos = _varint(buffer, pos)
        number, wire = key >> 3, key & 7
        if wire == 0:
            raw, pos = _varint(buffer, pos)
            values = [raw]
        elif wire == 2:
            size, pos = _varint(buffer, pos)
            raw = buffer[pos:pos + size]
            if len(raw) != size:
                fail("truncated protobuf message")
            pos += size
            values = [raw]
        elif wire == 1:
            pos += 8
            continue
        elif wire == 5:
            pos += 4
            continue
        else:
            fail(f"unsupported protobuf wire type {wire} in {type_name}")
        spec = fields.get(number)
        if spec is None:
            continue
        name, field_type, repeated = spec
        if field_type in VARINT_TYPES:
            if wire == 2:
                values = _packed_varints(values[0])
            values = [_convert_varint(v, field_type) for v in values]
        elif field_type == "string":
            values = [values[0].decode("utf-8")]
        elif field_type == "bytes":
            values = [bytes(values[0])]
        else:
            values = [decode_message(field_type, values[0])]
        if repeated:
            result.setdefault(name, []).extend(values)
        else:
            result[name] = values[-1]
    return result


def decode_wrapper(buffer):
    """Decode a `.lq.Wrapper`, decoding its payload when the wrapped type is in SCHEMA."""
    wrapper = decode_message("Wrapper", buffer)
    name = wrapper.get("name", "")
    data = wrapper.get("data", b"")
    short = name[len(".lq."):] if name.startswith(".lq.") else name
    if short in SCHEMA:
        return {"name": name, "data": decode_message(short, data)}
    return {"name": name, "data": None}


def decode_game_record(raw):
    """Decode a dumped record ({"head": ..., "data": base64 GameDetailRecords wrapper}) into {uuid, head, actions}."""
    try:
        payload = raw["data"]
        if isinstance(payload, str):
            payload = base64.b64decode(payload)
        wrapper = decode_wrapper(payload)
    except (KeyError, ValueError, TypeError) as error:
        raise PaifuError(f"cannot decode Mahjong Soul record data: {error}") from error
    if wrapper["name"] != ".lq.GameDetailRecords":
        fail(f"expected .lq.GameDetailRecords, got {wrapper['name']!r}")
    details = wrapper["data"]
    actions = [decode_wrapper(record) for record in details.get("records", [])]
    for action in details.get("actions", []):
        if action.get("type") == 1 and "result" in action:
            actions.append(decode_wrapper(action["result"]))
    head = raw.get("head", {})
    return {"uuid": head.get("uuid"), "head": head, "actions": actions}


def _varint(buffer, pos):
    result = 0
    shift = 0
    while True:
        if pos >= len(buffer):
            fail("truncated protobuf varint")
        byte = buffer[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def _packed_varints(buffer):
    values = []
    pos = 0
    while pos < len(buffer):
        value, pos = _varint(buffer, pos)
        values.append(value)
    return values


def _convert_varint(value, field_type):
    if field_type == "bool":
        return bool(value)
    if field_type in SIGNED_TYPES and value >= 1 << 63:
        return value - (1 << 64)
    return value
