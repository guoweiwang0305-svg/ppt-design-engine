# GCL × AIA 35 页视觉专家初评报告（2026-11-19）

## 状态与边界

- 35/35 页已完成 GPT-6 视觉专家初评：先评 GCL 16 页，再评 AIA 19 页。
- 本轮是 AI 辅助的**暂定专家基准**，不是独立人类专家最终金标准；正式准确率评测前，建议设计专家复核争议项。
- 本轮尚未执行独立视觉模型 API 批量推理：仓库没有配置视觉模型服务端点、模型版本或访问凭据。因此不虚构模型输出，也不计算伪造的 FP/FN。
- 本轮结果可用于产品设计规则校准；接入固定 provider/model 后再执行模型对照评测。

## 结果概览

| 系列 | 页数 | 有问题页面 | 问题标签数 |
|---|---:|---:|---:|
| GCL | 16 | 12 | 22 |
| AIA | 19 | 12 | 16 |

## 问题标签分布

- `information_overcrowded`: 16
- `chart_label_unreadable`: 13
- `style_inconsistent`: 3
- `chart_encoding_unclear`: 2
- `contrast_insufficient`: 1
- `decorative_noise`: 1
- `narrative_focus_unclear`: 1
- `weak_visual_hierarchy`: 1

## 系列 × 页面类型

| 页面类型 | 页面数 | 有问题页面 | 问题标签数 |
|---|---:|---:|---:|
| GCL · cover | 1 | 0 | 0 |
| GCL · image_led | 1 | 1 | 2 |
| GCL · chart | 2 | 2 | 3 |
| GCL · map_infographic | 1 | 0 | 0 |
| GCL · data_dashboard | 1 | 1 | 1 |
| GCL · comparison_table | 1 | 1 | 2 |
| GCL · ranking_table | 1 | 1 | 2 |
| GCL · matrix | 2 | 2 | 3 |
| GCL · taxonomy | 1 | 1 | 2 |
| GCL · process | 2 | 1 | 2 |
| GCL · ecosystem | 1 | 0 | 0 |
| GCL · image_led_infographic | 1 | 1 | 2 |
| GCL · dashboard | 1 | 1 | 3 |
| AIA · image_led | 4 | 2 | 3 |
| AIA · chart | 5 | 3 | 4 |
| AIA · data_table | 1 | 1 | 2 |
| AIA · matrix | 4 | 3 | 4 |
| AIA · process | 3 | 2 | 2 |
| AIA · image_led_infographic | 1 | 1 | 1 |
| AIA · closing | 1 | 0 | 0 |

## GCL 风格基准初步结论

1. 主色以品牌红、白、炭灰和中性灰为主；红色承担标题、关键数据和流程强调，不应被随机蓝色批注破坏。
2. 标题位置与标题红色应保持跨页一致；蓝色编辑批注应从交付稿剥离，不能进入风格模板。
3. 关键数字与图表优先于说明文字；图表标签、脚注、双语说明不得低于投影可读阈值。
4. 多列矩阵/流程页需要限制卡片数量和卡片内文；密度过高应拆页，不以缩小字体解决。
5. 截图、图表、流程要服务单一结论；占位黑块、无意义图标和装饰噪声应作为缺陷处理。

## AIA 信息组织与图示结构基准初步结论

1. 可沉淀为通用结构的模式：双图趋势比较、饼图+指标拆解、中心辐射/分类、树状分解、金字塔分层、阶段流程、人物图片+数据论证。
2. 图示必须显式表达关系维度；三维透视图若轴向和分类映射不清，应改为二维矩阵或分层表。
3. 图表注释应移出绘图区，避免覆盖数据线和关键标记。
4. 表格/金字塔/多维图需控制单元格字数与注释密度，必要时拆分“结论页”和“证据页”。
5. AIA 暖金/米色仅作为该来源风格特征，不迁移到 GCL 品牌样式。

## 产品规则建议

- GCL Profile：品牌色约束、标题/页眉一致性、批注色清理、图表标签最小字号、密度超限拆页。
- Information Design Rules：图表注释避让绘图区、关系类型与图示语法匹配、流程方向明确、矩阵轴定义完整、表格字号与行距检查。
- Visual Critic：将 `chart_label_unreadable`、`information_overcrowded`、`chart_encoding_unclear` 分成独立检测器，避免一个总分掩盖具体错误。

## 下一步

1. 设计专家复核已标记页及未标记页抽样。
2. 配置固定视觉模型 endpoint，固定 provider/model、system prompt、输入尺寸、温度和输出 schema。
3. 同一模型跑完 35 页，保存原始响应；用 `score-visual-benchmark` 计算总体、系列、页面类型和问题码维度的 FP/FN、Precision、Recall、F1。
4. 分别针对 FP 最高和 FN 最高的页面类型优化，每轮只改一类因素，再完整重跑 35 页。
