# CAD API 配方

仅在已选择 CAD 路线时按所需章节查阅；这些接口示例不是固定执行管线。目标文档、任务范围、单位与环境按当前任务确定；示例中的连接、新建、保存、全选和命令不得直接套在客户原图。先遵守 [执行约束](cad-execution.md)，调用参数与对象支持以目标 CAD 版本为准。

检索：COM 连接、坐标、基本图元、编辑、图层、标注、块/属性、选择集、三维、布局/打印、AutoLISP、批量保存、国产 CAD。

上游作者 Delancy；Daihua CAD 集成维护 Rain-dust，许可 MIT。

## ⚠️ Python AutoCAD COM 关键踩坑

### 环境
- AutoCAD 2020+ (中文版), Python 3.10+ + pyautocad/pywin32, Windows 11

### 连接方式
| 方式 | 结果 |
|------|------|
| `pyautocad.Autocad(create_if_not_exists=True)` | ✅ 推荐，自动处理COM |
| `win32com.client.Dispatch("AutoCAD.Application")` | ✅ 底层连接 |
| `win32com.client.GetActiveObject("AutoCAD.Application")` | ✅ 连接已运行的实例 |
| `win32com.client.Dispatch("AutoCAD.Application.24")` | ✅ 指定版本(2021=24,2022=24.1,2023=24.2,2024=24.3) |

### 调用边界
1. **pyautocad 安全数组**: 坐标必须用 `APoint(x,y,z)` 包装
2. **COM对象生命周期**: 仅在路线需要 CAD 时连接所选产品；连接失败先诊断。必要时才启动新实例，重新取得明确的任务文档，不把当前活动文档当作旧目标。
3. **单位**: AutoCAD 使用绘图单位；结合 `INSUNITS`、已知尺寸及项目约定确认毫米、米或英制，不凭软件语言推断。
4. **中文命令**: 用 `acad.doc.SendCommand("_LINE ")` 带下划线前缀
5. **选择集**: 用唯一名称创建，finally 中只 Delete 本任务新建的选择集，不删除整个集合或他人的选择集。
6. **中望/浩辰兼容**: 先验证目标产品的 COM 接口与对象支持；不假定 pyautocad 自动连接到所选国产 CAD，部分 VLAX 需适配。

---

## 一、AutoCAD 基础知识

### 1.1 AutoCAD 概述

AutoCAD是Autodesk公司开发的通用CAD软件，支持建筑、机械、电气、土木等领域。

### 1.2 坐标系

- **WCS (世界坐标系)**: 绝对坐标系，原点固定
- **UCS (用户坐标系)**: 可自定义原点和方向
- **极坐标**: `@距离<角度` (如 `@100<45`)
- **相对坐标**: `@x,y` (如 `@50,30`)

### 1.3 文件类型

| 类型 | 扩展名 | 说明 |
|------|--------|------|
| 图形文件 | .dwg | 标准图形文件 |
| 交换格式 | .dxf | 文本/二进制交换格式 |
| 模板 | .dwt | 含预设样式模板 |
| 标准 | .dws | 图层/标注/文字标准 |
| 脚本 | .scr | 批量命令脚本 |
| 线型 | .lin | 自定义线型定义 |
| 填充 | .pat | 自定义填充图案 |

### 1.4 常用API对象层次

```
AutoCAD.Application
├── ActiveDocument (Document)
│   ├── ModelSpace        (模型空间)
│   ├── PaperSpace        (图纸空间)
│   ├── Layers            (图层集合)
│   ├── Linetypes         (线型集合)
│   ├── TextStyles        (文字样式)
│   ├── DimStyles         (标注样式)
│   ├── Blocks            (块集合)
│   ├── SelectionSets     (选择集)
│   ├── Groups            (组集合)
│   └── Utility           (角度/距离/坐标工具)
├── Documents
├── Preferences           (系统配置)
└── MenuGroups            (菜单组)
```

---

## 二、绘图命令 (Drawing)

### 2.1 基本图元

```python
from pyautocad import Autocad, APoint, aDouble
acad = Autocad(create_if_not_exists=True)

# 直线
line = acad.model.AddLine(APoint(0,0,0), APoint(100,50,0))

# 圆
circle = acad.model.AddCircle(APoint(50,50,0), 30)

# 圆弧 (center, radius, start_angle弧度, end_angle弧度)
arc = acad.model.AddArc(APoint(50,50,0), 30, 0, 3.14159)

# 轻量多段线 (2D, 推荐)
pts = aDouble(0,0, 100,0, 100,50, 50,50)  # x,y交替
pline = acad.model.AddLightWeightPolyline(pts)
pline.Closed = True
pline.Color = 256  # ByLayer；颜色通过语义图层设置

# 椭圆
ellipse = acad.model.AddEllipse(APoint(50,50,0), APoint(30,0,0), 0.5)

# 样条曲线
fit_pts = aDouble(0,0,0, 20,30,0, 50,10,0, 80,60,0, 100,0,0)
spline = acad.model.AddSpline(fit_pts, aDouble(1,1,0), aDouble(1,0,0))

# 文字
text = acad.model.AddText("设计说明", APoint(10,10,0), 5)
mtext = acad.model.AddMText(APoint(10,10,0), 50, "多行\\P文字")

# 点
point = acad.model.AddPoint(APoint(50,50,0))
```

### 2.2 填充 (Hatch)

```python
outer_loop = [pline]
hatch = acad.model.AddHatch(0, "ANSI31", True)
hatch.AppendOuterLoop(outer_loop)
hatch.Evaluate()
hatch.PatternScale = 2.0
hatch.PatternAngle = 0.785  # 45°
hatch.Color = 256  # ByLayer
```

### 2.3 SendCommand（仅在 API 不适用且命令流程已验证时）

```python
acad.doc.SendCommand("_CIRCLE 50,50 30 ")
acad.doc.SendCommand("_LINE 0,0 100,50 \n")
# \n = 回车, 空格 = 结束当前输入
```

---

## 三、编辑命令 (Modify)

### 3.1 基本编辑

```python
# 移动
obj.Move(APoint(0,0,0), APoint(50,0,0))

# 复制
new_obj = obj.Copy()
new_obj.Move(APoint(0,0,0), APoint(100,0,0))

# 旋转 (基点, 角度弧度)
obj.Rotate(APoint(0,0,0), 1.5708)  # 90°

# 缩放 (基点, 比例因子)
obj.ScaleEntity(APoint(0,0,0), 2.0)

# 镜像 (镜像线两点)
obj.Mirror(APoint(0,0,0), APoint(0,100,0))

# 偏移
obj.Offset(10)  # 返回数组(可能多个结果)

# 阵列 (矩形)
obj.ArrayRectangular(3, 2, 1, 100, 50, 0)  # rows,cols,levels,row_sp,col_sp,level_sp
```

### 3.2 通过SendCommand操作

```python
acad.doc.SendCommand("_MOVE\n")       # 移动
acad.doc.SendCommand("_COPY\n")       # 复制
acad.doc.SendCommand("_ROTATE\n")     # 旋转
acad.doc.SendCommand("_SCALE\n")      # 缩放
acad.doc.SendCommand("_MIRROR\n")     # 镜像
acad.doc.SendCommand("_OFFSET 10\n")  # 偏移
acad.doc.SendCommand("_TRIM\n")       # 修剪
acad.doc.SendCommand("_EXTEND\n")     # 延伸
acad.doc.SendCommand("_FILLET R 5\n_FILLET\n")  # 圆角R5
acad.doc.SendCommand("_CHAMFER D 3 3\n_CHAMFER\n") # 倒角3x3
```

---

## 四、图层管理 (Layers)

```python
# 创建图层
layer = acad.doc.Layers.Add("WALL")
layer.Color = 1     # 红色 (ACI色号)
layer.Linetype = "Continuous"

# 设置当前图层
acad.doc.ActiveLayer = acad.doc.Layers("WALL")

# 遍历所有图层
for layer in acad.doc.Layers:
    print(f"{layer.Name}: color={layer.Color}, linetype={layer.Linetype}")

# 锁定/冻结/关闭
ref = acad.doc.Layers("WALL")
ref.Lock = True       # 锁定
ref.Freeze = False    # 冻结
ref.LayerOn = True    # 开关

# 修改对象图层
line.Layer = "DIM"

# 批量修改图层 (SendCommand)
acad.doc.SendCommand("_LAYMCH\n")       # 图层匹配
acad.doc.SendCommand("_LAYISO\n")       # 图层隔离
acad.doc.SendCommand("_LAYUNISO\n")     # 取消隔离
```

### ACI常用色号

| 色号 | 颜色 | 适用 |
|------|------|------|
| 1 | 红 | 标注/重点 |
| 2 | 黄 | 中心线 |
| 3 | 绿 | 辅助线 |
| 4 | 青 | 文字 |
| 5 | 蓝 | 轮廓 |
| 6 | 品红 | 剖面 |
| 7 | 白/黑 | 默认 |
| 8 | 灰 | 参考线 |

---

## 五、标注与文字 (Dimensions & Text)

### 5.1 标注

```python
p1 = APoint(0, 0, 0)
p2 = APoint(100, 0, 0)
text_pos = APoint(50, -20, 0)

# 线性标注
dim = acad.model.AddDimAligned(p1, p2, text_pos)

# 旋转标注
dim = acad.model.AddDimRotated(p1, p2, text_pos, 0)

# 半径/直径标注
dim_rad = acad.model.AddDimRadial(APoint(50,50,0), APoint(80,50,0), 10)
dim_dia = acad.model.AddDimDiametric(APoint(20,50,0), APoint(80,50,0), 10)

# 角度标注
dim_ang = acad.model.AddDimAngular(APoint(0,0,0), p1, p2, APoint(30,30,0))

# 坐标标注
dim_ord = acad.model.AddDimOrdinate(APoint(50,50,0), APoint(50,0,0), True) # X坐标

# 标注样式
dim_style = acad.doc.DimStyles.Add("GB_DIM")
dim.TextHeight = 3.5    # 字高
dim.ArrowheadSize = 2.5 # 箭头大小
dim.DecimalSeparator = "."
```

### 5.2 公差与粗糙度

```python
# 公差标注(通过SendCommand兼容性好)
acad.doc.SendCommand("_TOLERANCE\n")
# 或使用Leader+文字模拟
leader = acad.model.AddLeader(points, annotation, 0)
```

### 5.3 特殊字符

| 代码 | 字符 |
|------|------|
| %%c | φ 直径 |
| %%d | ° 度 |
| %%p | ± 正负号 |
| %%u | 下划线开关 |
| \\P | 换行(MTEXT) |

---

## 六、块与属性 (Blocks & Attributes)

### 6.1 块定义

```python
# 创建块定义
block = acad.doc.Blocks.Add(APoint(0,0,0), "MyBlock")
# 在块定义中添加对象
block.AddCircle(APoint(0,0,0), 10)
block.AddLine(APoint(-10,0,0), APoint(10,0,0))

# 插入块参照
insert_pt = APoint(50, 50, 0)
block_ref = acad.model.InsertBlock(insert_pt, "MyBlock", 1, 1, 1, 0)
```

### 6.2 带属性的块

```python
# 创建属性定义
att = block.AddAttribute(
    5,              # 字高
    0,              # 模式(0=无)
    "标签",         # 提示
    APoint(0,15,0), # 插入点
    "TAG",          # 标签
    "默认值"         # 默认值
)

# 插入后修改属性
for att in block_ref.GetAttributes():
    if att.TagString == "TAG":
        att.TextString = "零件-001"
        att.Update()
```

### 6.3 外部参照 (Xref)

```python
# 附着外部参照
xref = acad.model.AttachExternalReference(
    reference_dwg,  # 项目指定的外参绝对路径
    "base",              # 块名
    APoint(0,0,0),       # 插入点
    1, 1, 1, 0           # 比例和旋转
)
```

---

## 七、选择集与过滤

以下示例只删除自身新建的选择集。`doc` 是当前任务已明确选定的文档；读取全部实体不授权修改全部实体。

```python
import uuid

ss = doc.SelectionSets.Add("DAIHUA_" + uuid.uuid4().hex)
try:
    ss.Select(5)  # acSelectionSetAll；也可按任务使用窗口选择
    circles = [obj for obj in ss
               if obj.ObjectName == "AcDbCircle" and obj.Radius > 10]
    for obj in circles:
        print(f"圆半径: {obj.Radius}, 图层: {obj.Layer}")
finally:
    ss.Delete()  # 只清理本函数创建的选择集
```

需要原生 DXF 过滤器时，FilterType 与 FilterData 必须是匹配的组码数组和值数组，关系运算符用 -4 组码；按本机 COM 库构造相应 SAFEARRAY，不使用混合组码/值的 `VARIANT(0, ...)`。

### DXF组码常用过滤

| 组码 | 含义 | 示例 |
|------|------|------|
| 0 | 对象类型 | "CIRCLE","LINE","TEXT" |
| 8 | 图层名 | "WALL","DIM" |
| 62 | 颜色 | 1(红), 2(黄) |
| 40 | 半径(圆)/字高(文字) | 10.0 |
| 10 | 中心点/插入点 | 坐标 |

---

## 八、三维建模 (3D Modeling)

### 8.1 基本3D实体

```python
# 长方体
box = acad.model.AddBox(APoint(0,0,0), 100, 50, 30)  # 角点,长,宽,高

# 圆柱体
cyl = acad.model.AddCylinder(APoint(50,50,0), 20, 100)  # 底面中心,半径,高

# 球体
sphere = acad.model.AddSphere(APoint(50,50,30), 25)

# 圆锥体
cone = acad.model.AddCone(APoint(50,50,0), 15, 50)

# 圆环体
torus = acad.model.AddTorus(APoint(50,50,0), 30, 10)  # 中心,大半径,管半径
```

### 8.2 拉伸与旋转

```python
# 创建面域
regions = acad.model.AddRegion([pline])[0]

# 拉伸面域成实体
height = 50
taper_angle = 0  # 拔模角度(弧度)
solid = acad.model.AddExtrudedSolid(regions[0], height, taper_angle)

# 旋转面域成实体
solid = acad.model.AddRevolvedSolid(regions[0], APoint(0,0,0), APoint(0,0,1), 2 * 3.141592653589793)
```

### 8.3 布尔运算

```python
# 并集
solid1.Boolean(0, solid2)  # acUnion

# 差集
solid1.Boolean(1, solid2)  # acSubtraction

# 交集
solid1.Boolean(2, solid2)  # acIntersection
```

### 8.4 SendCommand 3D

```python
acad.doc.SendCommand("_BOX\n0,0,0\nL\n100\n50\n30\n")
acad.doc.SendCommand("_CYLINDER\n50,50,0\n20\n100\n")
acad.doc.SendCommand("_SUBTRACT\n")  # 差集
acad.doc.SendCommand("_UNION\n")     # 并集
```

---

## 九、图纸空间与打印

### 9.1 布局操作

```python
# 获取布局列表
for layout in acad.doc.Layouts:
    print(f"布局: {layout.Name}")

# 创建新布局
acad.doc.Layouts.Add("A3_打印")

# 切换布局
acad.doc.ActiveLayout = acad.doc.Layouts("A3_打印")

# 创建视口
vp = acad.doc.PaperSpace.AddPViewport(
    APoint(10,10,0),  # 中心点
    200,              # 宽
    150               # 高
)
vp.Display(True)  # 显示视口内容
```

### 9.2 打印/导出PDF

```python
# 通过SendCommand
acad.doc.SendCommand("_PLOT\n")        # 打印
acad.doc.SendCommand("_EXPORTPDF\n")   # 导出PDF

# 通过API
plot_cfg = doc.ActiveLayout  # 已固定任务文档的布局；设备/纸张先从本机枚举
plot_cfg.ConfigName = "DWG To PDF.pc3"
plot_cfg.PaperUnits = 1   # mm
plot_cfg.StandardScale = 0  # acScaleToFit
plot_cfg.PlotType = 4      # acExtents
doc.Plot.PlotToFile(output_pdf)  # 项目指定的输出绝对路径
```

---

## 十、AutoLISP 自动化 (CAD知识库核心)

### 10.1 LISP基础

来自"CAD学习知识库"的308个插件揭示了LISP在工程领域的真实生产力。

```lisp
;; 基础结构
(defun c:命令名 (/ 局部变量1 局部变量2)
  (setq var1 value1)       ; 设置变量
  (setq ss (ssget))        ; 获取选择集
  (princ "\\n提示文字")    ; 命令行输出
  (princ)                  ; 静默退出
)

;; 选择集遍历
(defun c:changecolor (/ ss i en)
  (setq ss (ssget))
  (setq i 0)
  (repeat (sslength ss)
    (setq en (ssname ss i))
    (setq ed (entget en))
    (entmod (subst (cons 62 1) (assoc 62 ed) ed))  ; 改为红色
    (setq i (1+ i))
  )
)

;; 坐标标注 (from ZBBZ.lsp)
(defun c:zbbz ()
  ;; 创建标注图层
  (entmake (list '(0 . "LAYER") '(100 . "AcDbLayerTableRecord")
    '(2 . "UserDimCoors") '(70 . 0) '(62 . 7) '(6 . "Continuous")))
  ;; 设置当前图层
  (setvar "CLAYER" "UserDimCoors")
  ;; 获取点
  (while (setq pt (getpoint "\\n拾取标注点:"))
    (setq x (rtos (car pt) 2 3))
    (setq y (rtos (cadr pt) 2 3))
    (setq str (strcat "X=" x "\\PY=" y))
    (entmake (list '(0 . "MTEXT") (cons 1 str) (cons 10 pt) '(40 . 3.5)))
  )
)
```

### 10.2 批量处理框架 (mini_系列)

CAD学习知识库中最核心的模式——`mini_`前缀系列，提供了专业级工程自动化框架：

```lisp
;; mini_ 系列的核心模式: 配置-选择-处理
(defun c:mini_任务名 ( / old_cmd config_file sel_set result)
  ;; 1. 保存当前环境
  (setq old_cmd (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)

  ;; 2. 加载配置(如有)
  ;; (load "mini_config.lsp")

  ;; 3. 选择对象
  (princ "\\n选择对象: ")
  (setq sel_set (ssget))

  ;; 4. 处理逻辑
  ;; ...

  ;; 5. 恢复环境
  (setvar "CMDECHO" old_cmd)
  (princ)
)
```

### 10.3 LISP常用函数速查

| 函数 | 用途 |
|------|------|
| `(ssget)` | 选择对象返回选择集 |
| `(entget en)` | 获取实体数据表 |
| `(entmod data)` | 修改实体数据 |
| `(entmake data)` | 创建新实体 |
| `(ssadd en ss)` | 添加实体到选择集 |
| `(sslength ss)` | 选择集数量 |
| `(ssname ss i)` | 获取第i个实体名 |
| `(command "CMD" ...)` | 执行AutoCAD命令 |
| `(vla-get-property obj)` | 获取ActiveX属性 |
| `(vlax-curve-getArea obj)` | 获取曲线面积 |
| `(vlax-curve-getDistAtPoint obj pt)` | 获取点到起点距离 |

### 10.4 LISP→Python 对照

| AutoLISP | Python(pyautocad) |
|----------|-------------------|
| `(setq p (getpoint))` | `p = acad.doc.Utility.GetPoint()` |
| `(command "LINE" p1 p2 "")` | `acad.model.AddLine(p1, p2)` |
| `(entget (car (entsel)))` | `acad.doc.Utility.GetEntity()` |
| `(ssget)` | `acad.doc.SelectionSets.Add("SS")` |
| `(vl-load-com)` | pyautocad自动处理 |
| `(entmod ...)` | `obj.Layer = "NEW"` 等属性赋值 |

---

## 十一、批量处理与文件操作

### 11.1 批量打开/处理/保存

先固定输入清单和新的输出目录，逐个打开任务文件，不复用随后可能变化的 ActiveDocument；在副本中修改并 SaveAs 到不存在的路径。只关闭本任务打开的文档，不覆盖原件，不把异常清理扩展为关闭所有图纸。每个结果回读检查成功后再处理下一个；失败时保留原始错误及该文件已执行状态，不能盲目全批重跑。

### 11.2 文件格式转换

批量转换先固定经授权的输入清单与输出目录，逐个打开并保存到新的目标路径；拒绝静默覆盖。优先使用 `Documents.Open()` 与当前 CAD 版本支持的 `SaveAs()` 格式枚举，转换后用实际文件回读核对单位、布局及关键实体，再关闭本任务打开的文档。

若必须使用命令，先验证该版本完整的保存/导出应答流程、确认目标文档，并等待命令真正完成；不能用固定 `sleep` 后发送 `_CLOSE` 作为完成判据。未完成或失败时保留诊断现场，不保存/关闭无关文档。

DXF、DWT、PDF、DWF、STL、STEP 等格式的导入/导出支持取决于 CAD 产品、版本、模块和转换器；逐项检查实际能力，不将改扩展名视为格式转换。

### 11.3 运行脚本

```python
# 运行SCR脚本
acad.doc.SendCommand(f'_SCRIPT "{script_path}"\n')  # 项目脚本绝对路径

# 加载LISP插件
acad.doc.SendCommand(f'(load "{lisp_path}")\n')  # 路径使用正斜线
acad.doc.SendCommand("MYTOOL\n")  # 执行LISP命令

# 运行VBA宏
acad.doc.SendCommand("_-VBARUN MyMacro\n")
```

---

## 十二、中望CAD/浩辰CAD兼容

### 12.1 COM 接口选择

按配置的 CAD 产品查询可用 ProgID，再连接该产品；没有通用 ProgID 时才查询对应版本化 ProgID。不在 ZWCAD/GStarCAD 失败后悄悄启动 AutoCAD，也不遍历所有产品启动实例。接口名、支持版本、Python 包与具体方法均需在目标机验证；仓库 MCP 的 ProgID 检测可复用。

### 12.2 常见接口族（不是本项目的兼容实测保证）

| 特性 | AutoCAD | 中望CAD | 浩辰CAD |
|------|---------|---------|---------|
| COM Dispatch | ✅ | ✅ | ✅ |
| pyautocad | ✅ | ✅ | ✅ |
| AutoLISP | ✅ | ✅ | ✅ |
| VLISP扩展 | ✅ | 部分支持 | 部分支持 |
| ObjectARX | ✅ | ZRX | GRX |
| SendCommand | ✅ | ✅ | ✅ |
| 三维建模 | ✅ | ✅ | ✅ |

---

## 十四、常见问题与调试

### 14.1 常见错误

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| pyautocad连接失败 | AutoCAD未运行 | 手动启动,或用`create_if_not_exists=True` |
| COM错误"RPC服务器不可用" | 目标 CAD 已关闭或连接失效 | 停止操作，显式重连并重新打开/指定任务文档 |
| 选择集"已存在" | 未Delete旧选择集 | 每次用完`ss.Delete()` |
| SendCommand无反应 | 命令格式错误 | 空格代替回车确认, `\n`代替回车 |
| 中文乱码 | 版本/命令接口/字体等 | 核对实际接口编码与字体，用小范围样本验证，不全局强改 GBK |
| LISP加载失败 | 路径含中文 | 用英文路径或`(findfile)` |
| 三维操作报错 | 未切换到3D视图 | `acad.doc.SendCommand("_VSCURRENT _R\n")` |

### 14.2 小范围调试

只读取与失败有关的实体属性、目标文档名、对象类型及层归属，不为每个对象枚举所有属性或重复导出全图。选择集采用唯一名称及 try/finally；用保存后的任务文件和明确的预期几何判断结果。错误需保留，不以空列表或无条件 True 掩盖失败。
