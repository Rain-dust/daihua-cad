# Daihua integration changes

Base: daobataotie/CAD-MCP at ef26482579424bb564b8b2ccc24f29f133f66fbf (MIT).

- Query tools attach/start CAD on first use through the existing COM executor.
- Discover registered AutoCAD ProgIDs rather than assuming an installation drive; DAIHUA_CAD_PROGID selects an explicit ProgID.
- Merge partial configuration with independent defaults, then apply DAIHUA_CAD_TYPE and DAIHUA_OUTPUT_DIR even after a missing/corrupt file fallback. Reject unknown CAD types. Relative output paths resolve from the repository independently of the client working directory.
- The installer always launches stdio transport. Explicit SaveAs types select 2018 DWG (64) or DXF (65); other extensions are rejected.
- New entities default to color 256, Linetype ByLayer and lineweight -1. The service reads the pinned document's actual current layer for omitted layer arguments.
- Keep one session document. Window commands and screenshot activate that target; closing/disconnecting it requires an explicit new/open. Reconnection or failed new/open never silently adopts another drawing.
- Failed creation/copy/hatch/array operations clean up only the new objects they created. Query errors propagate rather than returning partial lists as success. Undo/redo acknowledge submission and still require readback verification.

Original copyrights are retained in LICENSE and ../../licenses/cad-mcp-MIT.txt. Detailed review and test scope: ../../docs/REVIEW.md.

Primary API references: [SaveAs](https://help.autodesk.com/cloudhelp/2023/CHS/AutoCAD-ActiveX-Reference/files/GUID-ED0D0B02-25FC-4ED2-9DEE-2B0C9AA9416A.htm), [save format enumeration](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-ActiveX/files/GUID-04B5A49A-96B3-4CE1-9AED-7C3DE85225F5.htm), [Linetype](https://help.autodesk.com/cloudhelp/2024/PTB/AutoCAD-ActiveX-Reference/files/GUID-2EEC97F1-0956-47DA-9FF4-1058EAA173A8.htm).
