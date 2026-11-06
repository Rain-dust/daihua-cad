# Daihua CAD v0.1.0 验证记录

日期：2026-11-06。验证环境：Windows、Python 3.12、AutoCAD 2026。

- 在新的仓库内 `.venv` 中从 Python 包源安装依赖，使用隔离的客户端配置和 skills 目录完成安装，`--check` 通过。
- stdio MCP 初始化、工具发现通过，共 35 个工具；`--connect` 只读图层查询通过。
- 24 项测试通过，覆盖配置合并、幂等、冲突保护、卸载保留用户修改、目录链接保护、AutoCAD ProgID 排序及离线 DXF 生成与回读。
- 两套 skills 的 `quick_validate.py` 通过；相对引用与第三方 MIT 许可检查通过。
- PowerShell 5.1 的实际 `-DryRun` 通过，包含带空格、中文和特殊字符的路径。

这些检查验证首版的安装、协议和连接路径。未逐项测试全部 MCP 绘图命令；中望、浩辰及 AutoCAD LT 尚未在本项目实测。GitHub Actions 配置额外覆盖 Windows/Linux 与 Python 3.11/3.12；运行结果以 Actions 页面为准。

## v0.1.2 补充验证

- 修正 Windows 短路径与完整路径的测试比较；MCP 验证控制台输出采用 ASCII JSON，UTF-8 报告文件保留中文。
- 直接 Python 安装入口对宿主编码无法表示的字符作转义容错；新增 cp1252 子进程回归，验证中文和 emoji 路径的 dry-run 不写入文件。
- 本地测试增至 25 项并全部通过；Windows/Linux 与 Python 3.11/3.12 的自动检查见 GitHub Actions。
