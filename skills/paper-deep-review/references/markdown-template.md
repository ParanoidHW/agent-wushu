# Markdown Paper Review Template

Use this template for Chinese paper-review deliverables. Adapt headings when the user gives a stricter format, but preserve the evidence discipline.

```markdown
# <Paper Title> 精读分析

> 资料状态：说明 PDF/LaTeX/source/code 是否存在；说明图片来自原始素材还是 PDF 截图裁剪。

## 0. 资料与配图索引

- 论文：`<path>`
- 源码/LaTeX：`<path or unavailable>`
- 开源代码：`<repo url>`, commit `<hash>`
- 提取文本：`<path>`
- 图表：列出 Figure/Table 与本地图片路径。

## 1. 论文基本信息

- 研究领域：
- 核心问题：
- 研究目标：
- 关键约束/假设：

## 2. 核心贡献与创新点

列出 3-5 个贡献。每个贡献说明：
- 解决什么问题
- 与已有方法的差异
- 证据来源：Section/Figure/Table

## 3. 研究方法

### 3.1 问题到方案的逻辑链

用简洁链条说明：问题 -> 约束 -> 方法设计 -> 预期收益。

### 3.2 模型/系统架构

嵌入关键示意图。

### 3.3 关键公式

使用 LaTeX：

$$
<formula>
$$

解释公式中的变量、单位、系统含义。

### 3.4 训练/实验/部署设计

说明数据、baseline、公平性设置、指标、实现假设。

## 4. 关键结论

### 4.1 主结果

嵌入主表/主图，说明：
- 指标是什么
- 数字来自哪里
- 结论如何由数据推出

### 4.2 消融和机制证据

按 Figure/Table 解释，避免只复述 caption。

### 4.3 是否验证了假设

逐条对应论文假设、方法设计和实验结果。

## 5. Related Work 对比

| 类别/论文 | 方法核心 | 优点 | 局限 | 与本文关系 |
|---|---|---|---|---|
| <work> | <mechanism> | <benefit> | <limit> | <contrast> |

## 6. Infra 需求分析

分开写 paper-reported facts 与 inferred estimates。

### 6.1 算力

给出 FLOPs/latency/throughput 公式。

### 6.2 显存与存储

给出参数量、activation、cache、数据缓存公式。

### 6.3 带宽与互联

给出通信量公式：

$$
\mathrm{Bytes}=<formula>
$$

### 6.4 调度/Serving/自定义算子

说明 runtime、batching、scheduler、kernel、KV cache、CUDA graph 等需求。

## 7. 开源代码对照

- 仓库：
- commit：
- 代码范围：

| 论文机制 | 本地路径 | GitHub commit 链接 | 一致性判断 |
|---|---|---|---|
| <mechanism> | `<path>` | `<url>` | 一致/部分一致/未开源 |

明确说明 paper 技术细节不清楚时，源码如何补充；源码未覆盖时，不要过度推断。

## 8. 优点与局限

### 优点

### 局限

### 可改进之处

## 9. 研究启发

- 可借鉴思路：
- 可延伸方向：
- 可复现实验：

## 10. 解读问题/待验证清单

这些问题用于后续复读、复现或组会讨论：

1. 论文真正优化的目标函数是什么？指标是否和目标一致？
2. 关键假设是否被实验直接验证，还是只被间接支持？
3. baseline 是否公平，是否同数据、同预算、同指标？
4. 主结果是否依赖某个特定数据域、模型规模或系统负载？
5. 消融是否足以证明每个模块必要？
6. 公式中的概率、吞吐、显存或带宽估计是否有隐含单位和边界条件？
7. 论文声称的生产结果是否有足够 telemetry、SLA、负载说明？
8. 开源代码是否实现了论文核心算法，还是只实现训练/评测子集？
9. 哪些关键细节无法从论文或代码确认？
10. 如果要复现，最小闭环需要哪些数据、模型、硬件和脚本？

## 11. 一句话总结

用 1-2 句话说明本文最核心价值和最大不确定性。
```
