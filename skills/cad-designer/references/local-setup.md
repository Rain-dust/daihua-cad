# Daihua CAD 环境与验证约定

仅在需要安装、查找解释器、连接 CAD 或排查环境问题时读取。正常任务先检查已装工具并复用，不重复安装；离线绘图不以连接 MCP 为前置条件。

本 skill 随 Daihua CAD 分发，上游作者 Delancy，集成维护 Rain-dust。路径由使用者决定，不依赖维护者电脑盘符。

## 环境选择

- 检查当前 Python 环境、已安装的 CAD skills、ezdxf 和现有脚本，再选择技术路线。仓库运行环境通常在 .venv：Windows 为 .venv/Scripts/python.exe，其他平台为 .venv/bin/python；也可使用已经具备所需能力的现有解释器。
- 新建的简单二维、规则几何或依据明确的图片重建，可直接使用 ezdxf 生成与解析真实 DXF 实体，无需先启动 CAD 或 MCP。
- 修改原图、处理特殊对象、DWG 保存/转换或需要原生出图时，选择能保留所需结构的可用 CAD API、脚本、转换工具或 MCP；必要时与离线生成组合。不能仅因 CAD 不可用就把客户要求的 DWG 静默替换为 DXF。
- AutoCAD/浩辰CAD/中望CAD 的直接控制需要 Windows、可用 CAD 软件及 COM 接口。直接 COM 连接时检测本机实际通用或版本化 ProgID，不照搬另一台电脑的版本号。

## 安装或协议排查

需要完整安装且尚未配置时，在仓库根目录运行 install.ps1，或 python scripts/install.py --client codex。客户端可选 codex、claude、cursor、generic；安装器创建仓库内 .venv 并按所选客户端注册 MCP，通用模式提供可合并配置。以当前仓库文档、安装器帮助与输出为准。

MCP 标识为 daihua-cad，入口 vendor/cad-mcp/src/server.py，使用 stdio。用 python scripts/install.py --check 查看安装状态；用仓库 .venv 的 Python 运行 scripts/verify_mcp.py 验证协议，仅在确实需要 CAD 连接时追加 --connect。连接验证可能启动 CAD；仅为生成离线 DXF 不运行此步骤。

## 有状态 CAD 执行

- 固定任务文档与修改范围；不清空、保存或关闭无关文档，不按自动文件名推断文档可丢弃。
- 核对单位、坐标和比例；沿用原图的单位与 UCS，不静默改为毫米或重设坐标系。
- 采用当前 CAD 版本可用的无交互 API 或已验证命令；忙碌或等待输入时检查实际状态后限时重试，不无限等待或无差别结束进程。
- 交付格式、路径、命名和图层服从当前任务；最终图纸与脚本、日志、备份、临时文件分开。
- 保存后回读关键几何、图层和实体类型，按任务需要视觉核对。工具返回 success、固定延时或文件存在都不能单独证明图纸正确。

上游来源、版本和许可证见 Daihua CAD 仓库 sources.json 与 THIRD_PARTY_NOTICES.md。
