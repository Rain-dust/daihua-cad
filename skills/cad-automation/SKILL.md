---
name: cad-automation
description: 使用 CAD MCP、Python COM、AutoLISP 或离线 DXF 创建和编辑 CAD 图纸，处理图层、尺寸、块、出图及回读验证。用于 AutoCAD、浩辰 CAD、中望 CAD 自动化和 CAD 文件制作。
license: MIT
metadata:
  category: engineering-cad
  version: 1.2.2
  author: Delancy
  integration-maintainer: Rain-dust
---

# CAD 自动化绘图 Skill（优化版）

## 环境接入

上游作者 Delancy；Daihua CAD 集成维护 Rain-dust。执行前先阅读 [安装环境与验证约定](references/local-setup.md)，使用当前电脑配置的 MCP 或项目环境。

本skill提供AutoCAD自动化绘图的完整知识体系，涵盖Python COM自动化、AutoLISP插件开发、国产CAD兼容等核心内容。

## 0. 2026-06-11 优化版使用原则

本版把 CAD 自动化从“只会调用 AutoCAD”升级为“三栈协同”：

| 场景 | 首选技术 | 原因 | 降级方案 |
|---|---|---|---|
| 已安装 AutoCAD、要直接生成 DWG | `win32com` / `pyautocad` | 可调用真实 AutoCAD，适合出 DWG、标注、图层、打印 | SendCommand / SCR |
| 没有 CAD 软件、要稳定生成交换文件 | `ezdxf` | 离线生成 DXF，适合 CI、服务器、批量草图 | 生成 SVG/JSON 几何清单 |
| 参数化 3D、模具/夹具/结构件建模 | `CadQuery` / FreeCAD | 适合尺寸驱动和 STEP/STL 输出 | 先生成 2D 总图，再转 3D |
| 国产 CAD 兼容 | COM + 英文命令 + DXF | 中望/浩辰对 COM 和 DXF 兼容度通常较高 | AutoLISP |

### 执行铁律
1. 优先使用已配置的 MCP；直接 COM 时检测本机实际 CAD 与 ProgID。连接不可用时，只有任务允许 DXF 才转离线路线；必须交付 DWG 时先处理连接或说明交付障碍，不能把 DXF 改扩展名代替。
2. 先确认项目单位、坐标系和比例，模型按实际单位 1:1 绘制；机械示例可采用毫米，既有图纸不得静默换单位。图纸空间处理视口和出图比例。
3. 按项目建立图层、核对 WCS/UCS 并清理本任务创建的选择集。整理图形优先使用无交互 API（如 `PurgeAll()`）；审计、缩放和重生成按当前 CAD 版本及任务需要执行，不盲目串接会等待输入的命令。
4. 输出前至少做 L3 验证：对象数量、关键图层、关键几何尺寸、文字/标注存在性。
5. 使用外部开源项目的思路、API 或示例时，在内部工作记录保留来源、许可证和使用方式；除许可证明确要求随成果附带的声明外，不往客户交付包加入 `ATTRIBUTION.md`。

### 项目默认交付约定

- 可编辑 DWG 默认保存到模型空间的完整编辑视图，按构件和用途分层、外观 ByLayer。模型背景沿用使用者设置；不得以 PDF/图片或导入碎线替代原生图形。
- 未指定时，对外文件夹使用简短项目名，默认交付最终 DWG 和 PDF；脚本、日志、核验数据与备份单独存放。用户需要 DXF、源代码或其他成果时，按明确清单交付。
- 保存后的打开状态、图层有效性、图框可见性及打包内容，按 [可编辑 DWG 分层交付验收](references/editable-dwg-delivery.md) 检查。本节为项目默认约定，用户当前任务的明确要求优先；局部修改不因此扩展为整图重建。

### 可编辑 DWG 分层交付硬约束

交付可编辑 DWG 时必须阅读并执行 [可编辑 DWG 分层交付验收](references/editable-dwg-delivery.md)。按实际构件和用途分层，实体外观 ByLayer；不得把整张 PDF/图片、导入碎线或整图单一块充当可编辑 CAD。规则铺装用原生 HATCH，尺寸用 DIMENSION，组件用分类 INSERT；整理范围服从任务：新建或明确要求整图整理时处理所用底图，局部修改保留无关底图与既有标准。保存后逐张回读 DWG，清点“图层 × 实体类型”，抽查关闭/隔离及编辑更新。AUDIT 0 错误或 PDF 外观正确不能替代这些检查；不合格先修正再交付。

### 交付前文案检查

正式交付的 DWG/PDF 不写“按用户提供”“用户提供的方案图”等对话或制作过程用语。保留工程信息和必要技术限定，并同步核对两种格式；具体规则见 [CAD 设计狮：正式交付图纸用语](../cad-designer/SKILL.md#正式交付图纸用语)。

### 外部开源资料吸收范围
本 skill 只吸收公开文档中的工程方法，不复制大段源代码。参考项目：

| 项目 | 作用 | 许可证 | 使用方式 |
|---|---|---|---|
| `reclosedev/pyautocad` | AutoCAD ActiveX 自动化封装、坐标与对象遍历思路 | BSD-2-Clause | 作为 COM 自动化路线参考 |
| `mozman/ezdxf` | 离线 DXF 创建/读写/修改 | MIT | 作为无 AutoCAD 环境的 fallback |
| `CadQuery/cadquery` | Python 参数化 3D CAD | Apache-2.0 | 作为 3D 参数化建模路线参考 |
| 开源CAD自动化项目 | 行业最佳实践参考 | 多种 | 作为技术路线与接口设计参考 |

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

### 核心踩坑
1. **pyautocad 安全数组**: 坐标必须用 `APoint(x,y,z)` 包装
2. **COM对象生命周期**: `GetActiveObject`失败则需`Dispatch`
3. **单位**: AutoCAD 使用绘图单位；结合 `INSUNITS`、已知尺寸及项目约定确认毫米、米或英制，不凭软件语言推断。
4. **中文命令**: 用 `acad.doc.SendCommand("_LINE ")` 带下划线前缀
5. **选择集**: `acad.doc.SelectionSets` 使用后必须`Delete()`，否则累积报错
6. **中望/浩辰兼容**: pyautocad同样支持(COM接口兼容)，但部分VLAX函数需要适配

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
pline.Color = 1  # 红色

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
hatch.Color = 3
```

### 2.3 SendCommand 方式 (兼容性最好)

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
solid = acad.model.AddExtrudedSolid(regions, height, taper_angle)

# 旋转面域成实体
solid = acad.model.AddRevolvedSolid(regions, APoint(0,0,0), APoint(0,0,100), 360)
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
plot_cfg = acad.doc.Plot  # ActivePlotConfiguration
plot_cfg.ConfigName = "DWG To PDF.pc3"
plot_cfg.PaperUnits = 1   # mm
plot_cfg.StandardScale = 0  # acScaleToFit
plot_cfg.PlotType = 4      # acExtents
acad.doc.Plot.PlotToFile(output_pdf)  # 项目指定的输出绝对路径
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

```python
import os
from pyautocad import Autocad

acad = Autocad(create_if_not_exists=True)

def batch_process_dwgs(folder):
    """批量处理DWG文件"""
    for f in os.listdir(folder):
        if not f.endswith('.dwg'):
            continue
        path = os.path.join(folder, f)
        # 打开
        doc = acad.app.Documents.Open(path)
        doc = acad.app.ActiveDocument  # 确保获取最新文档

        # 在这里做处理...
        # 例如：清理、修改图层、添加标注等

        # 保存关闭
        doc.Save()
        doc.Close()
        print(f"已处理: {f}")

# 使用
batch_process_dwgs(drawings_folder)  # 项目指定的图纸目录
```

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

### 12.1 COM接口兼容性

来自"AutoCAD知识库"的国产CAD适配经验：

```python
# 中望CAD (ZWCAD)
try:
    acad = win32com.client.Dispatch("ZWCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")

# 浩辰CAD (GStarCAD)
try:
    acad = win32com.client.Dispatch("GStarCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")

# 通用兼容写法
def get_cad():
    for progid in ["AutoCAD.Application", "ZWCAD.Application", "GStarCAD.Application"]:
        try:
            return win32com.client.Dispatch(progid)
        except:
            continue
    raise Exception("未找到可用的CAD程序")
```

### 12.2 差异点

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

## 十三、AI+CAD 前沿 (AI+CAD知识库)

### 13.1 Text-to-CAD / AI生成CAD

目前主流的AI+CAD方向：

1. **自然语言→CAD模型**: CADAM、Leo AI、MecAgent等
2. **LLM生成CAD代码**: 通过大模型生成AutoLISP/Python/C#代码，再由AutoCAD执行
3. **特征识别**: AI识别工程图中的几何特征
4. **智能标注**: 自动提取模型项目生成标注

### 13.2 AI辅助CAD工作流

```python
# 通过AI生成AutoCAD脚本
# 示例：用户说 "画一个100x50的矩形，四周倒角R5"
# AI自动生成：

def ai_create_rounded_rect(length=100, width=50, radius=5):
    """AI生成的带倒角矩形"""
    acad = Autocad(create_if_not_exists=True)
    # 画矩形
    pts = aDouble(0,0, length,0, length,width, 0,width)
    pline = acad.model.AddLightWeightPolyline(pts)
    pline.Closed = True
    # 倒角
    acad.doc.SendCommand(f"_FILLET R {radius}\n_FILLET P\n")
    # 选择多段线
    pline.Highlight(True)
    acad.doc.SendCommand("P L\n")
    return pline

# 结合LLM的CAD Agent模式
# 1. LLM解析用户意图
# 2. 生成CAD操作序列
# 3. 通过COM/SendCommand执行
# 4. 验证结果反馈
```

### 13.3 重要开源项目

| 项目 | 说明 |
|------|------|
| Pointer-CAD | DeepSeek+港大,LLM生成B-Rep实体 |
| Zero-to-CAD | Autodesk, 大规模CAD构造序列 |
| text-to-cad | Jake, 自然语言→可编辑CAD |
| VideoCAD | MIT, 视频学习CAD操作 |
| WHUCAD | 武大, 首个CAD智能核心开源 |
| LLM4CAD | UT Austin, 多模态LLM→3D CAD |
| CADAM | 自然语言→参数化3D模型 |

---

## 十四、常见问题与调试

### 14.1 常见错误

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| pyautocad连接失败 | AutoCAD未运行 | 手动启动,或用`create_if_not_exists=True` |
| COM错误"RPC服务器不可用" | AutoCAD已关闭 | 重新dispatch |
| 选择集"已存在" | 未Delete旧选择集 | 每次用完`ss.Delete()` |
| SendCommand无反应 | 命令格式错误 | 空格代替回车确认, `\n`代替回车 |
| 中文乱码 | 编码问题 | SendCommand前确保AutoCAD设为GBK |
| LISP加载失败 | 路径含中文 | 用英文路径或`(findfile)` |
| 三维操作报错 | 未切换到3D视图 | `acad.doc.SendCommand("_VSCURRENT _R\n")` |

### 14.2 调试技巧

```python
# 查看所有对象属性
obj = acad.model(0)  # 第一个对象
for prop in dir(obj):
    if not prop.startswith('_'):
        try:
            val = getattr(obj, prop)
            print(f"{prop} = {val}")
        except:
            pass

# 列出所有文档
for i in range(acad.app.Documents.Count):
    doc = acad.app.Documents(i)
    print(f"文档 {i}: {doc.Name}")

# 查看选择集内容
ss = acad.doc.SelectionSets.Add("DEBUG")
ss.Select(5)  # 全选
print(f"当前图形有 {ss.Count} 个对象")

# 逐个查看类型
for obj in ss:
    print(f"  {obj.ObjectName}: Layer={obj.Layer}, Color={obj.Color}")
ss.Delete()
```

---

## 十五、工作流程总结

### AI自动化CAD标准流程

```
用户需求 → 分析绘图策略 → 选择APILISP/SendCommand → 生成代码 → 连接CAD执行 → 验证结果
```

### 功能矩阵

| 功能 | Python | LISP | SendCommand |
|------|:---:|:---:|:---:|
| 基本绘图 | ✅ | ✅ | ✅ |
| 编辑操作 | ✅ | ✅ | ✅ |
| 图层管理 | ✅ | ✅ | ✅ |
| 标注 | ✅ | ✅ | ✅ |
| 块/属性 | ✅ | ✅ | ✅ |
| 选择集过滤 | ✅ | ✅ | ✅ |
| 三维建模 | ✅ | ⚠️ | ✅ |
| 图纸空间 | ✅ | ⚠️ | ✅ |
| 批量处理 | ✅ | ✅ | ⚠️ |
| 文件转换 | ✅ | ⚠️ | ✅ |
| 外部参照 | ✅ | ✅ | ✅ |

### 选择指南

- **快速原型**: SendCommand（最通用，中望/浩辰全兼容）
- **生产自动化**: Python + pyautocad（类型安全，逻辑复杂）
- **插件开发**: AutoLISP（AutoCAD原生，用户自定义命令）
- **企业级**: C# .NET API（性能最强，DLL部署）
- **AI辅助**: LLM → Python/LISP代码 → COM执行

---

**注意**: 所有代码单位为绘图单位（默认mm），使用前确认AutoCAD图形单位设置。国产CAD(中望/浩辰)COM接口基本兼容，部分VLAX函数差异请查阅对应API文档。

---

## 十六、CAD 核心铁律速查（2026-06-01 从 SW skill 架构移植）

> 以下铁律来自 solidworks-automation v4.4.0 的成功验证模式，针对 CAD 场景做了适配。

---

### 铁律 0：先确定任务文档与操作范围

启动时连接或新建当前任务的文档，记录文档对象与输出路径。`Drawing*.dwg`、空模型空间或窗口标题均不能证明文档可丢弃；不要自动关闭文档、清空现有图形或清理他人的选择集。

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

### 铁律 1：选择集用完必 Delete——CAD 的"GetBodies2 防假跑" 🔴

**SW对应**: GetBodies2 实体计数验证

**CAD病灶**: `SelectionSets.Add("SS1")` 使用后不 Delete，再次运行同名选择集会报 "已存在" → 程序中断。

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

### 铁律 2：三级执行策略——CAD 等效于 Python→VBA→C# 🔴

**SW对应**: Sec 24 铁律8 (Tier 1 Python COM → Tier 2 VBA宏 → Tier 3 C# exe)

| 级别 | 方案 | 适用场景 | 限制 |
|:---:|------|------|------|
| **Tier 1** | Python + pyautocad | 图元创建、图层管理、标注 | COM 对象生命周期管理 |
| **Tier 2** | SendCommand / SCR 脚本 | 复杂编辑（TRIM/FILLET/CHAMFER） | 异步执行、错误处理弱 |
| **Tier 3** | AutoLISP / C# .NET | 插件开发、性能敏感、批量 | LISP 调试困难；C# 需 AutoCAD .NET SDK |

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

### 十六、知识库更新记录

| 版本 | 日期 | 核心变更 | 来源 |
|:---:|------|------|------|
| v1.1.0 | 2026-06-01 | 新增铁律速查：启动清理/选择集防泄漏/三级降级/六大地雷/审计验证/SendCommand管线 | 架构优化 |
| v1.0.0 | 2026-05-24 | 初始版本，含14大章节：绘图/编辑/图层/标注/块/选择集/3D/打印/LISP/批量/AI+CAD | 知识体系构建 |
| v1.2.0 | 2026-10-07 | 新增通用零件图 COM 兼容与验证经验 | 上游版本记录 |



---
---

## 十七、冲压模具自动绘图专项流程

当用户要求“画冲压模具、落料模、冲孔模、复合模、级进模、模架、凸模、凹模、卸料板、导柱导套”时，按本流程执行。

### 17.1 先问或默认的关键参数
如果用户未给参数，可使用以下教学示意参数并明确其假设；这些数值不构成可加工、可生产设计：

| 参数 | 默认值 | 说明 |
|---|---:|---|
| 模架外形 | 500 x 360 mm | 小型冲孔/落料模 |
| 上模座厚度 | 45 mm | 装配剖视可标注 |
| 卸料板厚度 | 18 mm | 位于凸模下方 |
| 凹模板厚度 | 30 mm | 位于下模座上方 |
| 下模座厚度 | 50 mm | 基准底板 |
| 工件/冲裁轮廓 | 180 x 90 mm，R12 | 可替换为用户轮廓 |
| 冲孔 | 4 x %%c18 | 默认四孔 |
| 单边间隙 | 材厚 x 5%-8% | 未知材厚时标为“按材料复核” |
| 导柱 | 4 x %%c32 | 布置在四角 |

### 17.2 推荐图层
| 图层 | 色号 | 内容 |
|---|---:|---|
| `DIE_OUTLINE` | 7 | 模座、模板外形 |
| `DIE_WORK` | 1 | 凸模、凹模刃口、冲裁轮廓 |
| `DIE_GUIDE` | 2 | 导柱、导套、中心线 |
| `DIE_FASTENER` | 3 | 螺钉、销钉、沉孔 |
| `DIE_DIM` | 4 | 尺寸标注 |
| `DIE_TEXT` | 5 | 标题、技术要求、明细 |
| `DIE_AUX` | 8 | 构造线、基准线 |

### 17.3 自动绘图顺序
1. 创建图层、文字样式、标注样式。
2. 绘制模架总平面：上/下模座外形、凹模板、卸料板投影。
3. 绘制工作部分：冲裁轮廓、凸模轮廓、凹模刃口轮廓、冲孔。
4. 绘制导向部分：四角导柱导套、中心线和定位基准。
5. 绘制紧固定位：螺钉、销钉、沉孔符号。
6. 添加尺寸：外形尺寸、导柱距、工件中心距、孔径、刃口间隙说明。
7. 添加技术要求：材料、热处理、刃口间隙、配合研磨、未注倒角。
8. 按 CAD 版本选择无交互整理、审计和视图更新方式，保存 DWG 并回读验证。

### 17.4 L3 验证标准
冲压模具图至少要通过以下检查：

```python
required_layers = {
    "DIE_OUTLINE", "DIE_WORK", "DIE_GUIDE",
    "DIE_FASTENER", "DIE_DIM", "DIE_TEXT"
}
minimum_objects = 40
required_text = ["冲压模具", "凹模板", "凸模", "卸料板", "导柱", "技术要求"]
```

如果对象数不足、关键图层缺失、工作刃口没有闭合轮廓，必须重新生成；不能只报告“绘制成功”。

### 17.5 首次连接验证
先运行 Daihua CAD 安装目录中的 `scripts/verify_mcp.py --connect` 做只读连接验证，再在新建文档或临时副本上尝试简单图元；不要将一次连接成功视为冲压模具设计已验收。


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
