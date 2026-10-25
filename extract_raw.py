import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "work" / "pydeps"))
import UnityPy

BASE = Path(__file__).parent
ROOT = BASE / "work" / "original" / "LeftLeftLEFT_Data"
OUT = BASE / "work" / "analysis"
OUT.mkdir(parents=True, exist_ok=True)
FILES = ["globalgamemanagers.assets", "level0", "level1", "level2", "level3", "resources.assets", "sharedassets0.assets", "sharedassets1.assets"]


def raw_strings(raw):
    found = []
    for offset in range(0, len(raw) - 4, 4):
        size = struct.unpack_from("<i", raw, offset)[0]
        if size < 1 or size > 65536 or offset + 4 + size > len(raw):
            continue
        data = raw[offset + 4:offset + 4 + size]
        if b"\x00" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if any(ord(c) < 32 and c not in "\r\n\t" for c in text):
            continue
        if not re.search(r"[A-Za-z]{2}", text):
            continue
        printable = sum(c.isprintable() or c in "\r\n\t" for c in text) / len(text)
        if printable < 0.95:
            continue
        found.append({"offset": offset, "size": size, "value": text})
    return found

records = []
native_texts = []
scripts = Counter()
errors = []
for filename in FILES:
    print(f"Loading {filename}...", flush=True)
    env = UnityPy.load(str(ROOT / filename))
    count = 0
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                head = obj.parse_monobehaviour_head()
                script = head.m_Script.deref_parse_as_object()
                script_name = f"{script.m_Namespace + '.' if script.m_Namespace else ''}{script.m_ClassName}"
                scripts[script_name] += 1
                try:
                    game_object = head.m_GameObject.deref_parse_as_object().m_Name
                except Exception:
                    game_object = ""
                strings = raw_strings(obj.get_raw_data())
                if strings:
                    records.append({
                        "file": filename,
                        "path_id": obj.path_id,
                        "script": script_name,
                        "assembly": script.m_AssemblyName,
                        "game_object": game_object,
                        "byte_size": obj.byte_size,
                        "strings": strings,
                    })
                    count += 1
            except Exception as exc:
                errors.append({"file": filename, "path_id": obj.path_id, "error": str(exc)})
        elif obj.type.name in ("TextMesh", "TextAsset", "Font"):
            try:
                tree = obj.read_typetree()
                native_texts.append({"file": filename, "path_id": obj.path_id, "type": obj.type.name, "tree": tree})
            except Exception as exc:
                errors.append({"file": filename, "path_id": obj.path_id, "error": str(exc)})
    print(f"  objects with strings: {count}", flush=True)

(OUT / "raw_mono_strings.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "native_texts.json").write_text(json.dumps(native_texts, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "raw_scripts.json").write_text(json.dumps(scripts.most_common(), ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "raw_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Done: {len(records)} objects, {len(errors)} errors")
