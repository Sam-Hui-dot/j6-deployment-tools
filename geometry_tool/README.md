# 检测框坐标还原工具

将经过等比例缩放和补边的模型输入坐标，换算回原图。`sample`中有一个从真实J6E运行结果解码得到的数值样例，可以离线使用。

## 最短运行路径

从仓库根目录进入 `geometry_tool`，确保Python环境装有NumPy：

```bash
python -m pip install -r ../requirements.txt
python map_boxes.py --record sample/transform.json --boxes sample/model_boxes.json --output restored.json
```

这条命令使用仓库中已保存的数据，不执行模型推理。参考文件为 `sample/restored_boxes_reference.json`。选择一个未存在的输出文件名。

## 两个输入文件

### 1. 实际缩放和补边记录

工具接受直接记录，也接受样例中带 `transform` 字段的外层记录。

```json
{
  "original_hw": [363, 853],
  "target_hw": [672, 672],
  "resized_hw": [285, 672],
  "padding_ltrb": [0, 193, 0, 194],
  "scale_xy": [0.7878077373974208, 0.7851239669421488]
}
```

- `original_hw`：原图高、宽。
- `target_hw`：模型画布高、宽。
- `resized_hw`：实际缩放后高、宽，均为整数。
- `padding_ltrb`：左、上、右、下补边。
- `scale_xy`：横、纵实际比例，即 `resized_width/original_width` 与 `resized_height/original_height`。

这份记录应来自真实执行的预处理。示例函数 `transform_record` 使用本轮OE 3.9.1示例的取整与居中补边规则，不会自动识别任意其他图片变换。

### 2. 模型坐标中的检测框

JSON格式为N×4数组，每行 `[x1, y1, x2, y2]`，不含类别、分数、归一化坐标或批次维度。例如：

```json
[
  [147.46858671307564, 249.7431862950325, 368.4360153377056, 454.8112570643425]
]
```

传入的框已经完成模型输出解码和所需的筛选/NMS，本工具只做几何变换。

## 换算关系

```python
x_original = (x_model - pad_left) / scale_x
y_original = (y_model - pad_top) / scale_y
```

左右两端和上下两端都使用对应公式。坐标按连续框边界处理，计算中不取整；模型漏检、输入颜色错误等问题不由坐标工具修复。

默认保留裁剪前坐标，方便查看框是否移出画面。显示在原图上时，可以加入 `--clip`，按本轮SDK显示范围裁剪到 `[0, width-1]` / `[0, height-1]`：

```bash
python map_boxes.py --record sample/transform.json --boxes sample/model_boxes.json --output restored_clipped.json --clip
```

使用 `--forward` 可将原图坐标映射到模型画布。此时输入应是原图坐标，不要把本例的模型坐标再次正向变换；`--forward` 与 `--clip` 不能同时使用。

## Python函数接入

在能够导入 `geometry_transform.py` 的位置：

```python
from geometry_transform import transform_record, map_boxes, clip_boxes

record = transform_record([363, 853])
# 预处理按record的resized_hw和padding_ltrb执行缩放补边。
# 将本张图片的record与对应模型输出一起传给后处理。
boxes = [[147.46858671307564, 249.7431862950325,
          368.4360153377056, 454.8112570643425]]
restored = map_boxes(boxes, record, inverse=True)
display_boxes = clip_boxes(restored, record['original_hw'])
```

同一张图片的输入、输出、记录必须对应。多图处理时不要复用上一张图片的变换记录。

`map_boxes`另保留实验用的 `missing_padding`、`stretch`、`sdk_ideal` 三种逆变换对照，用于复现错误或公式差异；默认是 `recorded`，日常接入使用默认值。

## 已有检查用例

源码带有7个单元检查，覆盖横图、竖图、不对称取整、已知框、往返映射、空框及非法尺寸。需要时在本目录运行：

```bash
python -m unittest discover -p "test_*.py"
```

整理本仓库时保持核心工具与原实验版本一致，未重新执行开发板实验。板端样例来源和统计范围见[evidence/README.md](evidence/README.md)。
