# 代画匠 · Daihua CAD

**面向 CAD 接单代画，把客户需求交给 Agent，完成绘图、修改和 DWG / PDF 交付。**

代画匠（Daihua CAD）是面向客户项目的 Agent 工具包，把两套 CAD skills、本机 [CAD-MCP](https://github.com/daobataotie/CAD-MCP) 和一键配置打包在同一个仓库，帮助你的 Agent 完成代画工作流：理解需求、绘制修改、检查图层标注、交付 DWG / PDF。

你负责客户沟通与任务判断，Agent 在本机工具环境中执行已授权的绘图工作。本项目提供技能与工具，不包含订单平台、客户管理或支付系统。

[English](README.en.md) · [安装说明](docs/INSTALL.md) · [故障排查](docs/TROUBLESHOOTING.md) · [Agent 执行入口](AGENTS.md)

## 让 Agent 一句话安装

把下面这句话交给你正在使用的 Agent：

> 请帮我安装 https://github.com/Rain-dust/daihua-cad 。先克隆仓库并阅读 AGENTS.md，检查 Windows、Python 和当前客户端环境，再按当前客户端运行安装器并完成 check 验证；保留已有配置，不修改无关 CAD 图纸。

安装器支持 Codex、Claude Code、Cursor，也可只生成通用 MCP 配置。Agent 能操作本机终端并修改客户端配置时，可直接完成安装；客户端重启后加载新配置。

## 手动快速开始

准备 Windows、Git 和 Python 3.11+（推荐 3.12）。连接 CAD 时，需要自行安装并激活桌面版 AutoCAD。

```powershell
git clone https://github.com/Rain-dust/daihua-cad.git
cd daihua-cad
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Client codex
python scripts/install.py --client codex --check
```

将 `codex` 换成 `claude`、`cursor` 或 `generic` 可切换目标。也可以直接运行：

```powershell
python scripts/install.py --client codex
```

安装需要联网下载 Python 依赖。脚本在仓库创建 `.venv`，复制 skills，并登记本机 stdio MCP 服务 `daihua-cad`。保留此仓库及其路径，客户端会从这里启动 MCP。

## 从客户需求到图纸交付

| 环节 | Agent 的工作 |
| --- | --- |
| 收需求 | 整理任务书、聊天要求与交付格式，识别影响绘制的缺失信息 |
| 理解原图 | 结合原始 CAD、截图和尺寸说明，确认绘制范围与修改内容 |
| 绘制修改 | 按任务选择本机 CAD 自动化或离线 DXF 路线 |
| 图纸验收 | 检查关键几何、图层、标注和可编辑性 |
| 客户交付 | 按约定整理 DWG / PDF，并报告实际验证结果 |

具体能力取决于 Agent 客户端、可用 CAD 软件与输入材料。正式交付前仍需按项目要求复核。

## 装进去的是什么

| 组件 | 用途 |
| --- | --- |
| `cad-automation` skill | 绘图自动化、COM / AutoLISP、离线 DXF 等方法与参考资料 |
| `cad-designer` skill | 设计、图层、标注与交付检查的指导 |
| `vendor/cad-mcp` | 基于上游 CAD-MCP 的本机 CAD 工具接口 |
| 安装器与便携补丁 | 建立隔离 Python 环境、适配路径、合并客户端配置、检查与卸载 |

Skills 是给 Agent 的工作说明和知识资料；MCP 提供调用 CAD 的工具。实际绘图仍由 Agent 根据你的任务选择路线并检查结果。

本仓库不安装或授权 AutoCAD；本机 MCP 不要求 OpenAI API key。你使用的 Agent 客户端可能有自己的账号和模型要求。

## 支持与验证边界

- 主目标：Windows + 已安装、已激活的桌面版 AutoCAD；Python 3.11+，推荐 3.12。
- 本项目的技术工作流曾在 AutoCAD 2026 使用；当前包的安装、协议检查和实际 CAD 连接是不同层级的验证。
- 默认协议检查不会启动 CAD。显式添加 `--connect` 才尝试只读连接，必要时会启动 AutoCAD。
- 不承诺 AutoCAD LT 兼容。中望、浩辰等来自上游的兼容能力尚未在本项目实测。
- 没有 AutoCAD 时可使用 skills 中的离线 DXF 路线；这不等于获得 DWG / COM 功能。

```powershell
.\.venv\Scripts\python.exe scripts/verify_mcp.py
.\.venv\Scripts\python.exe scripts/verify_mcp.py --connect
.\.venv\Scripts\python.exe examples/offline_plate.py
```

最后一条生成并审计一个离线 DXF 示例，结果放在 `output/`。安装检查通过代表配置和依赖检查通过，不代表所有 CAD 操作或图纸质量已通过验证。

实测与限制见[验证记录](docs/VALIDATION.md)；再次审查发现与修复的问题见[审查记录](docs/REVIEW.md)。

## 配置位置

| 客户端 | MCP 配置 | skills 默认目录 |
| --- | --- | --- |
| Codex | `$CODEX_HOME/config.toml` 或 `~/.codex/config.toml` | `~/.agents/skills` |
| Claude Code | `~/.claude.json` | `~/.claude/skills` |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/skills` |
| Generic | 仓库 `.daihua/mcp.json` | 不自动关联客户端 |

可用 `--config`、`--skills-dir` 指定位置。已有同名 skills 冲突时安装器会停止，请先比较内容并处理冲突。更多选项与卸载步骤见[安装说明](docs/INSTALL.md)。

## 开源与归属

本仓库以 MIT 许可分发本项目的集成代码与可按该许可分发的内容。CAD-MCP 上游为 [daobataotie/CAD-MCP](https://github.com/daobataotie/CAD-MCP)，vendored 源码保留其许可；skills 保留来源与作者信息。代画匠负责整理、便携化与安装体验，不将上游 MCP 或既有 skills 宣称为全部原创。

使用、再分发或贡献前，请阅读 [LICENSE](LICENSE) 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。第三方 CAD 软件、Python 依赖及其他被引用项目按各自许可使用。
