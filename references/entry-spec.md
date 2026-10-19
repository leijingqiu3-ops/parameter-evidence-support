# Entry specification

## Page and typography

| Item | Value |
|---|---|
| Page | A4 (21.0 x 29.7 cm) |
| Margins | top 2.0, bottom 1.9, left 2.2, right 2.2 cm |
| Body | Microsoft YaHei, 10.5 pt, line spacing 1.28 |
| Latin/numerals | Cambria where mixed with Chinese |
| Heading 1 | 16 pt, `#174A6E`, space before 16 pt |
| Heading 2 | 12.5 pt, `#233F54`, space before 12 pt |
| Body colour | `#1F2937` |
| Muted colour | `#5B6770` |
| Accent light | `#EAF1F6` |
| Quote block | fill `#F4F8FA`, left rule `#174A6E`, 9.6 pt |
| Screenshot | 16.4 cm wide by default; height capped at 20 cm; images taller than 9 cm start a new page; caption 8.8 pt muted; no crop of the sentence |
| Footer | document title + PAGE field, 8.5 pt muted |
| Table | header `#174A6E` white bold; body 8.8–9.6 pt; repeat header row |

## Fixed order inside one entry

1. **Heading 2**: `N. 参数名`
2. **Formula line(s)**: symbol = value/definition; red if the value is missing or internally inconsistent.
3. **Citation line** (bold 10.6 pt): first author, year, journal, volume(issue): pages, DOI.
4. **Journal line**: journal + year + pages; append `（无外部实验论文）` for class C.
5. **论文标题：** exact title.
6. **作者：** full author list, `;` separated.
7. **链接类信息：** DOI, PMID, PMCID, publisher/PubMed URL.
8. **Quote block label**: `文献提及这个参数取值的正文段落：`
9. **Verbatim English quote** (one sentence; use `…` only to omit irrelevant clauses).
10. **中文核对：** literal translation plus the unit conversion.
11. **论文网页链接：** clickable DOI/URL, or `无外部实验论文；定义见……`.
12. **核验结论与建议改法：** verdict, coloured red/amber/green.
13. **可直接写入论文的英文表述：** one paste-ready sentence.
14. **本地 PDF：** filename + PDF page + journal page, or `【找不到全文】`.
15. **原文截图：** one or more images + captions naming paper, page, and what is highlighted.

For class C entries, fields 5–7 use:

- 论文标题：the model/definition name;
- 作者：`本模型作者`;
- 链接类信息：`HSC 正文 p.X；SI p.Y`.

## Evidence colour rules

| Colour | When |
|---|---|
| Red `#AE3A3A` | value is wrong, unsupported, or missing; must change |
| Amber `#915E0F` | value is a model choice or operational range; relabel |
| Green `#236C4D` | value is verified against a primary source; keep |

## JSON schema

```json
{
  "title": "HSC 模型参数文献依据核验与修订建议",
  "subtitle": "按参数表逐项核对原始论文；页码指已核查 PDF 页，另注期刊页",
  "intro": "……",
  "grades": [
    ["A", "原始论文直接实测", "例：GATA2 27.7 ± 6.1 min"],
    ["B", "由实验值或比值换算", "例：μ = ln2 / t½"],
    ["C", "模型、数值协议或代码设定", "例：K_G2norm = 0.30"]
  ],
  "reading_notes": ["……"],
  "revision_summary": [
    {"priority": "必须改", "items": ["……", "……"]},
    {"priority": "建议改", "items": ["……"]}
  ],
  "sections": [
    {
      "heading": "A. 降解与半衰期参数",
      "entries": [
        {
          "heading": "GATA2 半衰期与 μ_G2",
          "formulas": [["t₁/₂ = 27.7 ± 6.1 min", "#174A6E"]],
          "citation": "Minegishi et al. 2005, Genes to Cells 10(7): 693–704",
          "journal": "Genes to Cells 2005;10(7):693–704",
          "doi": "10.1111/j.1365-2443.2005.00864.x",
          "pmid": "15966900",
          "paper_title": "Rapid turnover of GATA-2 via ubiquitin-proteasome protein degradation pathway",
          "authors": "Naoko Minegishi; Norio Suzuki; Yukie Kawatani; Ritsuko Shimizu; Masayuki Yamamoto",
          "links": "DOI 10.1111/...; PMID 15966900",
          "quote": "Densitometric analyses … showed that the half-life of endogenous GATA-2 in P815 cells was 27.7 ± 6.1 min (Fig. 1C).",
          "translation": "……",
          "url": "https://doi.org/10.1111/j.1365-2443.2005.00864.x",
          "verdict": "……",
          "verdict_level": "keep",
          "english": "GATA2 is rapidly turned over, with a reported half-life of 27.7 ± 6.1 min in P815 cells.",
          "local": "Minegishi_2005_GenesCells_GATA2-turnover.pdf, PDF p.2 / journal p.694",
          "image_width_cm": 16.4,
          "image_max_height_cm": 20.0,
          "image_page_break": "auto",
          "images": [
            {
              "path": "03_原文截图/01_GATA2_27.7min_Minegishi_p2.png",
              "caption": "Minegishi et al. 2005, PDF p.2；黄底为 27.7 ± 6.1 min 原句。"
            }
          ]
        }
      ]
    }
  ],
  "not_found": [
    {
      "reference": "Zhang & Watson 2005, J Biochem",
      "missing": "FLI1 p51/p48 的图和实验条件",
      "status": "【找不到全文】出版社全文无法获取；仅 PubMed 摘要明确 105/80 min。",
      "url": "https://doi.org/10.1093/jb/mvi032"
    }
  ],
  "files": ["已到位的核心 PDF……"],
  "advice": ["优先改……", "其次改……"]
}
```

`verdict_level` accepts `keep`, `relabel`, `rederive`, `remove`, `missing`; the builder maps them to green/amber/red.

## Screenshot controls

| Field | Default | Meaning |
|---|---|---|
| `images` | none | Ordered list of screenshot objects. Use this when one parameter needs a quote page plus a reference page, a figure, or a table. |
| `images[].path` | required | Absolute path or path relative to the JSON file. |
| `images[].caption` | empty | Caption placed directly below that image. |
| `images[].width_cm` | `image_width_cm` / 16.4 | Preferred display width. |
| `images[].max_height_cm` | `image_max_height_cm` / 20.0 | Maximum display height; width is reduced proportionally if needed. |
| `images[].page_break` | `image_page_break` / `auto` | `true`, `false`, or `auto`. `auto` starts a new page when the displayed image is taller than `image_page_break_height_cm`. |
| `image_width_cm` | 16.4 | Entry-level default width. |
| `image_max_height_cm` | 20.0 | Entry-level default height cap. |
| `image_page_break_height_cm` | 9.0 | Threshold for automatic page breaks. |

Backward-compatible single-image fields `image` and `image_caption` remain supported. If neither `images` nor `image` is present, the builder prints a visible `【找不到截图】` line instead of leaving a silent gap. A tall screenshot is automatically moved to a fresh page and kept with its caption; this prevents Word from leaving an orphan caption at the bottom of the previous page.
