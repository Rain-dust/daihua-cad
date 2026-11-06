# Daihua CAD：Agent 安装与维护入口

此仓库是面向客户接单、CAD 代画与修改的 Agent 工具包，打包 CAD skills、本机 CAD-MCP 与安装脚本。用户让你“安装代画匠 / 安装这个仓库”时，完成下面的流程，不要只给出操作建议。

## 安装流程

1. 阅读 `README.md`、`docs/INSTALL.md` 和安装器 `--help`。确认仓库完整；没有本地 checkout 时先克隆 `https://github.com/Rain-dust/daihua-cad.git`。
2. 检查操作系统、Python 版本与可执行路径。目标平台是 Windows，Python 3.11+，推荐 3.12。不要假定维护者的盘符、用户名、AutoCAD 版本或客户端配置在新机器上存在。
3. 从当前宿主和已有配置识别客户端：Codex → `codex`，Claude Code → `claude`，Cursor → `cursor`。确实无法判断时询问目标客户端；也可以在用户已同意通用配置时用 `generic`。不要同时改多个客户端来猜测。
4. 在仓库根目录运行 `python scripts/install.py --client <目标>`，或 PowerShell 包装器 `powershell -ExecutionPolicy Bypass -File .\install.ps1 -Client <目标>`。使用检查到的 Python 可执行文件，避免 Windows Store 占位程序。需要自定义路径时使用 `--config`、`--skills-dir`。
5. 完成 `python scripts/install.py --client <目标> --check` 和 `.\.venv\Scripts\python.exe scripts/verify_mcp.py`。默认协议检查不启动 CAD。不要把 `--skip-deps` 当成正式安装成功。
6. 如果用户要求验证本机 CAD 连接，运行 `.\.venv\Scripts\python.exe scripts/verify_mcp.py --connect`。它会尝试只读连接，必要时启动 CAD；不要为了验证连接创建、修改或保存用户图纸。
7. 汇报实际安装的配置路径、skills 路径、检查结果和客户端重启要求。检查失败时报告原始错误与下一步，不要声称完成了未执行的 CAD 验证。

用户的安装请求授权了上述常规本地安装、依赖下载、配置合并和检查。在授权范围内持续执行，不为每一步重复询问。遇到同名 skills 冲突、未知的用户定制或需要用户登录/授权 CAD 时，再针对具体障碍说明并询问。不要索取或替用户输入账号凭据。

## 保留用户环境

- 安装使用仓库内 `.venv`；不向全局 Python 无差别安装依赖。
- 用安装器合并 MCP 配置，不覆盖整个配置文件；不得删除其他 MCP 服务。
- 已有同名 skills 的内容与待安装版本冲突时停止处理该冲突，先比较内容。不要直接覆盖或删掉用户的本地版本。
- 安装器与客户端依赖这个仓库的绝对路径。移动仓库后重新安装并验证。
- 不修改无关图纸，不把安装变成 CAD 图纸整理任务。安装器不安装或激活 AutoCAD。
- 不使用远程 `curl | iex` 等直接执行网络脚本的方式。使用可检查的本地 checkout 和安装入口。
- 不把 `.venv/`、`.daihua/`、`output/`、账号凭据或私人图纸提交到仓库。

## CAD 任务与项目维护

客户代画任务先整理任务书、聊天记录、原图与截图，明确绘制范围、尺寸依据、修改内容和 DWG / PDF 交付要求。材料不足时区分可继续的工作与需要客户确认的关键缺口；不得编造尺寸或声称未完成的验收。实际绘图时阅读对应 `skills/cad-automation/SKILL.md` 和 `skills/cad-designer/SKILL.md`，仅按需读取其参考资料。先复用已知环境，结合精度、原图结构和实际交付格式选择 Python 程序化绘图、CAD API/脚本、MCP 或混合路线；不默认启动 AutoCAD 或调用 MCP，已有图纸局部修改不扩展为整图重绘。安装检查、协议检查、只读 CAD 连接和图纸几何验证是不同层级，分别报告。

维护源代码时保留上游许可、作者信息与 `THIRD_PARTY_NOTICES.md`。修改 vendored MCP 要更新 `vendor/cad-mcp/PATCHES.md` 中的补丁说明。例子只写入 `output/`，验证后不提交生成物。常规修改运行相关的安装器测试及 MCP 协议检查；涉及 CAD 行为时，在可用环境验证并明确版本与限制。
