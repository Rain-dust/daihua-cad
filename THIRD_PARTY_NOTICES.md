# 第三方来源与许可证

Daihua CAD 是由 Rain-dust 集成维护的 CAD Agent 工具包，包含既有开源 MCP 与 CAD skills 的适配版本。新增集成代码按仓库根目录的 MIT 许可证发布；原有组件保留各自作者、版权与 MIT 许可。

| 组件 | 原作者与上游 | 集成基线 | 保留的许可 |
|---|---|---|---|
| CAD MCP | 曹瑞；[daobataotie/CAD-MCP](https://github.com/daobataotie/CAD-MCP) | `ef26482579424bb564b8b2ccc24f29f133f66fbf` | [MIT 原文](licenses/cad-mcp-MIT.txt)，Copyright (c) 2025 曹瑞 |
| cad-automation、cad-designer | Delancy；[delancy827/cad-skills](https://github.com/delancy827/cad-skills) | `6051169eb3cd39a6539d823261b8519f718828ed` | [MIT 原文](licenses/cad-skills-MIT.txt)，Copyright (c) 2026 Delancy |

## 集成修改

- MCP 源码随仓库分发，保留上游许可证；当前源来自已有的本地适配版本，并通过仓库提交记录维护后续修改。
- 两个 skill 保留上游作者信息、CAD 自动化/设计知识及可编辑 DXF 核验脚本；每个 skill 目录附带上游 MIT 许可证，便于单独安装时一同保留。
- 集成版将电脑专属安装路径、私人交付位置和背景偏好改为当前项目约定；移除未随包分发的资料链接、字节码缓存与历史电脑测试细节。
- 修订模型单位说明及原生半径/直径标注 API 示例，保留交付后的几何、图层、编辑语义和视觉核验要求。
- 机器可读来源、固定提交与组件路径见 [sources.json](sources.json)。这些修改不改变原作者的版权声明。

## 运行时依赖与参考资料

Python 依赖由安装器从包分发源安装，各依赖仍适用其自身许可证；本仓库不将这些依赖重新声明为本项目原创。skills 中提到的 pyautocad、ezdxf、CadQuery 等项目主要用于技术路线与 API 参考，具体安装范围以仓库依赖文件为准。

本仓库不包含 AutoCAD、浩辰 CAD、中望 CAD 的软件本体、激活信息或厂商字体。图纸规范名称、厂商及产品名称仅用于说明兼容环境和工程用法。
