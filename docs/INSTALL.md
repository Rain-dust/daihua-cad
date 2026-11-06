# 安装与卸载

代画匠是面向客户接单、代画与修改的 Agent 工具包，使用 Windows 本机 CAD 自动化环境。仓库本身不提供 AutoCAD 安装包或许可证。先安装 Git 和 Python 3.11+（推荐 3.12）；实际连接时另需已安装并激活的桌面 AutoCAD。

## 交给 Agent

> 请安装 https://github.com/Rain-dust/daihua-cad 。先克隆并阅读 AGENTS.md，检查当前环境和客户端，用对应安装入口完成配置及 check 验证，保留已有配置，不修改无关 CAD 图纸。

Agent 会识别当前客户端，使用本地仓库中的安装脚本，完成配置后报告结果。若客户端没有本机终端或文件修改能力，请按下面步骤手动安装。

## 手动安装

在 PowerShell 中执行：

```powershell
git clone https://github.com/Rain-dust/daihua-cad.git
cd daihua-cad
python --version
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Client codex
```

也可直接用 Python 入口：

```powershell
python scripts/install.py --client codex
```

若 `python` 指向 Windows Store 或错误版本，改用你的 Python 3.11+ 的绝对路径；通过 Python Launcher 安装的环境也可用 `py -3.12 scripts/install.py --client codex`。安装器建立仓库内 `.venv` 并安装依赖，需要联网访问 Python 包源。

`--client` 可选：

| 值 | 写入位置 |
| --- | --- |
| `codex` | `$CODEX_HOME/config.toml`，未设置时为 `~/.codex/config.toml`；skills 放在 `~/.agents/skills` |
| `claude` | `~/.claude.json`；skills 放在 `~/.claude/skills` |
| `cursor` | `~/.cursor/mcp.json`；skills 放在 `~/.cursor/skills` |
| `generic` | 生成仓库 `.daihua/mcp.json`，供你合并到支持 stdio 的客户端 |

`~` 表示运行安装器的当前用户主目录。安装器使用 MCP 服务名 `daihua-cad`。若使用自定义客户端配置或 skills 路径，后续检查、更新、卸载继续使用同一组参数。

## 安装器选项

准确参数以 `python scripts/install.py --help` 为准。

| 参数 | 用途 |
| --- | --- |
| `--client codex\|claude\|cursor\|generic` | 选择配置目标 |
| `--config PATH` | 指定 MCP 配置文件 |
| `--skills-dir PATH` | 指定 skills 安装目录 |
| `--dry-run` | 预览操作，不执行安装变更 |
| `--check` | 检查安装状态 |
| `--uninstall` | 卸载本安装器管理的配置与 skills |
| `--skip-deps` | 跳过依赖安装，仅供测试或已经自行准备依赖的环境 |

例如，先预览，再安装到自定义目标：

```powershell
python scripts/install.py --client codex --config "C:\Users\me\.codex\config.toml" --skills-dir "C:\Users\me\.agents\skills" --dry-run
python scripts/install.py --client codex --config "C:\Users\me\.codex\config.toml" --skills-dir "C:\Users\me\.agents\skills"
```

PowerShell 包装器使用 PascalCase 参数，例如 `-Client`、`-ConfigPath`、`-SkillsDir`、`-DryRun`、`-Check`、`-Uninstall`、`-SkipDeps`。若 Python 已安装但不在 PATH，使用 `-PythonPath` 指定解释器：

```powershell
.\install.ps1 -Client codex -PythonPath 'C:\Python312\python.exe'
```

复杂调用也可直接使用 Python 入口。

## 安装后验证

从仓库根目录执行：

```powershell
python scripts/install.py --client codex --check
.\.venv\Scripts\python.exe scripts/verify_mcp.py
```

前者检查安装配置和文件；后者通过本机 stdio 检查 MCP 协议及工具注册，不启动 CAD。检查通过后重启客户端，确认能够加载 `daihua-cad` 与两个 CAD skills。客户端可能要求对 MCP 服务进行一次本地启用或信任操作，按客户端界面提示处理。

如需进一步检查 AutoCAD 连接：

```powershell
.\.venv\Scripts\python.exe scripts/verify_mcp.py --connect
```

这是只读连接验证，可能启动 AutoCAD。确保 AutoCAD 已完成激活、首次启动设置，且没有模态对话框。成功连接不等于所有绘图功能与交付质量都已验证。

不启动 CAD 的离线示例：

```powershell
.\.venv\Scripts\python.exe examples/offline_plate.py
```

它生成一个示例 DXF 并执行审计，产物位于 `output/`。请在示例或用户授权的图纸上验证具体绘图任务。

## 同名冲突、更新与移动

已有未被本安装器管理的同名 skills 目录，或已安装文件出现本地修改时，安装器会停止。安装、升级或卸载发生普通文件操作错误时，会尝试恢复此前配置、skills 和归属清单，排除错误后可使用相同参数重试；若恢复本身失败，按错误提示保留仓库和备份。Windows 目录联接与符号链接不能替代本工具管理的 skills 目录。先比较差异：有用的本地修改应保留或合并，确认后再移走旧版本并重新安装。不要盲目删除自定义 skills。

更新前查看仓库改动，再拉取代码、重新运行相同安装命令并检查。移动或重命名仓库会影响 MCP 启动路径；移动后同样重新安装并检查。不要仅移动 `.venv` 期待旧环境继续可用。

## 卸载

使用原安装目标和自定义路径参数执行：

```powershell
python scripts/install.py --client codex --uninstall
```

卸载只处理本工具可确认归属的配置与 skills；无法安全判断或安装后已被修改的内容可能保留并提示处理。它不卸载 AutoCAD，不影响其他 MCP 服务。卸载后重启客户端。

仓库内的 Python 环境和输出文件可在确认不再需要后随仓库一起自行删除。先完成客户端配置卸载，再删除仓库，避免保留失效启动路径。
