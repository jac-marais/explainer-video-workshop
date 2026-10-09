#!/usr/bin/env python3
"""Intake checks on third-party 3D assets before a three.js scene loads them. Prints failures, then one summary line per file; exits 1 on any failure.

  check_asset.py FILE... [--max-bytes N] [--max-side PX] [--max-pixels N]

Per file: `FAIL <path>: <reason>` lines, then `ok|FAIL <path> kind=<kind> bytes=<n> sha256=<hex>` (sha256 is for the asset ledger),
plus `needs=<loaders>` for required glTF extensions and `other=<n>` for ZIP entries outside the allowed extensions.
The type comes from the bytes, never from the extension. Nothing is decoded, extracted or run; only headers are read.

Checks: size and emptiness; Git LFS pointers; GLB header, chunk layout and BIN length; glTF JSON (version, buffer
and image URIs that are remote or leave the asset directory, files missing beside a .gltf, buffer and view ranges,
accessor views, total declared buffer size); the dimensions of every image, embedded or referenced (PNG, JPEG, WebP,
Radiance HDR, KTX2, OpenEXR); OBJ/MTL texture and library paths; ZIP entry names, symlinks, sizes and compression ratio.
glTF JSON (a .gltf or a GLB chunk) is capped at 16 MB. A GLB is checked for external references the same way as a .gltf.
Required extensions map to loaders: KHR_draco_mesh_compression to DRACOLoader, EXT_meshopt_compression to MeshoptDecoder,
KHR_texture_basisu to KTX2Loader; any other required extension is listed by name and does not fail.

Needs only the standard library.
"""
import argparse, base64, hashlib, json, re, stat, struct, sys, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, unquote_to_bytes

HEAD = 65536
JSON_LIMIT = 16 * 1024 * 1024
ZIP_TOTAL_FACTOR, ZIP_MAX_RATIO = 10, 200
ZIP_ALLOWED = {"glb", "gltf", "bin", "obj", "mtl", "png", "jpg", "jpeg", "webp", "ktx2", "hdr", "exr", "txt", "md"}
LOADERS = {"KHR_draco_mesh_compression": "DRACOLoader", "EXT_meshopt_compression": "MeshoptDecoder", "KHR_texture_basisu": "KTX2Loader"}
MAX_FAILS_SHOWN = 10
MAX_JPEG_SEGMENTS = 10_000


class Report:
    def __init__(self):
        self.kind, self.size, self.sha256 = "unknown", 0, "-"
        self.fails, self.needs, self.other = [], [], None

    def fail(self, message):
        self.fails.append(message)


# Readers: read(offset, n) returns up to n bytes, so a file, a buffer view and decoded data look the same.

def path_reader(path, base=0):
    def read(offset, n):
        with open(path, "rb") as f:
            f.seek(base + offset)
            return f.read(n)
    return read


def bytes_reader(data):
    return lambda offset, n: data[offset:offset + n]


def sub_reader(read, start, length):
    return lambda offset, n: read(start + offset, max(0, min(n, length - offset)))


# Image headers

def header(read, n):
    data = read(0, n)
    if len(data) < n:
        raise ValueError("truncated header")
    return data


def png_size(read):
    data = header(read, 24)
    if data[12:16] != b"IHDR":
        raise ValueError("first chunk is not IHDR")
    return struct.unpack(">II", data[16:24])


def jpeg_size(read):
    pos = 2
    for _ in range(MAX_JPEG_SEGMENTS):
        seg = read(pos, 9)
        if len(seg) < 2 or seg[0] != 0xFF:
            raise ValueError("bad marker before any frame header")
        marker = seg[1]
        if marker == 0xFF:  # fill byte
            pos += 1
        elif marker == 0x01 or 0xD0 <= marker <= 0xD8:  # markers without a length
            pos += 2
        elif 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):  # SOF, not DHT/JPG/DAC
            if len(seg) < 9:
                raise ValueError("truncated frame header")
            height, width = struct.unpack(">HH", seg[5:9])
            return width, height
        elif marker in (0xD9, 0xDA):
            raise ValueError("image data starts before any frame header")
        else:
            if len(seg) < 4:
                raise ValueError("truncated segment")
            length = struct.unpack(">H", seg[2:4])[0]
            if length < 2:
                raise ValueError("bad segment length")
            pos += 2 + length
    raise ValueError("no frame header found")


def webp_size(read):
    data = read(0, 30)
    chunk = data[12:16]
    if len(data) < (25 if chunk == b"VP8L" else 30):
        raise ValueError("truncated header")
    if chunk == b"VP8 ":
        if data[23:26] != b"\x9d\x01\x2a":
            raise ValueError("bad VP8 start code")
        width, height = struct.unpack("<HH", data[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        if data[20] != 0x2F:
            raise ValueError("bad VP8L signature")
        bits = struct.unpack("<I", data[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
    raise ValueError(f"unknown WebP chunk {chunk!r}")


def hdr_size(read):
    found = re.search(rb"\n\r?\n([-+][XY]) (\d{1,9}) ([-+][XY]) (\d{1,9})", read(0, 4096))
    if not found or found[1][1:] == found[3][1:]:
        raise ValueError("no resolution line")
    first, second = int(found[2]), int(found[4])
    return (second, first) if found[1][1:] == b"Y" else (first, second)


def ktx2_size(read):
    data = header(read, 28)
    width, height = struct.unpack("<II", data[20:28])
    return width, max(height, 1)  # a 1D texture stores height 0


def exr_size(read):
    data = read(0, HEAD)
    pos = 8
    while True:
        name_end = data.find(b"\0", pos)
        if name_end < 0:
            raise ValueError("header attributes not terminated")
        name = data[pos:name_end]
        if not name:
            raise ValueError("no dataWindow attribute")
        type_end = data.find(b"\0", name_end + 1)
        if type_end < 0 or type_end + 5 > len(data):
            raise ValueError("truncated header")
        length = struct.unpack("<I", data[type_end + 1:type_end + 5])[0]
        value = data[type_end + 5:type_end + 5 + length]
        if name == b"dataWindow":
            if length != 16 or len(value) != 16:
                raise ValueError("bad dataWindow")
            x0, y0, x1, y1 = struct.unpack("<4i", value)
            return x1 - x0 + 1, y1 - y0 + 1
        pos = type_end + 5 + length


IMAGE_SIZE = {"png": png_size, "jpeg": jpeg_size, "webp": webp_size, "hdr": hdr_size, "ktx2": ktx2_size, "exr": exr_size}
MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg", b"#?RADIANCE": "hdr", b"#?RGBE": "hdr",
         b"\xabKTX 20\xbb\r\n\x1a\n": "ktx2", b"v/1\x01": "exr"}


def image_kind(head):
    for magic, kind in MAGIC.items():
        if head.startswith(magic):
            return kind
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def check_image(read, a):
    """Failure messages for one image whose bytes read() serves."""
    kind = image_kind(read(0, 12))
    if kind is None:
        return ["not a PNG, JPEG, WebP, HDR, KTX2 or EXR image"]
    try:
        width, height = IMAGE_SIZE[kind](read)
    except ValueError as e:
        return [f"{kind}: {e}"]
    if width < 1 or height < 1:
        return [f"{kind} {width}x{height}: empty image"]
    fails = []
    if max(width, height) > a.max_side:
        fails.append(f"{kind} {width}x{height}: a side is over --max-side {a.max_side}")
    if width * height > a.max_pixels:
        fails.append(f"{kind} {width}x{height}: {width * height} pixels, over --max-pixels {a.max_pixels}")
    return fails


# References

def path_problem(ref):
    """Why a reference must not be followed ("remote URI" or "path traversal"), or None. Percent-decodes first."""
    path = unquote(ref)
    if re.search(r"[\x00-\x1f\x7f]", path):
        return "path traversal (control character)"
    path = path.strip()
    if path.startswith("//") or re.match(r"[A-Za-z][A-Za-z0-9+.-]+:", path):
        return "remote URI"
    if path.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", path) or "\\" in path or ".." in path.split("/"):
        return "path traversal"
    return None


def load_uri(uri, where, directory, a, rep):
    """(read, size) for a glTF URI, or None after recording why it cannot be used."""
    if not isinstance(uri, str):
        rep.fail(f"{where}: uri is not a string")
        return None
    if uri.lstrip()[:5].lower() == "data:":
        head, comma, payload = uri.lstrip().partition(",")
        if not comma:
            rep.fail(f"{where}: malformed data URI")
            return None
        data = base64.b64decode(payload) if head.lower().endswith(";base64") else unquote_to_bytes(payload)
        return bytes_reader(data), len(data)
    problem = path_problem(uri)
    if problem:
        rep.fail(f"{where}: {problem} {uri[:80]!r}")
        return None
    target = (directory / unquote(uri.strip())).resolve()
    if not target.is_relative_to(directory.resolve()):
        rep.fail(f"{where}: path traversal {uri[:80]!r} resolves outside the asset directory")
        return None
    if not target.is_file():
        rep.fail(f"{where}: missing file {uri[:80]!r}")
        return None
    size = target.stat().st_size
    if size > a.max_bytes:
        rep.fail(f"{where}: {uri[:80]!r} is {size} bytes, over --max-bytes {a.max_bytes}")
        return None
    return path_reader(target), size


# glTF

def items(doc, key):
    value = doc.get(key, [])
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{key} is not a list of objects")
    return value


def count(obj, key, where, default=None):
    value = obj.get(key, default)
    if type(value) is not int or value < 0:
        raise ValueError(f"{where}: {key} is not a non-negative integer")
    return value


def parse_json(raw):
    try:
        doc = json.loads(raw)
    except (ValueError, RecursionError) as e:
        raise ValueError(f"invalid JSON: {e}")
    if not isinstance(doc, dict):
        raise ValueError("JSON root is not an object")
    return doc


def check_gltf(doc, a, rep, directory, glb_bin):
    """glTF JSON checks. glb_bin is (read, length) for the GLB BIN chunk, or None."""
    asset = doc.get("asset")
    version = asset.get("version") if isinstance(asset, dict) else None
    if not (isinstance(version, str) and version.startswith("2")):
        rep.fail(f"asset.version is {version!r}, want 2.x")

    required = doc.get("extensionsRequired", [])
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        raise ValueError("extensionsRequired is not a list of strings")
    rep.needs = list(dict.fromkeys(LOADERS.get(name, name) for name in required))

    buffers = items(doc, "buffers")
    readers, total = {}, 0
    for i, buf in enumerate(buffers):
        where = f"buffers[{i}]"
        length = count(buf, "byteLength", where)
        total += length
        if "uri" not in buf:
            if i != 0 or rep.kind != "glb":
                rep.fail(f"{where}: no uri")
            elif glb_bin is None:
                rep.fail(f"{where}: no uri and the GLB has no BIN chunk")
            else:
                read, bin_length = glb_bin
                if length > bin_length:
                    rep.fail(f"{where}: byteLength {length} is over the BIN chunk's {bin_length} bytes")
                readers[i] = read
            continue
        loaded = load_uri(buf["uri"], where, directory, a, rep)
        if loaded is None:
            continue
        readers[i] = loaded[0]
        if loaded[1] < length:
            rep.fail(f"{where}: byteLength {length} is over the {loaded[1]} bytes of data")
    if total > a.max_bytes:
        rep.fail(f"declared buffers total {total} bytes, over --max-bytes {a.max_bytes}")

    views = items(doc, "bufferViews")
    for i, view in enumerate(views):
        where = f"bufferViews[{i}]"
        index = view.get("buffer")
        if type(index) is not int or not 0 <= index < len(buffers):
            rep.fail(f"{where}: buffer {index!r} does not exist")
            continue
        end = count(view, "byteOffset", where, 0) + count(view, "byteLength", where)
        if end > buffers[index]["byteLength"]:
            rep.fail(f"{where}: ends at byte {end}, past the {buffers[index]['byteLength']} bytes of buffers[{index}]")

    for i, accessor in enumerate(items(doc, "accessors")):
        index = accessor.get("bufferView")
        if index is not None and (type(index) is not int or not 0 <= index < len(views)):
            rep.fail(f"accessors[{i}]: bufferView {index!r} does not exist")

    for i, image in enumerate(items(doc, "images")):
        where = f"images[{i}]"
        index = image.get("bufferView")
        if "uri" in image:
            loaded = load_uri(image["uri"], where, directory, a, rep)
            if loaded is None:
                continue
            read = loaded[0]
        elif index is not None:
            view = views[index] if type(index) is int and 0 <= index < len(views) else None
            buffer = view.get("buffer") if view else None
            if type(buffer) is not int or buffer not in readers:
                rep.fail(f"{where}: bufferView {index!r} has no readable data")
                continue
            read = sub_reader(readers[buffer], count(view, "byteOffset", where, 0), count(view, "byteLength", where))
        else:
            rep.fail(f"{where}: neither uri nor bufferView")
            continue
        for message in check_image(read, a):
            rep.fail(f"{where}: {message}")


def check_gltf_file(path, size, a, rep):
    if size > JSON_LIMIT:
        raise ValueError(f"glTF JSON is {size} bytes, over the {JSON_LIMIT} limit")
    doc = parse_json(path.read_bytes())
    if "asset" not in doc:
        rep.kind = "unknown"
        raise ValueError("unknown type: JSON without an asset object")
    check_gltf(doc, a, rep, path.parent, None)


def check_glb(path, size, a, rep):
    if size < 12:
        raise ValueError("shorter than the 12-byte GLB header")
    with open(path, "rb") as f:
        _, version, total = struct.unpack("<4sII", f.read(12))
        if version != 2:
            raise ValueError(f"GLB version {version}, want 2")
        if total != size:
            rep.fail(f"header length {total} != file size {size}")
        chunks, offset = [], 12
        while offset < size:
            f.seek(offset)
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                rep.fail(f"{size - offset} stray bytes after the last chunk")
                break
            length, kind = struct.unpack("<I4s", chunk_header)
            if offset + 8 + length > size:
                rep.fail(f"chunk {len(chunks)} {kind!r} overruns the file: {length} bytes declared, {size - offset - 8} left")
                break
            chunks.append((kind, offset + 8, length))
            offset += 8 + length
        if not chunks:
            raise ValueError("no complete chunk")
        kind, start, length = chunks[0]
        if kind != b"JSON":
            raise ValueError(f"first chunk is {kind!r}, want JSON")
        if length > JSON_LIMIT:
            raise ValueError(f"JSON chunk is {length} bytes, over the {JSON_LIMIT} limit")
        f.seek(start)
        doc = parse_json(f.read(length))
    bin_chunk = next((c for c in chunks[1:] if c[0] == b"BIN\0"), None)
    glb_bin = bin_chunk and (sub_reader(path_reader(path), bin_chunk[1], bin_chunk[2]), bin_chunk[2])
    check_gltf(doc, a, rep, path.parent, glb_bin)


# OBJ, MTL, ZIP

def text_kind(head):
    if b"\0" in head:
        return None
    first_words = {line.split()[0] for line in head.decode("utf-8", "replace").splitlines() if line.split() and line.split()[0][0] != "#"}
    if "newmtl" in first_words:
        return "mtl"
    if first_words & {"v", "vt", "vn", "f", "mtllib", "usemtl"}:
        return "obj"
    return None


def check_obj(path, size, a, rep):
    with open(path, "rb") as f:
        for number, line in enumerate(f, 1):
            words = line.decode("utf-8", "replace").split()
            if not words:
                continue
            keyword = words[0].lower()
            if keyword in ("mtllib", "bump", "disp", "decal", "refl") or keyword.startswith("map_"):
                for ref in words[1:]:
                    # MTL files written on Windows use backslashes as separators.
                    problem = path_problem(ref.replace("\\", "/"))
                    if problem:
                        rep.fail(f"line {number}: {words[0]} {ref[:80]!r}: {problem}")


def check_zip(path, size, a, rep):
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as e:
        raise ValueError(f"bad zip: {e}")
    total, rep.other = 0, 0
    with archive:
        for info in archive.infolist():
            name = info.filename
            total += info.file_size
            reasons = []
            if name.startswith("/") or re.match(r"[A-Za-z]:", name):
                reasons.append("absolute path")
            if ".." in name.replace("\\", "/").split("/"):
                reasons.append("path traversal")
            if "\\" in name:
                reasons.append("backslash")
            if stat.S_ISLNK(info.external_attr >> 16):
                reasons.append("symlink")
            # The sizes come from the headers; nothing is extracted to confirm them.
            if info.file_size > ZIP_MAX_RATIO * max(info.compress_size, 1):
                reasons.append(f"compression ratio {info.file_size / max(info.compress_size, 1):.0f}:1, over {ZIP_MAX_RATIO}:1")
            if reasons:
                rep.fail(f"entry {name[:80]!r}: {', '.join(reasons)}")
            if not name.endswith("/") and PurePosixPath(name).suffix.lower().lstrip(".") not in ZIP_ALLOWED:
                rep.other += 1
    if total > ZIP_TOTAL_FACTOR * a.max_bytes:
        rep.fail(f"{total} bytes uncompressed, over {ZIP_TOTAL_FACTOR} x --max-bytes {a.max_bytes}")


def check_image_file(path, size, a, rep):
    for message in check_image(path_reader(path), a):
        rep.fail(message)


# Driver

def detect(head):
    if head.startswith(b"version https://git-lfs"):
        return "lfs-pointer"
    if head.startswith(b"glTF"):
        return "glb"
    if head.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        return "zip"
    if head.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"{"):
        return "gltf"
    return image_kind(head) or text_kind(head) or "unknown"


CHECKS = {"glb": check_glb, "gltf": check_gltf_file, "obj": check_obj, "mtl": check_obj, "zip": check_zip,
          **{kind: check_image_file for kind in IMAGE_SIZE}}


def check_file(path, a):
    rep = Report()
    if not path.is_file():
        rep.fail("cannot read: not a regular file")
        return rep
    try:
        with open(path, "rb") as f:
            head = f.read(HEAD)
            digest = hashlib.sha256(head)
            rep.size = len(head)
            while chunk := f.read(1 << 20):
                digest.update(chunk)
                rep.size += len(chunk)
    except OSError as e:
        rep.fail(f"cannot read: {e}")
        return rep
    rep.sha256 = digest.hexdigest()
    rep.kind = detect(head)
    if rep.size == 0:
        rep.kind = "empty"
        rep.fail("empty file")
    elif rep.size > a.max_bytes:
        rep.fail(f"{rep.size} bytes, over --max-bytes {a.max_bytes}")
    elif rep.kind == "lfs-pointer":
        rep.fail("Git LFS pointer, not the asset")
    elif rep.kind == "unknown":
        rep.fail("unknown type")
    else:
        try:
            CHECKS[rep.kind](path, rep.size, a, rep)
        except ValueError as e:
            rep.fail(str(e))
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path, metavar="FILE")
    ap.add_argument("--max-bytes", type=int, default=200_000_000, help="largest allowed file, and largest total of declared glTF buffers")
    ap.add_argument("--max-side", type=int, default=8192, help="longest allowed image side, px")
    ap.add_argument("--max-pixels", type=int, default=64 * 1024 * 1024, help="most pixels allowed in one image")
    a = ap.parse_args()

    failed = False
    for path in a.files:
        rep = check_file(path, a)
        for message in rep.fails[:MAX_FAILS_SHOWN]:
            print(f"FAIL {path}: {message}")
        if len(rep.fails) > MAX_FAILS_SHOWN:
            print(f"FAIL {path}: ... and {len(rep.fails) - MAX_FAILS_SHOWN} more")
        summary = f"{'FAIL' if rep.fails else 'ok'} {path} kind={rep.kind} bytes={rep.size} sha256={rep.sha256}"
        if rep.needs:
            summary += f" needs={','.join(rep.needs)}"
        if rep.other is not None:
            summary += f" other={rep.other}"
        print(summary)
        failed = failed or bool(rep.fails)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
