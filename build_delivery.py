import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from make_patch import (
    DATA_NAME,
    NATIVE_TEXT_TRANSLATIONS,
    PATCHED,
    RUNTIME_TRANSLATIONS,
    STATIC_TRANSLATIONS,
)

BASE = Path(__file__).parent
DELIVERABLES = BASE / "deliverables"
PACKAGE = DELIVERABLES / "LeftLeftLEFT_zhCN"
ZIP_PATH = DELIVERABLES / "LeftLeftLEFT_汉化包.zip"
ANALYSIS = BASE / "work" / "analysis"
CHANGED_FILES = [
    f"{DATA_NAME}/level0",
    f"{DATA_NAME}/level1",
    f"{DATA_NAME}/level2",
    f"{DATA_NAME}/level3",
    f"{DATA_NAME}/resources.assets",
    f"{DATA_NAME}/il2cpp_data/Metadata/global-metadata.dat",
]

INSTALL_BAT = r"""@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
if "%~1"=="" (set "GAME_DIR=%~dp0") else (set "GAME_DIR=%~1")
set "BACKUP_DIR=%GAME_DIR%\_LeftLeftLEFT_zhCN_Backup"
set "FILES=LeftLeftLEFT_Data\level0 LeftLeftLEFT_Data\level1 LeftLeftLEFT_Data\level2 LeftLeftLEFT_Data\level3 LeftLeftLEFT_Data\resources.assets LeftLeftLEFT_Data\il2cpp_data\Metadata\global-metadata.dat"

if not exist "%GAME_DIR%\LeftLeftLEFT.exe" (
    echo [错误] 未找到 LeftLeftLEFT.exe。
    echo 请把汉化包内容解压到游戏根目录，或把游戏目录作为本脚本参数。
    exit /b 1
)
tasklist /FI "IMAGENAME eq LeftLeftLEFT.exe" /NH | find /I "LeftLeftLEFT.exe" >nul
if not errorlevel 1 (
    echo [错误] 游戏正在运行，请先退出游戏再安装。
    exit /b 1
)
for %%F in (%FILES%) do (
    if not exist "%~dp0%%F" (
        echo [错误] 汉化包缺少文件：%%F
        exit /b 1
    )
    if not exist "%GAME_DIR%\%%F" (
        echo [错误] 游戏缺少文件：%%F
        exit /b 1
    )
)

if not exist "%BACKUP_DIR%\backup.complete" (
    echo 正在备份原始文件……
    if not exist "%BACKUP_DIR%\LeftLeftLEFT_Data\il2cpp_data\Metadata" (
        mkdir "%BACKUP_DIR%\LeftLeftLEFT_Data\il2cpp_data\Metadata" >nul
    )
    for %%F in (%FILES%) do (
        copy /b /y "%GAME_DIR%\%%F" "%BACKUP_DIR%\%%F" >nul
        if errorlevel 1 (
            echo [错误] 备份失败：%%F。尚未修改游戏文件。
            exit /b 1
        )
    )
    echo Original files for Simplified Chinese patch> "%BACKUP_DIR%\backup.complete"
) else (
    echo 已存在原始备份，不会覆盖。
)

for %%F in (%FILES%) do (
    copy /b /y "%~dp0%%F" "%GAME_DIR%\%%F" >nul
    if errorlevel 1 (
        echo [错误] 安装失败：%%F。可运行 uninstall_zhCN.bat 还原。
        exit /b 1
    )
)
echo.
echo 简体中文汉化安装完成。原始备份位于：%BACKUP_DIR%
echo 如需还原，请运行 uninstall_zhCN.bat。
exit /b 0
"""

UNINSTALL_BAT = r"""@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
if "%~1"=="" (set "GAME_DIR=%~dp0") else (set "GAME_DIR=%~1")
set "BACKUP_DIR=%GAME_DIR%\_LeftLeftLEFT_zhCN_Backup"
set "FILES=LeftLeftLEFT_Data\level0 LeftLeftLEFT_Data\level1 LeftLeftLEFT_Data\level2 LeftLeftLEFT_Data\level3 LeftLeftLEFT_Data\resources.assets LeftLeftLEFT_Data\il2cpp_data\Metadata\global-metadata.dat"

if not exist "%GAME_DIR%\LeftLeftLEFT.exe" (
    echo [错误] 未找到 LeftLeftLEFT.exe。
    exit /b 1
)
tasklist /FI "IMAGENAME eq LeftLeftLEFT.exe" /NH | find /I "LeftLeftLEFT.exe" >nul
if not errorlevel 1 (
    echo [错误] 游戏正在运行，请先退出游戏再还原。
    exit /b 1
)
if not exist "%BACKUP_DIR%\backup.complete" (
    echo [错误] 未找到完整原始备份：%BACKUP_DIR%
    exit /b 1
)
for %%F in (%FILES%) do (
    if not exist "%BACKUP_DIR%\%%F" (
        echo [错误] 备份缺少文件：%%F，已停止还原。
        exit /b 1
    )
)
for %%F in (%FILES%) do (
    copy /b /y "%BACKUP_DIR%\%%F" "%GAME_DIR%\%%F" >nul
    if errorlevel 1 (
        echo [错误] 还原失败：%%F
        exit /b 1
    )
)
echo.
echo 已还原原始英文文件。备份仍保留在：%BACKUP_DIR%
exit /b 0
"""

README = r"""Left! Left! LEFT! Playtest 简体中文汉化包
==================================================
适用游戏：Left! Left! LEFT! Playtest（Steam AppID 5425110）
制作日期：2026-10-25

汉化内容
- 主菜单、选关、邀请、设置、暂停与重开界面
- 起点／终点标记
- Steam／局域网联机状态与提示
- 准备、完成、试玩声明和驾驶操作说明
- 内嵌 SimHei（黑体）作为中文动态回退字体，保留原英文美术字体

安装方法
1. 退出游戏。
2. 将本压缩包中的全部内容解压到游戏根目录，也就是 LeftLeftLEFT.exe 所在目录。
3. 双击 install_zhCN.bat。
4. 安装完成后启动游戏。

也可以在本文件所在目录打开命令行，执行：
install_zhCN.bat "D:\Program Files (x86)\Steam\steamapps\common\Left! Left! LEFT! Playtest"

卸载方法
运行 uninstall_zhCN.bat；如果脚本不在游戏根目录，也把游戏目录作为参数传入。
脚本会恢复安装前备份的 6 个原始文件，不会删除存档或备份目录。

备份位置
游戏根目录\_LeftLeftLEFT_zhCN_Backup
安装器只有在完整备份成功后才会修改游戏文件；重复安装不会覆盖原始备份。

注意事项
- 本补丁仅对应当前 Playtest 版本。Steam 更新或验证游戏文件可能会覆盖汉化。
- 更新后请勿直接沿用旧补丁，以免版本不匹配。
- 联机标识、网络键名、快捷键、{0} 占位符和富文本标签均保持原样。
- 汉化只修改本地文本与字体资源，不修改可执行程序。
"""


def write_crlf(path, text):
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    verification = json.loads((ANALYSIS / "verification.json").read_text(encoding="utf-8"))
    assert verification["checks"]["status"] == "passed"
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)
    for relative in CHANGED_FILES:
        target = PACKAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PATCHED / relative, target)
    write_crlf(PACKAGE / "install_zhCN.bat", INSTALL_BAT)
    write_crlf(PACKAGE / "uninstall_zhCN.bat", UNINSTALL_BAT)
    write_crlf(PACKAGE / "使用说明.txt", README)
    shutil.copy2(BASE / "LICENSE", PACKAGE / "LICENSE")
    shutil.copy2(BASE / "THIRD_PARTY_NOTICES.md", PACKAGE / "THIRD_PARTY_NOTICES.md")
    shutil.copy2(ANALYSIS / "verification.json", PACKAGE / "补丁校验.json")
    with (PACKAGE / "翻译对照.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["位置", "英文原文", "简体中文"])
        for category, mapping in (
            ("界面", STATIC_TRANSLATIONS),
            ("场景标记", NATIVE_TEXT_TRANSLATIONS),
            ("运行时提示", RUNTIME_TRANSLATIONS),
        ):
            for old, new in mapping.items():
                writer.writerow([category, old, new])
    manifest = {
        "game": "Left! Left! LEFT! Playtest",
        "app_id": 5425110,
        "locale": "zh-CN",
        "built_at": "2026-10-25",
        "backup_directory": "_LeftLeftLEFT_zhCN_Backup",
        "files": {},
    }
    for relative in CHANGED_FILES:
        path = PACKAGE / relative
        manifest["files"][relative] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (PACKAGE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE).as_posix())
    with zipfile.ZipFile(ZIP_PATH) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == 14
    print(f"Package: {PACKAGE}")
    print(f"ZIP: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes)")
    print(f"ZIP SHA256: {sha256(ZIP_PATH)}")


if __name__ == "__main__":
    main()
