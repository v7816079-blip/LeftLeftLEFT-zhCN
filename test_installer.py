import filecmp
import json
import shutil
import subprocess
from pathlib import Path

from build_delivery import CHANGED_FILES, PACKAGE
from make_patch import ORIGINAL, PATCHED

BASE = Path(__file__).parent
TEST_GAME = BASE / "work" / "installer_test"
LOG_DIR = BASE / "work" / "analysis"


def run_batch(script, label):
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", str(PACKAGE / script), str(TEST_GAME)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=120,
    )
    (LOG_DIR / f"installer_{label}.log").write_bytes(result.stdout)
    assert result.returncode == 0, f"{script} failed with {result.returncode}; see installer_{label}.log"


def compare_tree(root, reference):
    for relative in CHANGED_FILES:
        assert filecmp.cmp(root / relative, reference / relative, shallow=False), (
            f"Mismatch for {relative}: {root} does not match {reference}"
        )


def main():
    if TEST_GAME.exists():
        shutil.rmtree(TEST_GAME)
    TEST_GAME.mkdir(parents=True)
    shutil.copy2(ORIGINAL / "LeftLeftLEFT.exe", TEST_GAME / "LeftLeftLEFT.exe")
    for relative in CHANGED_FILES:
        target = TEST_GAME / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ORIGINAL / relative, target)
    run_batch("install_zhCN.bat", "install")
    compare_tree(TEST_GAME, PATCHED)
    compare_tree(TEST_GAME / "_LeftLeftLEFT_zhCN_Backup", ORIGINAL)
    assert (TEST_GAME / "_LeftLeftLEFT_zhCN_Backup" / "backup.complete").is_file()
    run_batch("uninstall_zhCN.bat", "uninstall")
    compare_tree(TEST_GAME, ORIGINAL)
    run_batch("install_zhCN.bat", "reinstall")
    compare_tree(TEST_GAME, PATCHED)
    compare_tree(TEST_GAME / "_LeftLeftLEFT_zhCN_Backup", ORIGINAL)
    result = {
        "status": "passed",
        "install": "patched files match; backup matches original",
        "uninstall": "all six files restored byte-for-byte",
        "reinstall": "patched files match; original backup preserved",
    }
    (LOG_DIR / "installer_test.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(TEST_GAME)
    print("Installer test passed: install, uninstall, reinstall, and backup preservation")


if __name__ == "__main__":
    main()
