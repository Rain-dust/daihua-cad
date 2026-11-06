# Daihua integration changes

Base: daobataotie/CAD-MCP at ef26482579424bb564b8b2ccc24f29f133f66fbf (MIT).

- Query tools attach/start CAD on first use through the existing COM executor.
- Discover versioned AutoCAD COM registrations from HKCR, ordered by version; keep the generic ProgID fallback. DAIHUA_CAD_PROGID selects an explicit ProgID. No fixed installation drive is required.
- config.json uses ./output rather than the original local workstation path. DAIHUA_CAD_TYPE and DAIHUA_OUTPUT_DIR optionally override CAD type and output directory in the process environment.
- The installer always launches stdio transport from the repository root.

The shipped server is adapted upstream code. Original copyright is retained in LICENSE and ../../licenses/cad-mcp-MIT.txt (see the root third-party notice for the canonical license path).
