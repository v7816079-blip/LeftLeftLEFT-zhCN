import filecmp
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE / "work" / "pydeps"))
import UnityPy
from fontTools.ttLib import TTFont

from make_patch import (
    ANALYSIS,
    DATA_NAME,
    FONT_PATH,
    NATIVE_TEXT_TRANSLATIONS,
    ORIGINAL,
    PATCHED,
    RUNTIME_TRANSLATIONS,
    STATIC_TRANSLATIONS,
    replace_length_prefixed,
)

report = json.loads((ANALYSIS / "patch_report.json").read_text(encoding="utf-8"))
expected_changes = defaultdict(set)
for item in report["static"] + report["native_text"]:
    expected_changes[item["file"]].add(item["path_id"])
expected_changes["resources.assets"] = {91, 1470}
changed_files = {f"{DATA_NAME}/{name}" for name in expected_changes}
changed_files.add(f"{DATA_NAME}/il2cpp_data/Metadata/global-metadata.dat")
verification = {"files": {}, "checks": {}}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


OBJECT_CACHE = {}


def object_map(root, filename):
    key = (root, filename)
    if key not in OBJECT_CACHE:
        env = UnityPy.load(str(root / DATA_NAME / filename))
        OBJECT_CACHE[key] = {obj.path_id: obj for obj in env.objects}
    return OBJECT_CACHE[key]


for filename in ("level0", "level1", "level2", "level3", "resources.assets"):
    original_objects = object_map(ORIGINAL, filename)
    patched_objects = object_map(PATCHED, filename)
    assert original_objects.keys() == patched_objects.keys(), f"{filename}: object IDs changed"
    actual_changes = set()
    for path_id in original_objects:
        old_obj = original_objects[path_id]
        new_obj = patched_objects[path_id]
        assert old_obj.type.name == new_obj.type.name, f"{filename}:{path_id}: type changed"
        if old_obj.get_raw_data() != new_obj.get_raw_data():
            actual_changes.add(path_id)
    assert actual_changes == expected_changes[filename], (
        f"{filename}: unexpected object changes: expected {sorted(expected_changes[filename])}, "
        f"got {sorted(actual_changes)}"
    )
    print(f"{filename}: reload OK; only {len(actual_changes)} intended objects changed", flush=True)

for item in report["static"]:
    old_obj = object_map(ORIGINAL, item["file"])[item["path_id"]]
    new_obj = object_map(PATCHED, item["file"])[item["path_id"]]
    old_raw = old_obj.get_raw_data()
    new_raw = new_obj.get_raw_data()
    old_tags = re.findall(r"<[^>]+>", item["old"])
    new_tags = re.findall(r"<[^>]+>", item["new"])
    assert old_tags == new_tags, f"Rich-text tags changed: {item}"
    restored = replace_length_prefixed(
        new_raw, 88, item["new"].encode("utf-8"), item["old"].encode("utf-8"),
        f"verify {item['file']}:{item['path_id']}",
    )
    assert restored == old_raw, f"TMP reverse-check failed: {item}"
    for token in ("{0}", "ESC", "LMB", "Steam", "STEAM"):
        assert (token in item["old"]) == (token in item["new"]), f"Token changed: {token} in {item}"
print(f"TMP reverse-check OK: {len(report['static'])} objects", flush=True)

for item in report["native_text"]:
    old_obj = object_map(ORIGINAL, item["file"])[item["path_id"]]
    new_obj = object_map(PATCHED, item["file"])[item["path_id"]]
    old_raw = old_obj.get_raw_data()
    new_raw = new_obj.get_raw_data()
    assert new_obj.read_typetree()["m_Text"] == item["new"]
    new_data = item["new"].encode("utf-8")
    needle = struct.pack("<i", len(new_data)) + new_data
    offset = new_raw.find(needle)
    assert offset >= 0 and new_raw.find(needle, offset + 1) < 0
    restored = replace_length_prefixed(
        new_raw, offset, new_data, item["old"].encode("utf-8"), "verify TextMesh"
    )
    assert restored == old_raw
print(f"TextMesh reverse-check OK: {len(report['native_text'])} objects", flush=True)

old_font_obj = object_map(ORIGINAL, "resources.assets")[91]
new_font_obj = object_map(PATCHED, "resources.assets")[91]
old_font_raw = old_font_obj.get_raw_data()
new_font_raw = new_font_obj.get_raw_data()
old_font = bytes(old_font_obj.read_typetree()["m_FontData"])
new_font = bytes(new_font_obj.read_typetree()["m_FontData"])
assert new_font == FONT_PATH.read_bytes()
restored = replace_length_prefixed(
    new_font_raw, report["font"]["data_offset"], new_font, old_font, "verify font"
)
assert restored == old_font_raw
old_settings = object_map(ORIGINAL, "resources.assets")[1470].get_raw_data()
new_settings = object_map(PATCHED, "resources.assets")[1470].get_raw_data()
assert struct.unpack_from("<i", new_settings, 0xAC)[0] == 1
assert struct.unpack_from("<iq", new_settings, 0xB0) == (0, 1466)
assert new_settings[:0xAC] + b"\x00\x00\x00\x00" + new_settings[0xBC:] == old_settings
fallback_raw = object_map(PATCHED, "resources.assets")[1466].get_raw_data()
assert struct.unpack_from("<i", fallback_raw, 416)[0] == 1
assert struct.unpack_from("<iq", fallback_raw, 420) == (0, 91)
print("Font data and global fallback reverse-check OK", flush=True)

metadata_relative = Path(DATA_NAME) / "il2cpp_data" / "Metadata" / "global-metadata.dat"
old_metadata = (ORIGINAL / metadata_relative).read_bytes()
new_metadata = (PATCHED / metadata_relative).read_bytes()


def metadata_info(raw):
    magic, version = struct.unpack_from("<2I", raw, 0)
    assert magic == 0xFAB11BAF and version == 39
    table_offset, table_size, table_count = struct.unpack_from("<3I", raw, 8)
    data_offset, data_size, data_count = struct.unpack_from("<3I", raw, 20)
    offsets = list(struct.unpack_from(f"<{table_count}I", raw, table_offset))
    assert offsets[-1] == data_size and len(offsets) == data_count + 1
    literals = [
        raw[data_offset + offsets[i]:data_offset + offsets[i + 1]]
        for i in range(data_count)
    ]
    sections = [struct.unpack_from("<3I", raw, 8 + i * 12) for i in range(31)]
    return literals, sections


old_literals, old_sections = metadata_info(old_metadata)
new_literals, new_sections = metadata_info(new_metadata)
assert len(old_literals) == len(new_literals)
runtime_seen = set()
for index, (old_literal, new_literal) in enumerate(zip(old_literals, new_literals)):
    try:
        old_text = old_literal.decode("utf-8")
    except UnicodeDecodeError:
        old_text = None
    if old_text in RUNTIME_TRANSLATIONS:
        assert new_literal.decode("utf-8") == RUNTIME_TRANSLATIONS[old_text]
        runtime_seen.add(old_text)
        old_text_tags = re.findall(r"<[^>]+>", old_text)
        new_text = new_literal.decode("utf-8")
        assert old_text_tags == re.findall(r"<[^>]+>", new_text)
        for token in ("{0}", "ESC", "LMB", "W / S", "A / D", "SPACE", "MOUSE", "Steam", "STEAM"):
            assert (token in old_text) == (token in new_text), f"Metadata token changed: {token} in {old_text}"
    else:
        assert old_literal == new_literal, f"Unexpected metadata literal change at {index}"
assert runtime_seen == set(RUNTIME_TRANSLATIONS)
for index in range(2, 31):
    old_offset, old_size, old_count = old_sections[index]
    new_offset, new_size, new_count = new_sections[index]
    assert (old_size, old_count) == (new_size, new_count)
    assert old_metadata[old_offset:old_offset + old_size] == new_metadata[new_offset:new_offset + new_size], (
        f"Metadata section {index} content changed"
    )
print(f"Metadata check OK: {len(runtime_seen)} intended literals; all other sections identical", flush=True)

original_files = {p.relative_to(ORIGINAL).as_posix() for p in ORIGINAL.rglob("*") if p.is_file()}
patched_files = {p.relative_to(PATCHED).as_posix() for p in PATCHED.rglob("*") if p.is_file()}
assert original_files == patched_files
for relative in sorted(original_files):
    old_path = ORIGINAL / relative
    new_path = PATCHED / relative
    if relative not in changed_files:
        assert filecmp.cmp(old_path, new_path, shallow=False), f"Unexpected file change: {relative}"
    else:
        assert not filecmp.cmp(old_path, new_path, shallow=False), f"File did not change: {relative}"
        verification["files"][relative] = {
            "original_sha256": sha256(old_path),
            "patched_sha256": sha256(new_path),
            "original_bytes": old_path.stat().st_size,
            "patched_bytes": new_path.stat().st_size,
        }
print("Full-tree comparison OK: only the six intended files changed", flush=True)

font = TTFont(str(FONT_PATH), lazy=True)
cmap = font.getBestCmap()
all_translations = {}
for mapping in (STATIC_TRANSLATIONS, NATIVE_TEXT_TRANSLATIONS, RUNTIME_TRANSLATIONS):
    all_translations.update(mapping)
required = sorted({char for text in all_translations.values() for char in text if ord(char) > 127})
missing = [char for char in required if ord(char) not in cmap]
assert not missing, f"Font is missing characters: {missing}"
font.close()
verification["checks"] = {
    "tmp_objects": len(report["static"]),
    "textmesh_objects": len(report["native_text"]),
    "runtime_literals": len(runtime_seen),
    "changed_files": len(changed_files),
    "font_non_ascii_characters_checked": len(required),
    "font_missing_characters": missing,
    "status": "passed",
}
(ANALYSIS / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"All checks passed; SimHei covers all {len(required)} non-ASCII characters used", flush=True)
