# 故障排查

从仓库根目录运行命令。报告问题时附 Windows、Python、CAD、客户端版本与报错；不要上传账号凭据或私人图纸。

## 安装命令失败

**`python` 不存在、打开商店或版本太低**

安装 Python 3.11+（推荐 3.12），重新打开 PowerShell。使用 `python --version` 和 `Get-Command python` 检查实际程序；必要时用 Python 的绝对路径，或 `py -3.12 scripts/install.py --client codex`。若 Python 已安装但不在 PATH，可向 PowerShell 包装器显式传入路径：

```powershell
.\install.ps1 -Client codex -PythonPath 'C:\Python312\python.exe'
```

**PowerShell 不允许执行脚本**

可以对本次进程使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Client codex
```

也可以直接运行 `python scripts/install.py --client codex`。企业设备的策略由管理员管理，不需要为本项目永久更改机器策略。

**下载依赖超时、证书错误或代理问题**

检查当前终端的网络、代理和 Python 包源配置，修复后重跑相同安装命令。不要用 `--skip-deps` 掩盖下载失败；该选项不代表环境已经具备运行所需依赖。若 `.venv` 已损坏，在确认其确为本仓库隔离环境后重建，再运行安装器。

**同名 skills 冲突**

安装器会停止，防止覆盖已有版本。比较已安装目录与仓库 `skills/` 的差异，保留有价值的本地修改后再迁移或合并。卸载也不会为了成功而删除无法确认归属的用户文件。

## 客户端看不到 MCP 或 skills

先运行：

```powershell
python scripts/install.py --client codex --check
.\.venv\Scripts\python.exe scripts/verify_mcp.py
```

把 `codex` 换成实际目标；安装时传入过 `--config` 或 `--skills-dir`，检查时也传入相同参数。然后重启客户端，确认其加载的是该用户、该配置文件及该 skills 目录。客户端自己的服务启用或信任提示也需要完成。

- 服务名应为 `daihua-cad`，由本地 stdio 启动。
- 保持仓库路径不变；移动后重新安装，修复绝对启动路径。
- 不要让客户端使用另一个全局 Python 代替仓库 `.venv`。
- `generic` 只生成 `.daihua/mcp.json`，需要自行合并到实际客户端，它不会替任意客户端完成注册。

若 MCP 协议检查成功、客户端仍无法连接，查看客户端的 MCP 日志和最终启动命令。仅复制与问题相关的输出。

## AutoCAD 连接失败

默认协议检查不会连接 CAD。确认需要验证连接后，再执行：

```powershell
.\.venv\Scripts\python.exe scripts/verify_mcp.py --connect
```

先手动打开并完成 AutoCAD 的激活、首次启动设置，关闭模态弹窗，等待命令行空闲。Agent、Python 和 AutoCAD 应在同一 Windows 用户会话中运行；不同的提权级别可能妨碍 COM 访问。请使用正常桌面会话。

“无效的类字符串 / Class not registered”通常表示对应 COM 程序未安装或未正确注册。确认安装的是支持自动化的桌面版 AutoCAD。不要直接把某个维护者机器的固定版本号复制到新环境；让 Agent 检查实际安装。

AutoCAD LT 不保证可用；中望、浩辰等其他产品的支持源于上游，本项目尚未实测。协议检查成功只能说明 MCP 可以启动，不能证明 CAD COM 接口可用。

## 指定 CAD 类型、版本与输出目录

可在客户端的 `daihua-cad` MCP 服务环境变量（`env`）中设置：

| 变量 | 用途 |
| --- | --- |
| `DAIHUA_CAD_PROGID` | 显式指定已注册的 CAD COM ProgID；未设置时自动发现可用 AutoCAD 版本 |
| `DAIHUA_CAD_TYPE` | 覆盖上游配置中的 CAD 类型；其他产品仍需实际测试 |
| `DAIHUA_OUTPUT_DIR` | 设置有写入权限的输出目录 |

修改后重启 MCP 服务。保持 `command`、`args` 和 `cwd` 指向安装器创建的环境；不要把私有路径写回开源默认配置。手动加入 `env` 会使配置区别于安装器记录，后续 `--check` 会提示差异，重装可能停止以保护这些自定义项，卸载也会保留已修改的 MCP 条目。

## 没有 AutoCAD

可以阅读和使用 skills 的离线 DXF 路线，运行：

```powershell
.\.venv\Scripts\python.exe examples/offline_plate.py
```

结果写入 `output/`。离线 DXF 审计成功不代表 DWG 输出、CAD 软件显示、打印与标注效果已经验证。

## 卸载后还有文件

用与安装时相同的客户端和自定义路径运行 `--uninstall`，阅读保留项提示。安装器会保留无法确认归属或已修改的内容，先比较再手动处理。仓库、`.venv` 和 `output/` 的保留不代表客户端仍启用了 MCP。

提交 issue 时，提供最小复现命令、检查结果和去掉私人路径或内容的日志；如果涉及图纸，仅提供你有权公开的最小示例。
