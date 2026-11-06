# 程序化二维绘图与混合交付

当任务适合批量构造规则二维几何、读取/修改普通 DXF 或由可靠尺寸重绘图片时使用。Python 生成几何可作为首选，是否启动 CAD 取决于对象与最终格式要求，不取决于电脑是否安装 AutoCAD。

## 开始前的最小检查

复用已检测的项目解释器。用该解释器检查能否 import ezdxf 及版本；没有该库时，先看现有可用工具能否可靠完成，再决定是否按任务安装到隔离环境。不要为“检查环境”启动所有 CAD 软件或列出所有 MCP 工具。一次保存输入、参数、已知尺寸及输出清单，后续只读取变化的部分。

- 新图：先确认单位、坐标原点、真实比例及所需 DXF 版本。用函数/循环表达重复几何，先计算参数，再一次创建图层、对象和标注。
- 旧 DXF：在副本上 readfile 后按句柄、图层、块名或几何定位修改目标；保留未修改内容。复杂/未知实体、动态块、代理对象、关联约束或外参不能仅凭读写未报错判为保真，必要时交给原生 CAD API。
- 旧 DWG：ezdxf 不直接读写 DWG。保留原文件；优先原生修改而非全图经 DXF 往返。确需转换时先核对工具能力与结构损失风险，转换后检查最终文件。
- 参数化三维：按实际需求使用已装 CadQuery/FreeCAD 等支持的工具，不把二维 DXF 当成三维工程实体。

## 图片重绘的尺寸依据

区分正投影线稿/扫描图与有透视的照片。明确单位、已知尺寸、标注及基准点；仅能从像素获得相对关系，不能据此编造绝对尺寸。扫描缩放、非等比拉伸和照片透视需校正并用独立已知尺寸复核；证据不足时只处理确定部分，标记待确认项，不宣称精确还原。

按轮廓、圆/弧、孔、文字、尺寸、组件建立简短对象清单；OCR 文本与关键数字应对照原图。优先恢复少量连续、几何有意义的线/弧/多段线和原生标注，避免把整幅图片机械追踪成大量短线。参照图片可保留为独立底图，但不能替代设计实体。

## 可复用最小示例

以下仅演示已明确的 100×60 mm 板、四个直径 6 mm 孔和一个原生宽度标注，不是任何客户任务的默认尺寸。有仓库时也可复用 examples/offline_plate.py。按任务改参数与验收断言，不把示例直接充当成果。

保存脚本后，以已检查的 Python 运行：python make_plate.py <工作目录>/plate.dxf。

```python
from pathlib import Path
import math
import sys
import ezdxf

out = Path(sys.argv[1]).resolve()
if out.suffix.lower() != ".dxf":
    raise ValueError("This generator writes DXF only")
if out.exists():
    raise FileExistsError(out)
out.parent.mkdir(parents=True, exist_ok=True)

doc = ezdxf.new("R2010")
doc.units = ezdxf.units.MM
for name, color in [("PLATE", 7), ("HOLES", 2), ("DIM", 1)]:
    doc.layers.new(name, dxfattribs={"color": color})
msp = doc.modelspace()
msp.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)],
                   close=True, dxfattribs={"layer": "PLATE"})
for x, y in [(10, 10), (90, 10), (90, 50), (10, 50)]:
    msp.add_circle((x, y), 3, dxfattribs={"layer": "HOLES"})
msp.add_linear_dim(base=(0, -12), p1=(0, 0), p2=(100, 0),
                   dxfattribs={"layer": "DIM"},
                   override={"dimtxt": 3, "dimasz": 2.5, "dimlfac": 1}).render()
doc.saveas(out)

saved = ezdxf.readfile(out)
result = saved.audit()  # audit may repair in memory; do not silently resave fixes
if result.has_errors or result.has_fixes:
    raise RuntimeError("DXF database needs review")
model = saved.modelspace()
outline = list(model.query('LWPOLYLINE[layer=="PLATE"]'))
holes = list(model.query('CIRCLE[layer=="HOLES"]'))
dims = list(model.query('DIMENSION[layer=="DIM"]'))
assert saved.units == ezdxf.units.MM
assert len(model) == 6 and len(outline) == 1 and outline[0].closed
assert list(outline[0].get_points("xy")) == [(0, 0), (100, 0), (100, 60), (0, 60)]
assert len(holes) == 4
assert {(c.dxf.center.x, c.dxf.center.y) for c in holes} == {(10, 10), (90, 10), (90, 50), (10, 50)}
assert all(math.isclose(c.dxf.radius, 3) for c in holes)
assert len(dims) == 1 and math.isclose(dims[0].get_measurement(), 100)
assert all(e.dxf.color == 256 and e.dxf.linetype.upper() == "BYLAYER"
           and e.dxf.lineweight == -1 for e in model)
print(f"DXF geometry and native entities verified: {out}")
```

DIMENSION 的 render() 生成显示所需的匿名块，仍保留原生尺寸实体，不能将其炸开当作最终标注。新建标注检查测量值、单位因子与显示文字，不通过覆盖数字伪造尺寸；图纸整体外观仍需按任务核对。

## 混合路线与格式转换

在批量生成前确认最终交付链是否可用：

- 只需 DXF：直接生成、回读与必要预览即可，不强制打开 AutoCAD/MCP。
- 必需 DWG：用实际可用且支持目标版本的 CAD/转换器生成，再回读检查 DWG。文件头只用于排除明显伪装，不作为完整验收；转换能力缺失时明确缺少的成果，不能仅改名或私自降为 DXF。
- 必需 PDF：用当前可用的 CAD 打印/导出，或确能满足版面与对象要求的 DXF 渲染后端。先核对字体、纸幅/比例、线宽、文字和特殊对象支持；不能保证输出一致时用原生 CAD 出图。不要为了已有简单二维任务无条件安装一整套渲染工具。
- 主体规则但有特殊内容：在独立工作文件中批量生成主体，再通过原生 CAD 补特殊对象、布局和必要转换。既有 DWG 仅引入此次所需内容，不因此整体替换原图。

转换和补充可使用 Python COM、脚本、MCP 或其他专业工具，以可靠、少往返的方案为准。无须因为“可以不用 MCP”而增加复杂转换链。

## 验证边界

从输入尺寸和对象清单独立制定断言：关键坐标/半径/弧角、闭合性、孔距、单位、原生文字与尺寸、图层归属。核对重复对象时考虑不同层、空间和合法重合，不能自动全图 OVERKILL 删除客户内容。

解析/audit 用来发现格式问题，几何断言用来检查已定义的需求，预览用于检查错位、缺字、遮挡、标注重叠和遗漏；三者不能相互替代。audit 可能修复内存文档，应记录修复并在任务副本核查后再保存。复杂对象、字体和 PDF 的显示可能因 CAD 版本不同，应明确未验证项。

若使用 audit_editable_dxf.py，它只补充严格的语义图层/实体检查，不覆盖全部尺寸和图片一致性，也不证明中间 DXF 已正确转成最终 DWG。修改后只重跑受影响检查；将最终文件放独立交付目录并实际列出文件路径。

官方参考（按需查接口，不默认完整加载）：[ezdxf 读写与实体](https://ezdxf.readthedocs.io/en/stable/usage_for_beginners.html)、[原生尺寸与渲染限制](https://ezdxf.readthedocs.io/en/stable/tutorials/linear_dimension.html)。
