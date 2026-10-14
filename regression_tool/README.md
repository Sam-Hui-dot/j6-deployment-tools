# 固定模型回归检查工具

“回归”是重新检查已经跑通的功能。这个工具把一次当前运行的模型、输入文件、有效原始输出和任务结果，与独立核对过的基准比较，生成JSON报告并返回0或1。

需要**Python 3.11或更新版本**，只使用标准库，不安装其他依赖。离线比较不需要SDK或开发板。

## 下载后先跑演示

克隆仓库，或在GitHub点击 **Code → Download ZIP**。在仓库根目录运行：

```bash
python regression_tool/regression_check.py --baseline regression_tool/demo/baseline.json --runs regression_tool/demo/normal_runs.json --report reports/demo_normal.json
python regression_tool/regression_check.py --baseline regression_tool/demo/baseline.json --runs regression_tool/demo/mixed_runs.json --report reports/demo_mixed.json
```

| 命令 | 预期结果 | 退出码 |
|---|---|---:|
| `normal_runs.json` | 3/3通过，包含一个检测框重新排序但含义未变的案例 | 0 |
| `mixed_runs.json` | 3/10通过、7例告警 | 1 |

第二条故意包含失败案例，返回1是预期行为。报告不会覆盖已有文件，再次运行请换新报告名。

**demo中的10个案例完全是合成数据**，没有执行板端推理；模型文件是明确标注的文本占位文件，不是HBM。这里演示命令和比较规则，不能作为文章121例实测的证据。demo中填写的进程状态也是合成设置，并未执行对应进程。

`demo/expected_outcomes.json`列出每例预期告警的层：模型变化、同长度输入变化、同长度raw变化、分类名次变化、raw截短、失败状态却残留旧结果、重复检测框。正常检测框排列不同应通过。

## 六层报告分别检查什么

| 报告字段 | 检查内容 |
|---|---|
| `model` | 对实际模型文件计算SHA-256，并与基准比较 |
| `structure` | 输入/输出文件名集合、存在性和有效长度 |
| `execution` | 记录中的进程退出码是否为整数0 |
| `input` | 输入字节的SHA-256是否相同 |
| `raw` | 有效原始输出的SHA-256是否相同 |
| `result` | 规范化任务结果是否对应 |

分类结果使用 `{"top5_ids": [4, 3, 2, 1, 0]}`，按名次比较类别ID。检测结果使用 `{"boxes": [[x1, y1, x2, y2, score, class_id], ...]}`，按相同类别及前五个数的绝对差不超过1e-5做完整的一对一无序匹配；重复框不能复用同一个参考框。NaN/Inf和非整数类别值不接受。

这个1e-5是本轮固定后处理的比较容差，不是检测目标匹配用的IoU阈值。可以显式使用 `--tolerance` 调整绝对容差，修改比较标准前先核对实际数值变化。

## 换成自己的基准与运行记录

对照 `demo/baseline.json` 和 `demo/normal_runs.json` 的结构替换：

1. 固定模型与测试图片，独立核对第一次结果，再保存基准。
2. 基准保存模型真实哈希、具名输入与有效输出的长度/哈希，以及规范化任务结果。
3. 当前记录保存实际模型和产物路径、基准案例名、真实进程退出码及结果JSON路径。
4. 把 `--baseline` 和 `--runs` 指向自己的文件，用一个新的 `--report` 路径运行。

运行记录中的相对产物路径，以**runs JSON所在目录**为基准；绝对路径也接受。搬到其他机器时，要同时搬产物并改成对应路径，不能只搬一份记录。`run_id`须唯一，`baseline_case`须在基准的 `cases` 中存在。

库函数 `file_signature(Path(...))` 返回文件的长度与SHA-256，可以用来建立已核对文件的元数据。第一次基准的科学正确性仍需要独立检查；检查器不会从裸字节判断RGB是否正确。

模型更新后的哈希告警只表示变化，需要审查并明确重建基准。不要直接删除告警或自动把新输出当成参考。

## 捕获真实进程状态

`capture_cli_record.py`是本系列固定 `vision_cli.py` 图片入口的适配器。它真正启动子进程，保存退出状态、产物路径及规范化结果；**它不自动适配任意推理程序**。

使用它需要已有的图片入口、HBM、ARM执行器、图片处理依赖及匹配运行库，本仓库未打包这些板端依赖。已准备本轮接口的工程时，可运行：

```bash
python3 regression_tool/capture_cli_record.py --cli developer_kit/vision_cli.py --task classify --case classify_ILSVRC2012_val_00000073 --image image_app/images/ILSVRC2012_val_00000073.JPEG --model payload/models/resnet18.hbm --runner payload/bin/vision_runner_gcc12 --output results/new_classify --record results/new_classify.run.json
python3 regression_tool/regression_check.py --baseline regression_tool/evidence/baseline.json --runs results/new_classify.run.json --report results/new_classify.report.json
```

捕获器生成绝对路径。基准中的案例名和模型哈希必须对应自己的实际输入；上面命令是原接口的接入示例，不能只下载本仓库就执行模型。

仅读取用户填写的 `exit_code` 时，离线检查器无法独立证实它是否真实；真实状态应由捕获器或自己的执行程序记录。进程失败时，残留旧文件不会抵消非零状态。

## 真实实验资料

[evidence目录](evidence/README.md)提供121例回放的汇总、逐例覆盖CSV、固定模型基准，以及三次正常图片入口和一次缺图失败的板端捕获汇总。完整121例所依赖的模型、输入、raw文件不包含在仓库中，不能仅凭统计文件重新执行那121例。

离线demo用来学习工具，真实统计用来说明本轮覆盖范围，两者分开保存。原实验采用真实板端数据及注明来源的本地后处理变化；不是新增121次板端推理。

核心检查器和捕获器直接沿用已核对版本。原有16个检查用例一并提供，需要时在本目录运行 `python -m unittest discover -p "test_*.py"`。本次公开整理未重新执行测试或板端实验。
