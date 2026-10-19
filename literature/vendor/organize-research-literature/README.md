# organize-research-literature
# 科研文献深度阅读与整理 Agent Skill

> A reusable Agent Skill for deeply reading local PDF research papers, organizing them into a structured Excel literature database, and prioritizing them by relevance to a user-defined research topic.
>
> 一个可复用的 Agent Skill，用于深度阅读本地 PDF 科研论文，将其整理为结构化 Excel 文献数据库，并根据论文与“研究课题”的相关程度进行阅读优先级排序。

---

# English

## Overview

**Organize Research Literature** is a reusable Agent Skill designed for researchers, graduate students, engineers, and academic teams who need to process a large number of PDF papers efficiently and systematically.

It does more than extract titles or translate abstracts.

The workflow is designed to deeply review each paper, extract important research information, identify methods and models, summarize key results, detect duplicates, evaluate relevance, and organize everything into a structured Excel knowledge base.

The final output helps users quickly identify:

* Which papers should be deeply read first
* Which papers are useful for methods, models, experiments, or theory
* Which papers are mainly useful for background reading
* Which papers provide actionable ideas for future research

---

## Key Features

* Recursively scans local folders and subfolders for PDF papers
* Reads full paper content instead of relying only on abstracts
* Extracts bibliographic metadata:

  * Title
  * First author
  * Journal or conference
  * Year
  * DOI
  * Keywords
  * Paper type
* Detects duplicate papers using DOI, normalized titles, author information, and file similarity
* Extracts detailed research information:

  * Research background
  * Research questions
  * Experimental setup
  * Numerical methods
  * Working fluids or materials
  * Geometry and operating conditions
  * Measurement techniques
  * Calibration methods
  * Data-processing methods
  * Equations and non-dimensional parameters
  * Models and correlations
  * Quantitative results
  * Validation methods
  * Errors and uncertainty analysis
  * Limitations and applicability ranges
* Generates structured literature summaries in Excel
* Preserves existing workbook formatting and manually written content
* Evaluates each paper according to its relevance to a user-defined research topic
* Adds color-coded reading-priority labels
* Sorts papers by relevance
* Generates actionable research notes for highly relevant papers
* Produces a CSV processing log for traceability and auditing

---

## Reading Priority System

The skill classifies papers into three relevance levels.

| Label            | Meaning                                                                                        | Reading Recommendation | Color |
| ---------------- | ---------------------------------------------------------------------------------------------- | ---------------------- | ----- |
| Strong Relevance | Directly supports the current research topic, experiment, model, measurement method, or theory | Deep read first        | Red   |
| Medium Relevance | Useful for methods, models, flow-regime criteria, engineering context, or research design      | Focused review         | Blue  |
| Weak Relevance   | Mainly useful for background, application context, or broader field understanding              | Background browsing    | Gray  |

The final Excel workbook is sorted in the following order:

```text
Strong Relevance → Medium Relevance → Weak Relevance → Manual Review
```

---

## Deep-Reading Workflow

For each paper, the Agent follows a structured workflow:

```text
1. Scan PDF files
2. Extract metadata
3. Detect duplicates
4. Read the full paper
5. Extract methods, conditions, models, figures, tables, equations, and results
6. Identify limitations and evidence pages
7. Evaluate relevance to the research topic
8. Generate structured Excel summaries
9. Add research notes and actionable recommendations
10. Assign reading-priority labels
11. Sort the Excel database by relevance
12. Generate processing logs
```

The Agent should review, whenever available:

* Title page
* Abstract
* Keywords
* Introduction
* Experimental setup
* Materials and methods
* Numerical methods
* Results and discussion
* Conclusions
* Tables
* Figures and captions
* Equations
* Appendices
* Supplementary information

---

## Typical Excel Output

The Skill can populate or update Excel columns such as:

| Field                 | Description                                                                            |
| --------------------- | -------------------------------------------------------------------------------------- |
| Title                 | Original paper title                                                                   |
| Title Translation     | Academic translation of the title                                                      |
| First Author          | First author only                                                                      |
| Journal               | Journal, conference, or thesis source                                                  |
| Innovation            | Specific contributions and novelty                                                     |
| Full Summary          | Background, methods, conditions, results, conclusions, and limitations                 |
| Research Focus        | Core questions, parameters, models, equations, and research priorities                 |
| Research Significance | Scientific and engineering value                                                       |
| Research Method       | Experimental, theoretical, numerical, measurement, calibration, and validation methods |
| Notes                 | Topic-specific insights and actionable next steps                                      |
| Relevance Priority    | Strong relevance, medium relevance, or weak relevance                                  |

---

## High-Relevance Paper Notes

For highly relevant papers, the Agent produces detailed research notes, including:

```text
[Why This Paper Is Highly Relevant]
...

[Methods That Can Be Directly Referenced]
...

[Implications for the Current Research Topic]
...

[Applicable Models and Their Validity Range]
...

[Potential Risks and Error Sources]
...

[Actionable Next Steps]
1. ...
2. ...
3. ...
```

This helps transform literature reading into practical research actions.

---

## Repository Structure

```text
.
├── SKILL.md
├── README.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── references/
│   ├── column_schema.md
│   └── research_profile_template.md
├── scripts/
│   └── research_literature_excel.py
└── installation guides/
```

---

## How to Use

Prepare the following inputs:

1. A local folder containing PDF research papers
2. An existing Excel literature-summary workbook
3. A research profile describing:

   * Current research topic
   * Research objectives
   * Experimental methods
   * Key variables
   * Relevant theories or models
   * Relevance classification criteria
   * Expected Excel output structure

Then run this Skill to:

```text
Read PDFs → Extract evidence → Generate summaries → Classify relevance → Update Excel → Sort literature → Create logs
```

---

## Outputs

After processing, the workflow produces:

1. An updated Excel literature database
2. Detailed paper summaries
3. Color-coded reading-priority labels
4. Relevance-ranked literature records
5. Actionable research notes for highly relevant papers
6. A CSV processing log containing:

   * File path
   * File name
   * Metadata
   * Duplicate status
   * Parsing status
   * Relevance level
   * Sections reviewed
   * Pages reviewed
   * Figures, tables, and equations reviewed
   * Key evidence pages
   * Failure reasons
   * Manual-review flags

---

## Use Cases

This Skill can be adapted to literature-review workflows in many fields, including:

* Fluid mechanics
* Heat transfer
* Chemical engineering
* Energy systems
* Mechanical engineering
* Materials science
* Environmental engineering
* Biomedical engineering
* Computer science
* Social sciences
* Humanities research

The research topic, output language, Excel schema, relevance criteria, and depth of reading can all be customized.

---

## Important Notes

* This Skill is designed for deep literature organization, not only abstract summarization.
* The quality of the output depends on the readability and completeness of the PDF files.
* Scanned PDFs may require OCR before full analysis.
* The Agent should not invent missing experimental conditions, equations, authors, journal information, or conclusions.
* Private PDFs, unpublished data, personal Excel files, and confidential research materials should not be uploaded to public repositories.

---

# 中文说明

## 项目简介

**Organize Research Literature** 是一个可复用的科研文献阅读与整理 Agent Skill。

它适用于需要批量阅读、整理和筛选 PDF 文献的科研人员、硕博研究生、工程师和研究团队。

它不仅仅是提取论文标题、翻译摘要，或者把 PDF 简单写进 Excel。

这个 Skill 的目标是：

* 完整阅读论文
* 提取研究方法、实验条件、理论模型、图表、公式和结果
* 识别重复论文
* 判断论文与“研究课题”的真实相关程度
* 将论文整理成结构化 Excel 知识库
* 用颜色区分哪些文章需要精读、重点浏览或背景阅读
* 为高度相关论文提供可执行的研究建议

最终得到的不是普通文献表，而是一套能够支持论文综述、实验设计、模型比较和后续研究决策的文献知识库。

---

## 核心功能

* 自动递归扫描本地文件夹及子文件夹中的 PDF 文献
* 完整阅读论文，而不是只读取标题和摘要
* 自动提取论文基础信息：

  * 标题
  * 第一作者
  * 期刊或会议名称
  * 年份
  * DOI
  * 关键词
  * 文献类型
* 自动识别重复论文
* 提取论文中的关键信息：

  * 研究背景
  * 研究问题
  * 实验装置
  * 数值方法
  * 工作流体或材料
  * 几何结构与工况
  * 测量技术
  * 标定方法
  * 数据处理方法
  * 理论模型与经验关联式
  * 重要公式与无量纲数
  * 关键图表和定量结果
  * 验证方法
  * 误差与不确定度分析
  * 研究局限性与适用范围
* 自动生成结构化 Excel 文献总结
* 保留原 Excel 表格的格式、列结构和人工填写内容
* 根据论文与研究课题的相关程度进行分类
* 自动添加红、蓝、灰三种阅读优先级标签
* 自动按照相关程度排序文献
* 对高度相关论文输出可直接用于后续研究的行动建议
* 生成 CSV 处理日志，实现可追溯和可审计的文献整理过程

---

## 阅读优先级分类

Skill 会将文献分为三类：

| 标签   | 含义                             | 阅读建议 | 颜色 |
| ---- | ------------------------------ | ---- | -- |
| 强相关  | 能够直接支持当前研究课题、实验方法、测量技术、模型或理论分析 | 优先精读 | 红色 |
| 中等相关 | 对模型、流型、实验设计、工程背景或理论分析有明显参考价值   | 重点浏览 | 蓝色 |
| 弱相关  | 主要用于背景、工程应用、综述扩展或跨领域参考         | 背景阅读 | 灰色 |

Excel 最终会按照以下顺序排列：

```text
强相关 → 中等相关 → 弱相关 → 待人工核查
```

这样可以一眼识别：

* 哪些论文必须优先精读
* 哪些论文可作为方法或理论参考
* 哪些论文主要用于背景浏览
* 哪些论文需要后续人工确认

---

## 完整阅读流程

对于每篇论文，Agent 会按照以下步骤执行：

```text
1. 扫描 PDF 文件
2. 提取论文基础信息
3. 检测重复文献
4. 完整阅读论文内容
5. 提取实验条件、测量方法、图表、公式、模型与结果
6. 提取误差来源、局限性和适用范围
7. 判断与研究课题的相关程度
8. 写入 Excel 文献总结
9. 生成研究备注和可执行建议
10. 添加阅读优先级标签
11. 根据相关度排序 Excel 文献库
12. 生成处理日志
```

对于可读取的 PDF，Agent 会尽可能阅读：

* 首页
* 摘要
* 关键词
* 引言
* 实验装置
* 材料与方法
* 数值方法
* 结果与讨论
* 结论
* 表格
* 图表与图注
* 公式
* 附录
* 补充材料

---

## Excel 输出内容

Skill 可以向 Excel 中写入或补全以下内容：

| 字段         | 内容说明                 |
| ---------- | -------------------- |
| 标题         | 论文原始标题               |
| 标题翻译       | 学术化中文标题翻译            |
| 作者         | 第一作者                 |
| 期刊         | 期刊、会议或学位论文来源         |
| 创新点        | 论文相较已有研究的具体创新        |
| 全文概要       | 研究背景、方法、工况、结果、结论与局限性 |
| 研究重点       | 核心问题、关键参数、模型、公式和研究重点 |
| 研究意义       | 科学价值与工程价值            |
| 研究方法       | 实验、理论、数值、测量、标定和验证方法  |
| 备注         | 论文对当前研究课题的具体启示与行动建议  |
| 相关度（阅读优先级） | 强相关、中等相关或弱相关         |

---

## 强相关论文的输出内容

对于强相关论文，Agent 会在备注栏中进一步生成：

```text
【相关度判断依据】
……

【可直接借鉴的方法】
……

【对当前研究课题的具体启示】
……

【可比较的理论模型与适用范围】
……

【潜在误差来源与风险提示】
……

【后续可执行动作】
1. ……
2. ……
3. ……
```

这样可以把“读论文”转化为：

* 实验设计建议
* 测量和标定思路
* 模型对比方案
* 误差控制策略
* 后续研究行动清单

---

## 仓库结构

```text
.
├── SKILL.md
├── README.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── references/
│   ├── column_schema.md
│   └── research_profile_template.md
├── scripts/
│   └── research_literature_excel.py
└── 安装与使用说明文件
```

---

## 使用方式

使用前需要准备：

1. 一个包含 PDF 文献的本地文件夹
2. 一个现有的 Excel 文献整理表格
3. 一份研究课题说明，包括：

   * 当前研究主题
   * 研究目标
   * 实验方法
   * 关键变量
   * 需要比较的理论模型
   * 文献相关度判断标准
   * Excel 输出格式

Skill 执行流程为：

```text
读取 PDF → 提取证据 → 完整总结 → 判断相关度 → 更新 Excel → 排序文献 → 输出日志
```

---

## 最终输出

执行完成后，将生成：

1. 更新后的 Excel 文献数据库
2. 按相关度排序的阅读清单
3. 红、蓝、灰颜色标记的阅读优先级
4. 每篇论文的完整中文总结
5. 强相关论文的可执行研究建议
6. CSV 处理日志，记录：

   * 文件路径
   * 文件名称
   * 论文元信息
   * 去重状态
   * PDF 解析状态
   * 相关度等级
   * 已阅读章节
   * 已阅读页码
   * 已检查的图表、表格和公式
   * 关键证据页码
   * 失败原因
   * 人工核查标记

---

## 适用领域

本 Skill 可以适用于多种科研方向，例如：

* 流体力学
* 传热传质
* 化学工程
* 能源系统
* 机械工程
* 材料科学
* 环境工程
* 生物医学工程
* 计算机科学
* 社会科学
* 人文研究

研究课题、相关度标准、Excel 表格结构、输出语言和阅读深度均可根据具体需求进行修改。

---

## 注意事项

* 本 Skill 的目标是深度整理文献，而不是简单摘要翻译。
* 输出质量取决于 PDF 是否完整、是否可以读取文字、图表和公式是否清晰。
* 扫描版 PDF 可能需要 OCR 才能完整解析。
* Agent 不应编造论文中没有出现的实验条件、公式、作者、期刊或结论。
* 建议不要将未公开论文、真实实验数据、私人 Excel 表格或含有个人信息的文件上传到公开仓库。
* 公开发布时，建议使用脱敏后的示例 Excel 文件，而不是自己的真实研究资料。

---

## License

This project is released under the MIT License.

本项目采用 MIT License 开源协议。

