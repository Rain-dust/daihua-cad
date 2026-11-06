# Daihua CAD · 代画匠

**Give your agent a client brief and work through CAD drafting, revisions, and DWG / PDF delivery.**

Daihua CAD is an agent toolkit for client drafting projects. It bundles two CAD skills, local [CAD-MCP](https://github.com/daobataotie/CAD-MCP), portability patches, and an installer so your agent can work through requirements, drafting, layer and dimension checks, and DWG / PDF delivery.

You manage the client relationship and decide the scope; the agent executes authorized drawing work with local tools. This repository is a skills and tools package. It does not include an order marketplace, CRM, or payment system.

[中文](README.md) · [Installation guide](docs/INSTALL.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Agent instructions](AGENTS.md)

## Ask your agent to install it

> Install https://github.com/Rain-dust/daihua-cad for me. Clone the repository and read AGENTS.md first. Check Windows, Python, and the current client, then run the appropriate installer and check its result. Preserve existing configuration and do not modify unrelated CAD drawings.

The agent needs terminal and local configuration access. Supported configuration targets are Codex, Claude Code, Cursor, and a generic MCP snippet. Restart the client after installation to load the server and skills.

## Quick start

Use Windows, Git, and Python 3.11+ (3.12 recommended). CAD connection requires an independently installed and activated desktop AutoCAD.

```powershell
git clone https://github.com/Rain-dust/daihua-cad.git
cd daihua-cad
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Client codex
python scripts/install.py --client codex --check
```

Replace `codex` with `claude`, `cursor`, or `generic`. The Python entry point is equivalent:

```powershell
python scripts/install.py --client codex
```

Installation downloads Python dependencies, creates a repository-local `.venv`, copies the skills, and registers the local stdio server as `daihua-cad`. Keep the repository at its installed path: the client launches the MCP server from it.

## From client brief to drawing delivery

| Stage | Agent workflow |
| --- | --- |
| Requirements | Consolidate task briefs, messages, delivery formats, and missing inputs |
| Source review | Read source CAD, screenshots, and dimensions to establish scope |
| Drafting and revisions | Choose batch Python geometry, native CAD, or a mixed workflow |
| Drawing checks | Review key geometry, layers, dimensions, and editability |
| Delivery | Prepare agreed DWG / PDF files and report what was verified |

For simple 2D geometry and image reconstruction with reliable dimensions, the skills first consider installed Python/ezdxf tools. Existing DWG revisions, special objects, native plotting, and format conversion use suitable CAD APIs, scripts, or MCP when needed. Accuracy, preservation of the source drawing, and the agreed formats take priority; AutoCAD startup and per-entity MCP calls are not default steps. Detailed skill references are loaded only for the chosen task.

Actual capabilities depend on the agent client, available CAD software, and source material. Review deliverables against the project requirements before sending them to a client.

## Included components

| Component | Purpose |
| --- | --- |
| `cad-automation` | Automation methods, COM / AutoLISP guidance, offline DXF, and reference material |
| `cad-designer` | Design, layers, dimensions, and delivery checks |
| `vendor/cad-mcp` | Local CAD tools based on upstream CAD-MCP |
| Installer and portability patches | Python environment, portable paths, client configuration, checks, and uninstall |

Skills guide the agent; MCP exposes tools it can call. The agent still needs to choose the right workflow and validate each drawing.

Daihua does not install or license AutoCAD. The local MCP server does not require an OpenAI API key. Your agent client may require its own account or model access.

## Compatibility and verification

The primary target is Windows with an activated desktop AutoCAD and Python 3.11+ (3.12 recommended). The underlying workflow has previously been used with AutoCAD 2026. Installer checks, MCP protocol checks, and a live CAD connection are separate verification stages.

AutoCAD LT is not guaranteed. Other CAD products supported upstream have not been tested in this project. Offline DXF creation can be used without AutoCAD; it does not provide DWG / COM functionality.

```powershell
.\.venv\Scripts\python.exe scripts/verify_mcp.py
.\.venv\Scripts\python.exe scripts/verify_mcp.py --connect
.\.venv\Scripts\python.exe examples/offline_plate.py
```

The default protocol check does not start CAD. `--connect` attempts a read-only connection and may start AutoCAD. The offline example writes and audits a DXF under `output/`. A successful installation check does not certify every CAD operation or drawing.

## Configuration targets

| Client | MCP configuration | Default skills directory |
| --- | --- | --- |
| Codex | `$CODEX_HOME/config.toml` or `~/.codex/config.toml` | `~/.agents/skills` |
| Claude Code | `~/.claude.json` | `~/.claude/skills` |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/skills` |
| Generic | Repository `.daihua/mcp.json` | No automatic client association |

Override destinations with `--config` and `--skills-dir`. Installation stops on conflicting same-name skills; inspect and resolve these before continuing. See the [installation guide](docs/INSTALL.md) for all options and uninstall steps.

## License and attribution

Project integration code is distributed under MIT. Vendored CAD-MCP comes from [daobataotie/CAD-MCP](https://github.com/daobataotie/CAD-MCP) and retains its upstream license. Existing skills retain their source and author information. Daihua provides packaging, portability work, and installation; it does not claim the upstream MCP or skills as wholly original work.

Read [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution. Third-party CAD applications, Python dependencies, and referenced projects remain subject to their own terms.

The v0.1.3 [review report](docs/REVIEW.md) records reproduced issues, fixes, native AutoCAD checks, and remaining test boundaries.
