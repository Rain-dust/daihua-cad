# Daihua CAD 环境与验证约定

仅在需要定位运行环境或接入 CAD/MCP 时查阅，不作为每个绘图任务的必读步骤。

本 skill 随 Daihua CAD 分发；上游作者 Delancy，集成维护 Rain-dust。安装路径由使用者决定，不依赖任何维护者电脑上的盘符。

## 安装与环境

- 在仓库根目录运行 `install.ps1`，或 `python scripts/install.py --client codex`；客户端可选 `codex`、`claude`、`cursor`、`generic`。安装器创建仓库内 `.venv`，按所选客户端注册 MCP；通用模式提供可合并的配置。
- MCP 标识为 `daihua-cad`，入口为 `vendor/cad-mcp/src/server.py`，使用 stdio。Windows Python 位于 `.venv/Scripts/python.exe`，其他平台为 `.venv/bin/python`；实际以安装器输出和客户端配置为准。
- AutoCAD/浩辰CAD/中望CAD 的直接控制需要 Windows、可用的 CAD 软件及 COM 接口；CAD 软件与授权由使用者自行安装。离线 DXF 可用 `ezdxf`，不要求安装 CAD。
- 用 `python scripts/install.py --check` 查看安装状态；用 `.venv` 中的 Python 运行 `scripts/verify_mcp.py` 验证 MCP 协议，追加 `--connect` 进行只读 CAD 连接验证。连接可能启动 CAD，但不应修改图纸。

## 执行绘图

- 先按主 skill 的任务与交付格式选择路线：简单二维可直接使用已装 Python/ezdxf；需要原生 CAD 时才选择已配置的 `daihua-cad` MCP、COM 或脚本。直接 COM 检测目标 CAD 与实际 ProgID，不照搬其他电脑版本号或随意切换产品。连接失败时先诊断；仅在客户允许 DXF 时采用该交付，必需 DWG 不得静默降级。
- 新任务先新建图纸或明确目标文档；不清空、保存、关闭无关文档，不按自动文件名推断文档可以丢弃。
- 先核对项目单位、坐标系和比例；模型按实际单位 1:1 绘制，既有图纸的单位不能静默改成毫米。
- 交付路径、文件格式、命名和图层遵循当前项目要求；未指定时，将最终图纸与脚本、日志、临时文件分别存放。
- 根据 CAD 版本选择无交互 API 或已验证的命令序列。遇到等待输入或忙碌状态时限时重试，记录失败点；避免无限等待和无差别结束 CAD 进程。
- 保存后回读文件，核对关键尺寸、图层与实体类型，并按任务需要做视觉检查；工具返回 success 不代表图纸正确。

上游仓库、版本和许可证记录于 Daihua CAD 仓库的 `sources.json` 与 `THIRD_PARTY_NOTICES.md`。
