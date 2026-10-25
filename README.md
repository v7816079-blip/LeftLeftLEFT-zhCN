# Left! Left! LEFT! Playtest 简体中文汉化包

适用于 Steam 上的 **Left! Left! LEFT! Playtest**（AppID：`5425110`）。本补丁将游戏界面、联机提示和驾驶说明翻译为简体中文，并加入中文动态回退字体。

> 非官方、由玩家制作的汉化项目。适配版本于 2026-10-25 验证；Steam 更新后请勿直接沿用旧补丁。

## 汉化内容

- 主菜单、选关、邀请、设置、暂停与重开界面
- 起点／终点标记
- Steam／局域网联机状态与提示
- 准备、完成、试玩声明和驾驶操作说明
- 动态车组信息、驾驶员／领航员身份和空位提示
- 中文动态回退字体，保留原英文美术字体

当前版本包含 **135 处 TMP 界面对象、6 处 TextMesh 场景标记、45 条运行时文本**的修改。

## 直接安装（推荐）

1. 在仓库的 **Releases** 页面下载最新 `LeftLeftLEFT_zhCN_*.zip`。
2. 完全退出游戏。
3. 将压缩包中的**全部内容**解压到游戏根目录，即 `LeftLeftLEFT.exe` 所在目录。
4. 双击 `install_zhCN.bat`，看到安装完成提示后启动游戏。

也可以不复制到游戏目录，直接在汉化包所在目录运行：

```bat
install_zhCN.bat "D:\Program Files (x86)\Steam\steamapps\common\Left! Left! LEFT! Playtest"
```

如果你的 Steam 库在其他位置，请把参数替换为实际游戏目录。

## 卸载

运行 `uninstall_zhCN.bat`。如果脚本不在游戏根目录，把游戏目录作为参数传入：

```bat
uninstall_zhCN.bat "D:\你的 Steam 库\steamapps\common\Left! Left! LEFT! Playtest"
```

卸载脚本会恢复 `_LeftLeftLEFT_zhCN_Backup` 中备份的 6 个原始文件，不删除存档或备份目录。

## 注意事项

- 安装器首次运行时会先备份，再覆盖资源；重复安装不会覆盖原始备份。
- 安装包只包含补丁资源与脚本，不包含游戏可执行程序。
- Steam 更新或“验证游戏文件完整性”可能覆盖汉化。
- **安装器不会判断游戏版本。** 更新后请不要继续使用旧汉化包，以免资源版本不匹配。
- 联机标识、网络键名、快捷键、`{0}` 占位符和富文本标签保持原样。
- 本项目与游戏开发者或发行商没有隶属关系。

## 验证范围

- 补丁构建后逐对象反向校验，确认只有预期的 6 个资源文件发生变化。
- 中文字体覆盖当前翻译使用的全部 214 个非 ASCII 字符。
- 安装 → 卸载 → 再次安装测试通过；卸载后 6 个文件逐字节还原，原始备份保持不变。
- 已实际启动游戏并检查主菜单与设置页，中文无方框；Steam 初始化及大厅创建成功。
- 尚未进行双客户端联机互测，也未逐页检查全部关卡。
- 退出测试时记录到一次 `FacepunchTransport` 空引用日志；尚未做原版对照，原因未确认。

## 从源码构建

仅供希望审查、修改或复现补丁的用户。普通玩家直接下载 Release 即可。

### 环境

- Windows
- Python 3.10+
- 当前 Playtest 游戏文件
- 合法可用的黑体字体文件 `simhei.ttf`

安装依赖：

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

### 准备文件

1. 将游戏根目录内容复制到 `work\original`。至少应保留 `LeftLeftLEFT.exe`、`LeftLeftLEFT_Data` 及其原始结构。
2. 将本机合法可用的 `simhei.ttf` 复制为 `work\simhei.ttf`。
3. 不要提交 `work` 目录；其中可能包含完整游戏文件和个人数据。

### 构建与测试

在仓库根目录依次执行：

```bat
.venv\Scripts\python extract_raw.py
.venv\Scripts\python make_patch.py
.venv\Scripts\python verify_patch.py
.venv\Scripts\python build_delivery.py
.venv\Scripts\python test_installer.py
```

输出位于 `deliverables\LeftLeftLEFT_zhCN` 和 `deliverables\LeftLeftLEFT_汉化包.zip`。

构建脚本针对当前资源布局做了严格断言。如果游戏更新导致对象、元数据或字体布局变化，脚本会停止，需要重新分析和适配。

## 翻译与贡献

翻译对照位于 [`translations/LeftLeftLEFT_zhCN.csv`](translations/LeftLeftLEFT_zhCN.csv)，规范译文的构建源为 [`make_patch.py`](make_patch.py)。

欢迎通过 Issue 或 Pull Request 改进翻译、兼容性和说明文档。提交前请运行构建校验；不要上传原版游戏目录、个人备份、测试截图或含 Steam ID 等个人信息的日志。

## 开源许可

自制脚本与翻译采用 [MIT License](LICENSE)。游戏原始资源、黑体字体及其他第三方内容不在 MIT 授权范围内，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
