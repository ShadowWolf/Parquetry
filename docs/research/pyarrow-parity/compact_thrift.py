"""A minimal reader for Thrift's compact protocol.

The pyarrow API does not show every field of a Parquet footer, for example
which statistics fields are present. This module decodes the raw structures so
the probe can print them. Structs come back as dicts keyed by Thrift field id.
The field ids are those in parquet.thrift in the apache/parquet-format
repository.
"""
import struct


def _varint(buf, pos):
    result = 0
    shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return result, pos


def _zigzag(n):
    return (n >> 1) ^ -(n & 1)


def _value(buf, pos, kind, in_list=False):
    if kind in (1, 2):  # boolean
        if in_list:
            return buf[pos] == 1, pos + 1
        return kind == 1, pos
    if kind == 3:  # byte
        return buf[pos], pos + 1
    if kind in (4, 5, 6):  # i16, i32, i64
        n, pos = _varint(buf, pos)
        return _zigzag(n), pos
    if kind == 7:  # double
        return struct.unpack("<d", buf[pos:pos + 8])[0], pos + 8
    if kind == 8:  # binary or string
        n, pos = _varint(buf, pos)
        return bytes(buf[pos:pos + n]), pos + n
    if kind in (9, 10):  # list or set
        header = buf[pos]
        pos += 1
        count = header >> 4
        element_kind = header & 15
        if count == 15:
            count, pos = _varint(buf, pos)
        items = []
        for _ in range(count):
            item, pos = _value(buf, pos, element_kind, True)
            items.append(item)
        return items, pos
    if kind == 12:  # struct
        return read_struct(buf, pos)
    raise ValueError(f"unsupported Thrift type {kind}")


def read_struct(buf, pos):
    """Reads one struct starting at pos. Returns (dict by field id, end position)."""
    fields = {}
    field_id = 0
    while True:
        header = buf[pos]
        pos += 1
        if header == 0:
            return fields, pos
        delta = header >> 4
        kind = header & 15
        if delta:
            field_id += delta
        else:
            n, pos = _varint(buf, pos)
            field_id = _zigzag(n)
        fields[field_id], pos = _value(buf, pos, kind)


def read_footer(path):
    """Returns (file bytes, FileMetaData as a dict by field id)."""
    buf = open(path, "rb").read()
    length = struct.unpack("<I", buf[-8:-4])[0]
    footer, _ = read_struct(buf, len(buf) - 8 - length)
    return buf, footer
