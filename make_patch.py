import json
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE / "work" / "pydeps"))
import UnityPy

ORIGINAL = BASE / "work" / "original"
PATCHED = BASE / "work" / "patched"
DATA_NAME = "LeftLeftLEFT_Data"
ANALYSIS = BASE / "work" / "analysis"
FONT_PATH = BASE / "work" / "simhei.ttf"

STATIC_TRANSLATIONS = {
    "LOADING...": "加载中……",
    "FRIEND": "好友",
    "PLAYTEST": "试玩版",
    "WAITING FOR THE DRIVER\nTO PICK A STAGE": "等待驾驶员\n选择关卡",
    "BACK": "返回",
    "OFF": "关",
    "BEST  —": "最佳  —",
    "NAVIGATOR": "领航员",
    "Pick a friend below.": "请在下方选择一位好友。",
    "INVITE A NAVIGATOR": "邀请领航员",
    "MAIN MENU": "主菜单",
    "STAGE 01": "关卡 01",
    "STAGE 02": "关卡 02",
    "STAGE 03": "关卡 03",
    "LEAVE": "离开",
    "START": "开始",
    "STEAM OFF": "STEAM 离线",
    "FPS CAP": "帧率上限",
    "VOLUME": "音量",
    "CREW": "车组",
    "PICK A STAGE": "选择关卡",
    "INVITE": "邀请",
    "CREW 1/2": "车组 1/2",
    "SETTINGS": "设置",
    "<color=#998050>DRIVER</color>     steers the wreck\n<color=#998050>NAVIGATOR</color>  calls the turns": "<color=#998050>驾驶员</color>  负责操控车辆\n<color=#998050>领航员</color>  负责提示转弯",
    "QUIT": "退出",
    "empty seat": "空位",
    "MUSIC": "音乐",
    "GAME": "游戏",
    "MENU": "菜单",
    "OG MAP  ·  first ever created for Left! Left! LEFT!": "原始地图  ·  本作最早制作的地图",
    "LEAVE SESSION": "离开会话",
    "RESTART": "重新开始",
    "ESC  BACK TO THE ROAD": "ESC  返回道路",
    "BACK TO MENU": "返回主菜单",
    "R  RESTART      ESC  MENU": "R  重开      ESC  菜单",
    "RESUME": "继续",
    "DRIVER": "驾驶员",
    "PAUSED": "已暂停",
}

NATIVE_TEXT_TRANSLATIONS = {
    "START": "起点",
    "FINISH": "终点",
}

RUNTIME_TRANSLATIONS = {
    "CONNECTING TO STEAM...": "正在连接 STEAM……",
    "STEAM LOBBY FAILED  -  restart the game": "STEAM 大厅连接失败  -  请重启游戏",
    "STEAM OFF  -  ": "STEAM 离线  -  ",
    "WAITING FOR THE DRIVER...": "正在等待驾驶员……",
    "LOBBY READY": "大厅已就绪",
    "LOBBY  -  invite a navigator": "大厅  -  邀请一位领航员",
    "Host — Driver": "主机 — 驾驶员",
    "Client — Navigator": "客户端 — 领航员",
    "Driver left the session.": "驾驶员已离开会话。",
    "Invite failed — try from Steam friends.": "邀请失败——请从 Steam 好友列表邀请。",
    "Invite sent to ": "邀请已发送给 ",
    "No online friends here — invite from the Steam overlay.": "这里没有在线好友——请通过 Steam 界面邀请。",
    "No online friends. Invite from the Steam friends list instead.": "没有在线好友。请改用 Steam 好友列表邀请。",
    "Online friends: {0}. Pick one below (or invite from Steam).": "在线好友：{0}。请在下方选择（或从 Steam 邀请）。",
    "Online friends: {0}. Pick one, or use the Steam overlay.": "在线好友：{0}。请选择一位，或使用 Steam 界面邀请。",
    "Offline (solo stage)": "离线（单人关卡）",
    "This PC's Wi-Fi IP (other PC types this):": "本机 Wi-Fi IP（在另一台电脑上输入）：",
    "(no LAN IP — connect Wi-Fi first)": "（未获取局域网 IP——请先连接 Wi-Fi）",
    "Host failed — port ": "主机创建失败——端口 ",
    "PLAYTEST BUILD": "试玩版本",
    "PRESS R WHEN READY": "准备好后按 R",
    "READY": "就绪",
    "FINISHED": "已完成",
    "DOOR ON": "车门 开",
    "DOOR OFF": "车门 关",
    "MUD ON": "泥污 开",
    "MUD OFF": "泥污 关",
    "LIGHT": "浅色",
    "DARK": "深色",
    "CREW ": "车组 ",
    "DRIVER": "驾驶员",
    "NAVIGATOR": "领航员",
    "empty seat": "空位",
    "  (you)": "  （你）",
    "OFF": "关",
    "Host (you drive)": "主机（你负责驾驶）",
    "Join (you navigate)": "加入（你负责领航）",
    "STREET": "街道",
    "CONTROLS": "操作说明",
    "E            grab / drop tablet\nHOLD E       dash knob = wipers\n             (drop tablet first)\nLMB + look   grab open door, slam shut\nMOUSE        look around": "E            拿起 / 放下平板\n长按 E       仪表板旋钮 = 雨刷\n             （先放下平板）\nLMB + 视角   抓住打开的车门并关上\nMOUSE      环顾四周",
    "W / S     throttle / brake\nA / D     steer\nSPACE     handbrake\nMOUSE     look around": "W / S     油门 / 刹车\nA / D     转向\nSPACE     手刹\nMOUSE     环顾四周",
    "You're in an early playtest with limited content.\nStages, UI and feel can still change a lot —\nthis is not what the final game has to look like.\nExpect bugs, jank, and unfinished bits.\n\nThanks for breaking it with us.": "你正在参与内容有限的早期试玩。\n关卡、界面和手感仍可能有较大改动——\n本次试玩并不代表游戏的最终形态。\n可能会遇到程序错误、卡顿和未完成内容。\n\n感谢你与我们一起把它“玩坏”。",
    "      NAVIGATOR  ": "      领航员  ",
    "DRIVER  ": "驾驶员  ",
    "DRIVER  —      NAVIGATOR  —": "驾驶员  —      领航员  —",
}

report = {
    "static": [],
    "native_text": [],
    "runtime": [],
    "font": {},
    "settings": {},
    "files": {},
}


def aligned4(value):
    return (value + 3) & ~3


def replace_length_prefixed(raw, offset, old_data, new_data, label):
    old_size = struct.unpack_from("<i", raw, offset)[0]
    assert old_size == len(old_data), f"{label}: expected {len(old_data)} bytes, found {old_size}"
    assert raw[offset + 4:offset + 4 + old_size] == old_data, f"{label}: source data mismatch"
    old_end = offset + 4 + old_size
    old_aligned_end = aligned4(old_end)
    assert old_aligned_end <= len(raw), f"{label}: source exceeds object"
    assert not any(raw[old_end:old_aligned_end]), f"{label}: nonzero source padding"
    new_end = offset + 4 + len(new_data)
    new_aligned_end = aligned4(new_end)
    return (
        raw[:offset]
        + struct.pack("<i", len(new_data))
        + new_data
        + bytes(new_aligned_end - new_end)
        + raw[old_aligned_end:]
    )


def save_environment(env, target):
    assets = env.assets
    assert len(assets) == 1, f"{target.name}: expected one serialized file, got {len(assets)}"
    target.write_bytes(assets[0].save())


def patch_assets():
    records = json.loads((ANALYSIS / "raw_mono_strings.json").read_text(encoding="utf-8"))
    native = json.loads((ANALYSIS / "native_texts.json").read_text(encoding="utf-8"))
    by_file = defaultdict(list)
    for item in records:
        if item["file"] not in ("level0", "level1", "level2", "level3"):
            continue
        if item["script"] != "TMPro.TextMeshProUGUI":
            continue
        for entry in item["strings"]:
            if entry["offset"] == 88 and entry["value"] in STATIC_TRANSLATIONS:
                by_file[item["file"]].append((item["path_id"], entry))
    for item in native:
        if item["type"] == "TextMesh" and item["tree"].get("m_Text") in NATIVE_TEXT_TRANSLATIONS:
            by_file[item["file"]].append((item["path_id"], item))

    used_static = set()
    for filename in ("level0", "level1", "level2", "level3", "resources.assets"):
        source = ORIGINAL / DATA_NAME / filename
        target = PATCHED / DATA_NAME / filename
        env = UnityPy.load(str(source))
        objects = {obj.path_id: obj for obj in env.objects}
        if filename != "resources.assets":
            expected = by_file[filename]
            assert expected, f"{filename}: no planned changes"
            for path_id, entry in expected:
                obj = objects[path_id]
                raw = obj.get_raw_data()
                if isinstance(entry, dict) and "value" in entry:
                    old_text = entry["value"]
                    new_text = STATIC_TRANSLATIONS[old_text]
                    new_raw = replace_length_prefixed(
                        raw, 88, old_text.encode("utf-8"), new_text.encode("utf-8"),
                        f"{filename}:{path_id}",
                    )
                    used_static.add(old_text)
                    kind = "TMPro.TextMeshProUGUI"
                else:
                    old_text = entry["tree"]["m_Text"]
                    new_text = NATIVE_TEXT_TRANSLATIONS[old_text]
                    old_data = old_text.encode("utf-8")
                    needle = struct.pack("<i", len(old_data)) + old_data
                    offset = raw.find(needle)
                    assert offset >= 0 and raw.find(needle, offset + 1) < 0, f"{filename}:{path_id}: TextMesh string not unique"
                    new_raw = replace_length_prefixed(
                        raw, offset, old_data, new_text.encode("utf-8"), f"{filename}:{path_id}"
                    )
                    kind = "UnityEngine.TextMesh"
                obj.set_raw_data(new_raw)
                report["static" if kind.startswith("TMPro") else "native_text"].append({
                    "file": filename, "path_id": path_id, "type": kind,
                    "old": old_text, "new": new_text,
                })
        else:
            font_obj = objects[91]
            tree = font_obj.read_typetree()
            old_font = bytes(tree["m_FontData"])
            new_font = FONT_PATH.read_bytes()
            assert len(old_font) == 350200 and len(new_font) == 9745792
            raw = font_obj.get_raw_data()
            needle = struct.pack("<i", len(old_font)) + old_font
            offset = raw.find(needle)
            assert offset >= 0 and raw.find(needle, offset + 1) < 0, "Font 91 data not unique"
            new_raw = replace_length_prefixed(raw, offset, old_font, new_font, "resources.assets:91")
            font_obj.set_raw_data(new_raw)
            report["font"] = {
                "file": filename, "path_id": 91, "source": FONT_PATH.name,
                "old_bytes": len(old_font), "new_bytes": len(new_font), "data_offset": offset,
            }

            settings = objects[1470]
            raw = settings.get_raw_data()
            assert len(raw) == 300
            assert raw[0x2C:0x34] == b"\x01\x00\x00\x002\x00\x00\x00"
            assert struct.unpack_from("<iq", raw, 0x64) == (0, 1467)
            assert struct.unpack_from("<i", raw, 0xAC)[0] == 0
            assert struct.unpack_from("<i", raw, 0xB0)[0] == 1
            assert struct.unpack_from("<iq", raw, 0xB8) == (0, 1468)
            # The game's TMP_Settings layout places the empty global fallback list at 0xAC.
            # Insert one same-file PPtr and shift only the following fields.
            new_raw = raw[:0xAC] + struct.pack("<i", 1) + struct.pack("<iq", 0, 1466) + raw[0xB0:]
            assert len(new_raw) == 312
            assert new_raw[:0xAC] == raw[:0xAC] and new_raw[0xBC:] == raw[0xB0:]
            assert struct.unpack_from("<iq", new_raw, 0xB0) == (0, 1466)
            settings.set_raw_data(new_raw)
            report["settings"] = {
                "file": filename, "path_id": 1470, "fallback_offset": 0xAC,
                "fallback_path_id": 1466, "old_bytes": len(raw), "new_bytes": len(new_raw),
            }
        save_environment(env, target)
        report["files"][filename] = {"source_bytes": source.stat().st_size, "patched_bytes": target.stat().st_size}
        print(f"Patched {filename}: {target.stat().st_size} bytes", flush=True)
    missing = set(STATIC_TRANSLATIONS) - used_static
    assert not missing, f"Static translations not used: {sorted(missing)}"


def patch_metadata():
    relative = Path(DATA_NAME) / "il2cpp_data" / "Metadata" / "global-metadata.dat"
    source = ORIGINAL / relative
    target = PATCHED / relative
    raw = source.read_bytes()
    magic, version = struct.unpack_from("<2I", raw, 0)
    assert magic == 0xFAB11BAF and version == 39
    table_offset, table_size, table_count = struct.unpack_from("<3I", raw, 8)
    data_offset, data_size, data_count = struct.unpack_from("<3I", raw, 20)
    first_section_offset = table_offset
    section_count = (first_section_offset - 8) // 12
    assert section_count == 31 and table_size == table_count * 4
    offsets = list(struct.unpack_from(f"<{table_count}I", raw, table_offset))
    assert len(offsets) == data_count + 1 and offsets[-1] == data_size
    next_section_offset = struct.unpack_from("<I", raw, 32)[0]
    assert next_section_offset == data_offset + data_size

    found = {}
    new_data = bytearray()
    new_offsets = []
    for index in range(data_count):
        start = offsets[index]
        end = offsets[index + 1]
        literal = raw[data_offset + start:data_offset + end]
        try:
            text = literal.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        new_offsets.append(len(new_data))
        if text in RUNTIME_TRANSLATIONS:
            assert text not in found, f"Duplicate runtime literal: {text!r}"
            new_text = RUNTIME_TRANSLATIONS[text]
            found[text] = index
            new_literal = new_text.encode("utf-8")
            report["runtime"].append({"index": index, "old": text, "new": new_text})
        else:
            new_literal = literal
        new_data.extend(new_literal)
    missing = set(RUNTIME_TRANSLATIONS) - set(found)
    assert not missing, f"Runtime translations not found: {sorted(missing)}"
    new_offsets.append(len(new_data))
    new_data_size = len(new_data)
    aligned_data_size = (new_data_size + 7) & ~7
    shift = aligned_data_size - data_size

    output = bytearray(raw[:data_offset])
    output.extend(new_data)
    output.extend(bytes(aligned_data_size - new_data_size))
    output.extend(raw[next_section_offset:])
    struct.pack_into(f"<{table_count}I", output, table_offset, *new_offsets)
    struct.pack_into("<I", output, 24, new_data_size)
    for section_index in range(2, section_count):
        header_offset = 8 + section_index * 12
        section_offset, section_size, section_count_value = struct.unpack_from("<3I", raw, header_offset)
        assert section_offset >= next_section_offset
        struct.pack_into("<3I", output, header_offset, section_offset + shift, section_size, section_count_value)
    assert len(output) == len(raw) + shift
    target.write_bytes(output)
    report["files"][relative.as_posix()] = {
        "source_bytes": len(raw), "patched_bytes": len(output),
        "old_literal_data_size": data_size, "new_literal_data_size": new_data_size,
        "section_shift": shift,
    }
    report["metadata"] = {"version": version, "literals": data_count, "translated": len(found)}
    print(f"Patched metadata: {len(output)} bytes, {len(found)} runtime strings", flush=True)


def main():
    assert ORIGINAL.is_dir() and FONT_PATH.is_file()
    if PATCHED.exists():
        shutil.rmtree(PATCHED)
    shutil.copytree(ORIGINAL, PATCHED)
    patch_assets()
    patch_metadata()
    (ANALYSIS / "patch_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    translations = {
        "static": STATIC_TRANSLATIONS,
        "native_text": NATIVE_TEXT_TRANSLATIONS,
        "runtime": RUNTIME_TRANSLATIONS,
    }
    (ANALYSIS / "translations.json").write_text(json.dumps(translations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Done: {len(report['static'])} TMP strings, {len(report['native_text'])} TextMesh strings, "
        f"{len(report['runtime'])} runtime strings",
        flush=True,
    )


if __name__ == "__main__":
    main()
