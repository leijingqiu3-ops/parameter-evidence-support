# Generic Literature Workbook Schema

Use the workbook’s existing headers first. If the workbook has no usable schema, use this default:

| Column | Field | Rule |
| --- | --- | --- |
| A | 标题 | Original paper title from PDF title page/metadata/body, not filename. |
| B | 标题翻译 | Natural title translation in the output language; for Chinese output, no English residue. |
| C | 作者 | First author only unless the workbook asks for all authors. Use `未明确给出` if unreliable. |
| D | 来源 | Journal, conference, thesis type, archive, or publisher source. Use `未明确给出` if unreliable. |
| E | 创新点 / 主要贡献 | Concrete novelty, solved limitation, new method/model/data/range/validation. |
| F | 全文概要 | Background, object, problem, route, data/conditions, findings, conclusions, limitations. |
| G | 研究重点 | Key questions, variables, parameters, methods, models, benchmarks, comparisons, figures/formulas worth rereading. |
| H | 研究意义 | Academic and application value; do not duplicate action remarks. |
| I | 研究方法 | Specific experiment/theory/computation/statistics/field/data/design method, validation, uncertainty or limitations. |
| J | 备注 / 与课题关联 | Topic-specific relevance, transferable methods, risks, and next actions. |
| K | 相关度（阅读优先级） | Optional. Use `强相关` / `中等相关` / `弱相关` / blank only. |

## Header Mapping

Map common equivalents:

- 标题: `Title`, `论文题目`, `题名`
- 标题翻译: `中文题名`, `译名`, `Translated title`
- 作者: `第一作者`, `Author`, `First author`
- 来源: `期刊`, `会议`, `Journal`, `Source`, `Publication`
- 创新点: `主要贡献`, `Contribution`, `Novelty`
- 全文概要: `摘要整理`, `Summary`, `Overview`
- 研究重点: `重点`, `Key points`, `Focus`
- 研究意义: `意义`, `Value`, `Importance`
- 研究方法: `方法`, `Methods`, `Methodology`
- 备注: `启示`, `Notes`, `Remarks`, `与课题关联`
- 相关度: `阅读优先级`, `Priority`, `Relevance`

## Remarks By Relevance

High relevance:

```text
【相关度判断依据】
……

【可直接借鉴的方法/证据】
……

【对当前课题的具体启示】
……

【限制与迁移风险】
……

【后续可执行动作】
1. ……
2. ……
3. ……
```

Medium relevance:

```text
【中等相关原因】
……

【可借鉴内容】
……

【建议阅读重点】
……
```

Low relevance:

```text
该文与当前研究课题关联较弱，主要可作为背景、相邻方法或应用场景参考；不建议直接作为核心实验设计、模型验证或论证依据。
```

## Chinese-Only Rule

For Chinese workbooks, B/E/F/G/H/I/J must be Chinese-only prose. Scan those columns for `[A-Za-z]{3,}` before final delivery. Rewrite copied English evidence rather than leaving raw PDF sentences in cells.
