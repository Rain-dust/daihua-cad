# CAD 执行与恢复

仅在技术路线需要真实 CAD 时读取；离线 DXF 任务不先连接 CAD。下面约束适用于已明确选定的任务文档。上游作者 Delancy；Daihua CAD 集成维护 Rain-dust，许可 MIT。

### 铁律 0：先确定任务文档与操作范围

确定 CAD 路线后连接、打开副本或新建当前任务的文档，记录文档对象与输出路径。`Drawing*.dwg`、空模型空间或窗口标题均不能证明文档可丢弃；不要自动关闭文档、清空现有图形或清理他人的选择集。

COM 选择集只清理本任务创建的对象，推荐唯一名称与 `try/finally`（见下一节）。AutoLISP 的选择集引用在使用后设为 `nil` 即可；`ssget "_X"` 每次重新选择数据库中的实体，不是枚举遗留选择集，不能用 `while (ssget "_X")` 清理。

```lisp
;; ss 是本函数创建并使用的选择集；结束时释放引用
(defun task_selection_example (/ ss)
  (setq ss (ssget "_X"))
  ;; 在明确的任务范围内读取或处理 ss；空图时 ss 为 nil
  (if ss (princ (sslength ss)))
  (setq ss nil)
  (princ)
)
```

### 自己创建的选择集及时释放

`SelectionSets.Add("SS1")` 使用后不 Delete，再次运行同名选择集会报 "已存在" → 程序中断。

```python
import uuid

def task_entities(doc):
    ss = doc.SelectionSets.Add("DAIHUA_" + uuid.uuid4().hex)
    try:
        ss.Select(5)  # 只读取已明确选定文档中的实体
        return list(ss)
    finally:
        ss.Delete()
```

实体总数仅用于发现明显遗漏。根据任务检查对象类型、语义图层、关键尺寸、单位及布局；保存后回读并应用独立于生成结果的验收断言。不要因数量超过阈值或没有异常就返回 `passed=True`，也不要在只读核验中执行修复或 PURGE。

---

### 根据操作选择 CAD 接口

| 接口 | 方案 | 适用场景 | 限制 |
|:---:|------|------|------|
| COM | Python + pyautocad | 图元创建、图层管理、标注 | COM 对象生命周期管理 |
| 命令脚本 | SendCommand / SCR 脚本 | 复杂编辑（TRIM/FILLET/CHAMFER） | 异步执行、错误处理弱 |
| 原生开发 | AutoLISP / C# .NET | 插件开发、性能敏感、批量 | LISP 调试困难；C# 需 AutoCAD .NET SDK |

**降级逻辑**：先记录当前失败点及实际已产生的对象。只有确认上一条操作未生效，或已在任务副本中回滚，才换路线重试；不能在部分成功后盲目重发导致重复实体。`SendCommand` 接收成功和加载 LISP 成功均不是绘图完成证明，需等待命令结束并核验结果。保留原始错误，不用裸 `except` 将失败变成 `True`。

---

### 铁律 3：坐标、捕捉与命令完成状态

- API 使用 WCS/UCS 的约定按具体接口核对；任务使用局部 UCS 时保留其意图，需要临时切换时保存并恢复。不要对每条命令强制 `_UCS _W`。
- `_NON` 是命令内部针对下一点的对象捕捉覆盖，不是可在空闲命令行单独执行的全程开关。需要在整个任务片段中禁用捕捉时保存 `OSMODE`，按位加入 16384，并在结束或异常时恢复原值。
- `SendCommand` 在等待输入等情形下会异步返回；固定 `sleep` 不能证明命令已经完成。使用当前版本可用的命令完成事件、活动命令状态与有限超时，确认空闲后再发送下一条；超时后停止并诊断。
- COM 坐标参数按使用的库构造双精度数组（例如 pyautocad 的 `APoint`）；不要把 pywin32 的 VARIANT 与其他 COM 封装混用。

```python
from contextlib import contextmanager

@contextmanager
def suppress_running_osnap(doc):
    original = int(doc.GetVariable("OSMODE"))
    try:
        doc.SetVariable("OSMODE", original | 16384)
        yield  # 在此执行已验证、可等待完成的任务操作
    finally:
        doc.SetVariable("OSMODE", original)
```

### 铁律 4：审计与整理按需执行，验收依靠实际结果

保存前核对关键几何、图层、标注与打印布局，并在保存后回读。`AUDIT` 用于数据库检查；修复选项会修改图纸，应在任务文档或副本中按需要执行。清理未引用资源可优先使用 `doc.PurgeAll()`，但客户模板中的未使用图层/样式可能需要保留，不把 PURGE 当作每次绘图或只读核验的前置步骤。

`PURGE` 会显示对话框，命令行版本为 `-PURGE`；不要向 `_PURGE` 后直接串接命令行应答。若需执行交互命令，核对本机完整应答、超时和完成状态。AUDIT 的零错误及工具返回 success 均不能代替保存后的工程验收。

官方依据：[ssget](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-0F37CC5E-1559-4011-B8CF-A3BA0973B2C3.htm)、[对象捕捉覆盖](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Core/files/GUID-76B81C1A-373E-4BCD-975A-789FB36C89FE.htm)、[OSMODE](https://help.autodesk.com/cloudhelp/2026/CHS/AutoCAD-Core/files/GUID-DD9B3216-A533-4D47-95D8-7585F738FD75.htm)、[PURGE](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Core/files/GUID-D68BA47B-A79D-4F58-9715-0569CC24BCEF.htm)、[SendCommand](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-ActiveX-Reference/files/GUID-E13A580D-04CA-46C1-B807-95BB461A0A57.htm)。

---


## 十八、COM 兼容与零件图验证经验

以下建议需要在目标 CAD 版本验证，不能将某一电脑上的行为当作通用保证。

### 18.1 COM 忙碌与文档生命周期

- CAD 忙碌时，属性访问和方法调用都可能返回调用被拒绝。重试函数应接收 `lambda: app.Documents.Add()` 等完整调用，采用次数或时间上限；失败时保留错误码与目标文档信息。
- 新建文档后等待其就绪，再读取 `ActiveDocument`。某些版本在无打开文档时需要重新取得文档集合或重新连接，不对所有版本断言相同行为。
- 仅修改当前任务明确选定或创建的文档。自动文件名及窗口标题不能证明内容可以删除；需要清空时在任务文档或临时副本上操作。

### 18.2 避免交互命令挂起

优先使用适合的 COM API，例如 `doc.PurgeAll()`。`AUDIT`、`PURGE` 等命令可能因版本、语言、错误状态追加提示；使用前检查完整应答序列和超时。遇到挂起先尝试取消当前命令并诊断，不自动结束所有 CAD 进程。

### 18.3 保留原生半径与直径标注

`AddDimRadial(Center, ChordPoint, LeaderLength)` 接收圆心与圆上点；`AddDimDiametric(ChordPoint, FarChordPoint, LeaderLength)` 接收直径两端点。两者均不接收圆对象作为点参数。使用 WCS 三维坐标数组，创建后核对实体类型与实际测量值；不要通过覆盖线性尺寸文字来伪造直径标注。参见 Autodesk 的 [半径标注 API](https://help.autodesk.com/cloudhelp/2022/ENU/AutoCAD-ActiveX-Reference/files/GUID-4DAA2BF5-9658-477E-8A1B-1D27831BA2E5.htm) 与 [直径标注 API](https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-LT-ActiveX-Reference/files/GUID-A713EB17-E229-48E7-BFA3-AF7DE13B09BF.htm)。

### 18.4 填充、字体与出图

- 关联填充使用有效闭合边界，按内外环设置岛屿，创建后检查关联句柄和实际显示。
- 文字与线型创建前检查是否已存在；字体、PC3 和纸张名称应从目标电脑检测，不假设某种中文字体或驱动必然存在。
- 为确定性出图可临时设置 `BACKGROUNDPLOT=0`，结束后恢复原值；从目标绘图设备枚举纸张，按项目选择实际比例或适合方案预览的布满图纸。输出后确认文件存在且可读。

### 18.5 保存后的验证

按空间、图层和原生实体类型清点，核对实际单位、关键尺寸、图框和文字。再通过打印预览或截图检查尺寸文字重叠、剖切标识、填充归属等问题；数量、清理成功或工具返回值不能替代这些检查。
