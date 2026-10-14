# J6 部署实验工具

地平线征程6部署实验中的小工具、使用说明和样例。当前提供两项：**检测框坐标还原**和**固定模型回归检查**。

| 工具 | 解决什么 | 运行环境 |
|---|---|---|
| [坐标还原](geometry_tool/README.md) | 将缩放补边后的框换算回原图 | Python 3.9+、NumPy |
| [回归检查](regression_tool/README.md) | 修改程序后，对照可信基准检查模型、文件与任务结果的变化 | Python 3.11+，标准库即可 |

回归工具另附10个明确标注的**合成演示案例**，用于学习命令与报告；真实J6E实验的121例覆盖统计放在独立的[evidence目录](regression_tool/evidence/README.md)。下载仓库不会执行模型推理。

配套文章：[《检测框画偏了？把 J6 模型输出的位置还原到原图》](https://developer.horizon.auto/blog/14163)。实验于2026年10月12日在J6E MatrixB上完成，环境为OE 3.9.1、UCP 3.15.8、HBRT 4.11.11。

## 先看它解决什么

模型要求672×672输入，原照片可能是横图。预处理先缩小图片，再上下补灰边。模型返回的位置包含这些灰边，画回原图时必须先减补边、再除以缩放比例。

![缩放、补边与坐标还原示意](docs/letterbox.svg)

例如宽853、高363的原图，实际缩小为672×285，上方补193行、下方补194行。一个假设的模型纵坐标200，还原到原图约为8.9；漏减上方补边就会算成约254.7。

工具接收两个JSON文件：**实际变换记录**和**模型空间中的框**，输出原图坐标。它不执行模型推理，也不需要开发板。

## 下载与运行

可以使用Git克隆：

```bash
git clone https://github.com/Sam-Hui-dot/j6-deployment-tools.git
cd j6-deployment-tools/geometry_tool
python -m pip install -r ../requirements.txt
python map_boxes.py --record sample/transform.json --boxes sample/model_boxes.json --output restored.json
```

也可以在GitHub点击 **Code → Download ZIP**，解压后进入 `geometry_tool`，再执行安装依赖和运行命令。需要Python 3.9或更新版本，以及NumPy；实验与原样例复核使用的版本记录见[证据说明](geometry_tool/evidence/README.md)。

结果写入新的 `restored.json`。同一案例的保存参考是 `sample/restored_boxes_reference.json`。输出文件已存在时工具拒绝覆盖，第二次运行请换一个输出文件名。

## 仓库内容

| 目录/文件 | 用途 |
|---|---|
| [geometry_tool](geometry_tool/README.md) | 坐标还原命令、Python函数和完整使用说明 |
| `geometry_tool/sample` | 一组真实板端输出解码后的框、变换记录及还原参考 |
| [geometry_tool/evidence](geometry_tool/evidence/README.md) | 28个构造视图的记录、汇总统计和来源说明 |
| `geometry_tool/test_geometry_transform.py` | 横竖图、取整补边、已知坐标等已有检查用例 |
| `docs/letterbox.svg` | 本仓库绘制的流程示意 |
| [regression_tool](regression_tool/README.md) | 固定模型文件/任务结果对照检查器、真实进程捕获适配器和演示 |
| `regression_tool/demo` | 10个合成离线案例：3个正常对照、7个变化/失败案例 |
| [regression_tool/evidence](regression_tool/evidence/README.md) | 121例真实来源回放的统计、逐例覆盖表与新的板端捕获汇总 |

## 回归工具快速体验

在仓库根目录，使用Python 3.11或更新版本运行；不需要安装NumPy：

```bash
python regression_tool/regression_check.py --baseline regression_tool/demo/baseline.json --runs regression_tool/demo/normal_runs.json --report reports/demo_normal.json
python regression_tool/regression_check.py --baseline regression_tool/demo/baseline.json --runs regression_tool/demo/mixed_runs.json --report reports/demo_mixed.json
```

第一条预期3/3通过、退出0；第二条包含主动制造的错误，预期3/10通过、7例告警、退出1。这个非零退出是演示目的，查看生成的JSON报告可定位差异层。再次运行请换新报告名。

演示中的模型文件是文本占位文件，不是HBM，输入与输出也是合成字节。用于真实项目时，应换为自己的模型与经过独立核对的基准。[详细用法](regression_tool/README.md)说明了记录格式、捕获器的适配范围和真实实验来源。

## 适用范围

坐标按连续框边界处理，在换算期间保留浮点数。还原规则应与自己的真实预处理一致；缩放、裁剪、旋转或补边位置发生变化时，要同步记录对应变换。

本次实验使用8张原照片构造28个横、竖、方及不对称补边视图，保存板端输出后固定模型空间筛选/NMS，共比较111个框的逆变换。详见[实验统计](geometry_tool/evidence/README.md)。它检查的是位置换算，未用目标标注评价检测精度。

仓库包含独立工具、自有记录、数值样例与合成演示。离线工具运行不依赖OE SDK；捕获器连接真实板端程序时则需要相应程序和运行环境。COCO原照片、模型权重、HBM、SDK库及完整板端raw不包含在本仓库。

## 许可与反馈

源码、说明与自有数值记录采用[MIT许可](LICENSE)。发现与实际预处理不一致的情况，可以在Issues中附图片尺寸、缩放尺寸、补边、输入框坐标和期望坐标；提供可复现数值即可。
