"""Minimal reader for .NET BinaryFormatter streams (version 2, no SOAP header).

Hex of Steel saves (``maps/*.sav``) are Unity ``BinaryFormatter`` payloads.
This module parses the record-level object graph so we can recover map
metadata (SizeX/SizeY), the TilesTable dictionary, and tile Name strings.

Scope: enough of MS-SER.BF to *read* HoS saves:
  - StreamHeader / SerializedStreamHeader
  - ClassAttributes (LibraryType) + ClassInfo/ClassInfoHeader records
  - BinaryObject (+ BinaryObjectWithMap / BinaryObjectWithMapTyped)
  - BinaryArray (single/multi-dim, primitive + object element types)
  - BinaryFormattedString primitives (length-prefixed UTF-16LE)
  - ObjectReferences (the ``O`` member sentinel)
Member names in typed class infos are length-prefixed ASCII strings; values
follow with type tags per Table 3 of MS-SER.BF.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class RecordTypeEnum(IntEnum):
    SINGLE = 0x00
    ARRAY = 0x01
    GENERIC_LIST = 0x02
    STREAM_HEADER = 0x04
    OBJECT_MAP = 0x08
    OBJECT_MAP_APT_TYPE = 0x09
    SERIALIZABLE_TYPES = 0x0C
    CLASS_INFO = 0x10
    CLASS_INFO_HEADER = 0x11
    BINARY_OBJECT = 0x12
    BINARY_ARRAY = 0x14
    BINARY_STRING = 0x15
    MESSAGE_START = 0x16
    EXTERNAL_OBJECT = 0x17
    EXTERNAL_INFO = 0x18
    GENERIC_INFORMATION = 0x20
    OBJECT_INFO = 0x21
    STRING_INFO = 0x22
    NAME_INFO = 0x23
    OBJECT_REFERENCE = 0x40
    DEPENDENT_OBJECTS = 0x41


class ElementType(IntEnum):
    END = 0x00
    VOID = 0x01
    BOOLEAN = 0x02
    CHAR = 0x03
    I1 = 0x04
    U1 = 0x05
    I2 = 0x06
    U2 = 0x07
    I4 = 0x08
    U4 = 0x09
    I8 = 0x0A
    U8 = 0x0B
    SINGLE = 0x0C
    DOUBLE = 0x0D
    STRING = 0x0E
    POINTER = 0x0F
    PRIMITIVE = 0x10          # deprecated alias
    OBJECT = 0x11
    CLASS = 0x12
    VALUE_TYPE = 0x13         # deprecated alias
    ARRAY = 0x14
    GENERIC_COLLECTION = 0x15
    TYPED_PARAMETER = 0x16    # deprecated alias
    INDIRECT = 0x17           # deprecated alias
    SERIALIZABLE = 0x18       # deprecated alias
    NULL = 0x19


PRIMITIVE_SIZES = {
    ElementType.BOOLEAN: 1,
    ElementType.CHAR: 2,
    ElementType.I1: 1,
    ElementType.U1: 1,
    ElementType.I2: 2,
    ElementType.U2: 2,
    ElementType.I4: 4,
    ElementType.U4: 4,
    ElementType.I8: 8,
    ElementType.U8: 8,
    ElementType.SINGLE: 4,
    ElementType.DOUBLE: 8,
}

_PRIM_UNPACK = {
    ElementType.BOOLEAN: "<?",   # bool as 1 byte handled separately
    ElementType.CHAR: "<H",
    ElementType.I1: "<b",
    ElementType.U1: "<B",
    ElementType.I2: "<h",
    ElementType.U2: "<H",
    ElementType.I4: "<i",
    ElementType.U4: "<I",
    ElementType.I8: "<q",
    ElementType.U8: "<Q",
    ElementType.SINGLE: "<f",
    ElementType.DOUBLE: "<d",
}


@dataclass
class Member:
    """One field value inside a serialized object."""
    name: str | None
    elem_type: int
    value: Any


@dataclass
class BinaryObject:
    object_id: int
    type_id: int
    members: list[Member] = field(default_factory=list)

    def get(self, name: str) -> Any:
        for m in self.members:
            if m.name == name:
                return m.value
        raise KeyError(name)

    def has(self, name: str) -> bool:
        return any(m.name == name for m in self.members)


@dataclass
class TypeInfo:
    """A LibraryType or SerializableTypes entry: id -> full type name."""
    type_id: int
    name: str
    assembly_id: int


class BFReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.objects: dict[int, BinaryObject] = {}
        self.typeinfos: dict[int, TypeInfo] = {}      # LibraryType ids
        self.sertypes: dict[int, str] = {}            # SerializableTypes ids
        self.classinfos: dict[int, tuple[list[int], list[str]]] = {}  # clsid -> (elem_types, names)
        self.classinfo_headers: dict[int, tuple[int, list[int]]] = {} # clsid -> (clsdefid, parent chain)
        self.string_values: dict[int, str] = {}       # string_map_id -> str
        self.message_len = 1

    # --- low level -----------------------------------------------------
    def _take(self, n: int) -> bytes:
        b = self.data[self.pos:self.pos + n]
        if len(b) != n:
            raise EOFError(f"need {n} bytes at {self.pos}")
        self.pos += n
        return b

    def u8(self) -> int:
        return self._take(1)[0]

    def i32(self) -> int:
        return struct.unpack("<i", self._take(4))[0]

    def i64(self) -> int:
        return struct.unpack("<q", self._take(8))[0]

    def utf16_string(self) -> str:
        """Length-prefixed UTF-16LE (BinaryFormattedString)."""
        n = self.i32()
        raw = self._take(n * 2)
        return raw.decode("utf-16-le")

    def ascii_name(self) -> str:
        """Length-prefixed ASCII (member names / URIs in class info headers)."""
        n = self.u8()
        return self._take(n).decode("ascii", "replace")

    # --- main loop ------------------------------------------------------
    def parse(self) -> None:
        self._header()
        while True:
            try:
                etype = self.u8()
            except EOFError:
                break
            if etype == ElementType.END:
                continue
            rt = RecordTypeEnum(etype)
            if rt is RecordTypeEnum.SERIALIZABLE_TYPES:
                pass  # handled below via full name; keep branch harmless
            if rt is RecordTypeEnum.SINGLE:
                self._single()
            elif rt is RecordTypeEnum.OBJECT_MAP:
                self._object_map(typed=False)
            elif rt is RecordTypeEnum.OBJECT_MAP_APT_TYPE:
                self._object_map(typed=True)
            elif rt is RecordTypeEnum.SERIALIZABLE_TYPES:
                self._serializable_types()
            elif rt is RecordTypeEnum.CLASS_INFO:
                self._class_info()
            elif rt is RecordTypeEnum.CLASS_INFO_HEADER:
                self._class_info_header()
            elif rt is RecordTypeEnum.BINARY_OBJECT:
                self._binary_object()
            elif rt is RecordTypeEnum.BINARY_ARRAY:
                self._binary_array()
            elif rt is RecordTypeEnum.BINARY_STRING:
                self._binary_string()
            elif rt is RecordTypeEnum.MESSAGE_START:
                self._message_start()
            elif rt is RecordTypeEnum.OBJECT_INFO:
                pass  # remoting metadata, ignore
            else:
                raise ValueError(f"unhandled record 0x{etype:02x} at offset {self.pos - 1}")

    # --- records --------------------------------------------------------
    def _header(self):
        """Consume the stream preamble (observed in HoS saves at offset 0):

        ``00`` padding byte, int32 RecordInfo (=1), int32 Version (=-1 here),
        int32 Purpose (=1), int32 TargetHeaderLength (=0, header omitted),
        then a 0x00 end-of-header marker. First real record follows.
        """
        self.pos = 1                      # skip leading 0x00
        self.i32()                        # RecordInfo
        self.i32()                        # Version
        self.i32()                        # Purpose
        tlen = self.i32()                 # TargetHeader length (chars)
        if tlen > 0:
            self._take(tlen * 2)          # UTF-16 target header if present
        if self.data[self.pos] == 0x00:   # END of header section
            self.pos += 1

    def _single(self):
        item = self.i32()
        tname = self.utf16_string()
        aid = self.i32()
        self.typeinfos[item] = TypeInfo(item, tname, aid)

    def _message_start(self):
        self.i32()               # MessageId
        self.message_len = self.i32()

    def _object_map(self, typed: bool):
        oid = self.i32()
        clsid = self.i32()
        nvals = self.i32()
        obj = BinaryObject(object_id=oid, type_id=clsid)
        self.objects[oid] = obj
        if typed:
            self.ascii_name()    # object description (ignored)
            n_inst = self.i32()
            inst_elem_types = [self.u8() for _ in range(n_inst)]
            inst_member_names = [self.ascii_name() for _ in range(n_inst)]
            self.classinfos.setdefault(clsid, (inst_elem_types, inst_member_names))
        for _ in range(nvals):
            elem_type = self.u8()
            val = self._value(elem_type)
            obj.members.append(Member(None, elem_type, val))
        # fill names from classinfo once available
        self._late_name(obj)

    def _late_name(self, obj: BinaryObject):
        ci = self._resolve_classinfo(obj.type_id)
        if ci and not any(m.name is None for m in obj.members):
            return
        if ci:
            elem_types, names = ci
            # only assign when counts match (untyped maps store values w/o names)
            if len(names) >= len(obj.members):
                for m, nm in zip(obj.members, names[-len(obj.members):]):
                    if m.name is None:
                        m.name = nm

    def _resolve_classinfo(self, clsid: int):
        seen = set()
        cur = clsid
        merged_t: list[int] = []
        merged_n: list[str] = []
        while cur and cur not in seen:
            seen.add(cur)
            hdr = self.classinfo_headers.get(cur)
            ci = self.classinfos.get(cur)
            if ci:
                merged_t = ci[0] + merged_t
                merged_n = ci[1] + merged_n
            cur = hdr[1][0] if hdr and hdr[1] else 0
        return (merged_t, merged_n) if merged_n else None

    def _serializable_types(self):
        """SerializableTypes: Count, then per type int32 TypeId + name.

        HoS writes this record *before* MessageStart, so no MessageLen
        field is present (observed at offset 0x11 of every sample save).
        """
        count = self.i32()
        assert 0 < count < 100000, f"implausible SerializableTypes count {count}"
        for _ in range(count):
            tid = self.i32()
            self.sertypes[tid] = self.utf16_string()

    def _class_info(self):
        clsid = self.i32()
        msglen = self.i32()
        assert msglen == self.message_len
        nprops = self.i32()
        elem_types = [self.u8() for _ in range(nprops)]
        names = [self.ascii_name() for _ in range(nprops)]
        self.classinfos[clsid] = (elem_types, names)
        # retro-fill names on already-parsed untyped objects of this class
        for obj in self.objects.values():
            if obj.type_id == clsid:
                self._late_name(obj)

    def _class_info_header(self):
        clsid = self.i32()
        clsdefid = self.i32()
        nparents = self.i32()
        parents = [self.i32() for _ in range(nparents)]
        self.utf16_string()  # TypeName
        self.utf16_string()  # LibraryName (MemberTypeForTopLevel)
        self.classinfo_headers[clsid] = (clsdefid, parents)

    def _binary_object(self):
        oid = self.i32()
        clsid = self.i32()
        nvals = self.i32()
        obj = BinaryObject(object_id=oid, type_id=clsid)
        self.objects[oid] = obj
        ci = self._resolve_classinfo(clsid)
        for i in range(nvals):
            elem_type = self.u8()
            name = None
            if ci and i < len(ci[1]):
                name = ci[1][i]
            elif ci:
                name = ci[1][i - len(ci[1])] if False else None
            val = self._value(elem_type)
            obj.members.append(Member(name, elem_type, val))
        if ci is None:
            self._pending_ci.append(obj)
        else:
            self._late_name(obj)

    def _binary_string(self):
        smid = self.i32()
        s = self.utf16_string()
        self.string_values[smid] = s

    def _binary_array(self):
        oid = self.i32()
        rank = self.i32()
        self.i32(); self.i32()          # typeElement, elementTypeId
        bounds = [self.i32() for _ in range(rank)]
        self.i32(); self.i32()          # lowerBound x2
        total = 1
        for b in bounds:
            total *= max(b, 0)
        elem_type = self.u8()
        vals = [self._value(elem_type) for _ in range(total)]
        arr = BinaryObject(object_id=oid, type_id=-1)
        arr.members = [Member(f"[{i}]", elem_type, v) for i, v in enumerate(vals)]
        arr.bounds = bounds  # type: ignore[attr-defined]
        self.objects[oid] = arr

    # --- values ----------------------------------------------------------
    def _value(self, elem_type: int):
        et = elem_type & 0x7F  # high bit may mark additional info
        if et in PRIMITIVE_SIZES:
            if ElementType(et) is ElementType.BOOLEAN:
                return bool(self.u8())
            fmt = _PRIM_UNPACK[ElementType(et)]
            return struct.unpack(fmt, self._take(PRIMITIVE_SIZES[ElementType(et)]))[0]
        if et == ElementType.STRING:
            return self._string_ref()
        if et in (ElementType.OBJECT, ElementType.GENERIC_COLLECTION, ElementType.ARRAY):
            marker = self.u8()
            if marker == ElementType.NULL:
                return None
            assert marker == ord("O"), f"bad object ref marker {marker:#x}"
            return ("ref", self.i32())
        if et == ElementType.TYPED_PARAMETER or et == ElementType.CLASS:
            # type handle then value of resolved type — rare in saves
            self.i32()
            return None
        raise ValueError(f"unhandled element type 0x{et:02x} at {self.pos - 1}")

    def _string_ref(self) -> str:
        marker = self.u8()
        if marker == ElementType.NULL:
            return ""
        if marker == ord("M"):
            # inline new string: ObjectId(int32) + length-prefixed utf16
            smid = self.i32()
            n = self.i32()
            s = self._take(n * 2).decode("utf-16-le")
            self.string_values[smid] = s
            return s
        if marker == ord("S"):
            return self.string_values[self.i32()]
        raise ValueError(f"bad string marker {marker:#x}")

    # helpers ------------------------------------------------------------
    def deref(self, val) -> Any:
        if isinstance(val, tuple) and val and val[0] == "ref":
            return self.objects.get(val[1])
        return val

    def resolve(self, val):
        """Return the concrete object/string behind a parsed value."""
        if val is None:
            return None
        if isinstance(val, tuple) and val[0] == "ref":
            return self.objects.get(val[1])
        return val


def load(data: bytes) -> BFReader:
    r = BFReader(data)
    r._pending_ci = []
    r.parse()
    # second pass naming
    for obj in r._pending_ci:
        r._late_name(obj)
    return r
