# 参数文献支撑：完整使用与复现教程

这份教程面向两类使用者：

1. **直接运行脚本的人**：不安装 Codex 技能，也能按命令生成同样的 Word；
2. **在 Codex 中调用技能的人**：把本目录放进 `.codex/skills/`，用自然语言启动整个流程。

最终产物是一份中文 Word：每个参数都有分级、文献、页码、英文原句、中文核对、核验结论、可粘贴英文、本地 PDF 和原文截图。找不到的项目明确写 `【找不到】`。

---

## 0. 最短复现路径

如果你只想确认这套东西能跑，先执行：

```bash
git clone https://github.com/leijingqiu3-ops/parameter-evidence-support.git
cd parameter-evidence-support
pip install -r requirements.txt
python scripts/build_evidence_docx.py assets/example_spec.json example_report.docx
```

成功时会生成 `example_report.docx`，包含 2 个示例条目和 1 张示例截图。

> Windows 上如果 `python` 不在 PATH，请使用你的实际解释器，例如 `py -3` 或 `C:\path\to\python.exe`。
>
> macOS/Linux 通常使用 `python3`。

---

## 1. 安装

### 1.1 作为普通脚本使用

只需要 Python 3.10 或更高版本：

```bash
python --version
pip install -r requirements.txt
```

依赖：

- `python-docx`：生成 DOCX；
- `PyMuPDF`：读取 PDF、定位原句、渲染截图；
- `Pillow`：给截图加高亮和裁切。

### 1.2 作为 Codex 技能使用

把整个目录放到：

```text
~/.codex/skills/parameter-evidence-support
```

Windows 示例：

```text
C:\Users\<你的用户名>\.codex\skills\parameter-evidence-support
```

技能入口是 `SKILL.md`。安装后在 Codex 中可以直接说：

```text
使用 parameter-evidence-support，核对我正文和 SI 的全部参数。
找原始文献、下载 PDF、定位原文并截图，按固定格式生成 Word。
找不到的写【找不到】。
```

---

## 2. 建立工作目录

建议把输入、PDF、截图和输出分开：

```text
my-parameter-audit/
├─ 00_input/
│  ├─ manuscript.pdf
│  ├─ SI.pdf
│  └─ parameters.csv
├─ 01_pdfs/
├─ 02_shots/
├─ 03_output/
├─ candidates.csv
└─ spec.json
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force 00_input,01_pdfs,02_shots,03_output
```

macOS/Linux：

```bash
mkdir -p 00_input 01_pdfs 02_shots 03_output
```

---

## 3. 建立参数清单

先读正文和 SI，把每个数值列出来。建议用 CSV：

```csv
id,parameter,value,unit,equation,claim_type,current_citation
1,GATA2 half-life,27.7 ± 6.1,min,mu_G2 = ln2/t_half,measured,Minegishi 2005
2,K_G2 norm,0.30,dimensionless,Eq.(1),model_set,HSC SI
3,PU.1 Kd,7.1 ± 0.2,nM,Hill function,measured,Munde 2013
```

`claim_type` 至少区分：

- `measured`：原始论文直接测量；
- `derived`：由实验值换算；
- `model_set`：模型、归一化、扫描范围或代码常数；
- `unknown`：暂时找不到。

注意：参数核验和数据导入是两个任务。除非用户明确要求，不要把 GEO 矩阵维度、细胞数、伪时间等混进参数报告。

---

## 4. 找候选文献

```bash
python scripts/find_papers.py "GATA2 half-life P815 cycloheximide" --limit 15 --year-from 1990 --out candidates.csv
```

输出 CSV 包含标题、作者、期刊、年份、DOI、PMID、引用数和链接。脚本按引用数排序，但**引用数不是证据**，必须人工筛选。

优先顺序：

1. 原始研究论文，含 Methods 和原始数据；
2. 同一细胞类型、同一实验体系的论文；
3. 综述只作为线索，不作为“实测值”的来源；
4. 会议摘要必须标注 `abstract`。

找到 DOI/PMID 后核验元数据：

```bash
python scripts/verify_refs.py 10.1111/j.1365-2443.2005.00864.x 15966900
```

检查标题、作者、期刊、卷期、页码是否与你要引用的论文一致。一个 DOI 能打开，不代表它包含你声称的数值。

---

## 5. 下载 PDF

### 5.1 自动下载开放获取版本

```bash
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir 01_pdfs --email you@example.org
```

脚本会查询 OpenAlex、Unpaywall 和 Europe PMC，只接受真正的 `%PDF-` 文件。成功时输出文件路径和元数据。

### 5.2 没有开放获取版本

如果输出：

```text
【找不到开放获取 PDF】
```

按以下顺序处理：

1. 用学校/机构订阅在浏览器中打开出版社页面；
2. 手动下载 PDF，保存到 `01_pdfs/`；
3. 如果安装了 `nature-downloader`，可把它作为可选的机构下载层；
4. 仍然没有权限时，在报告中写 `【找不到全文】`，不要伪造截图。

**不要**绕过付费墙、CAPTCHA、Cloudflare 或 SSO。

---

## 6. 定位原句并生成截图

从 PDF 中复制一句**连续、逐字**的英文原句，然后运行：

```bash
python scripts/locate_passage.py 01_pdfs/Minegishi_2005_GenesCells_GATA2-turnover.pdf "Densitometric analyses of three independent GATA-2 immunoblots, which were normalized with the band intensity of β-actin immunoblots, showed that the half-life of endogenous GATA-2 in P815 cells was 27.7 ± 6.1 min (Fig. 1C)." --out-dir 02_shots --page 2
```

脚本对换行、PDF 断词和空格差异有容错。成功时生成：

```text
02_shots/
├─ Minegishi_2005_GenesCells_GATA2-turnover_p2_page.png
├─ Minegishi_2005_GenesCells_GATA2-turnover_p2_crop.png
└─ Minegishi_2005_GenesCells_GATA2-turnover_p2_passage.json
```

JSON 里重点看：

- `page_number`：1-based PDF 页码；
- `context`：原句前后的上下文；
- `bbox_pdf_points`：高亮区域坐标；
- `occurrences_found`：该句在 PDF 中出现几次。

如果提示 `【找不到原文】`：

- 缩短引文，只保留一句；
- 用 `--page` 限定到正确页；
- 确认是否跨页；跨页时改用其中一页的短句；
- 扫描版 PDF 没有文字层时，需要先 OCR。

如果提示 `【找不到文本层】`，说明该 PDF 是图片扫描版，不能直接定位文字。

---

## 7. 写 `spec.json`

复制示例：

```powershell
Copy-Item assets/example_spec.json .\spec.json
```

macOS/Linux：

```bash
cp assets/example_spec.json spec.json
```

每个条目至少需要这些字段：

```json
{
  "heading": "GATA2 半衰期",
  "formulas": [["t1/2 = 27.7 ± 6.1 min", "#174A6E"]],
  "citation": "Minegishi et al. 2005, Genes to Cells 10(7): 693–704",
  "journal": "Genes to Cells 2005;10(7):693–704",
  "paper_title": "Rapid turnover of GATA-2 via ubiquitin-proteasome protein degradation pathway",
  "authors": "Naoko Minegishi; Norio Suzuki; Yukie Kawatani; Ritsuko Shimizu; Masayuki Yamamoto",
  "links": "DOI 10.1111/j.1365-2443.2005.00864.x; PMID 15966900",
  "quote": "Densitometric analyses ... 27.7 ± 6.1 min (Fig. 1C).",
  "translation": "三次独立免疫印迹给出 P815 细胞内源 GATA-2 半衰期为 27.7 ± 6.1 min。",
  "url": "https://doi.org/10.1111/j.1365-2443.2005.00864.x",
  "verdict": "数值可用；不要把 0.5–1 h 写成实测范围。",
  "verdict_level": "keep",
  "english": "GATA2 is rapidly turned over, with a reported half-life of 27.7 ± 6.1 min in P815 cells.",
  "local": "Minegishi_2005_GenesCells_GATA2-turnover.pdf, PDF p.2 / journal p.694",
  "image": "02_shots/Minegishi_2005_GenesCells_GATA2-turnover_p2_crop.png",
  "image_caption": "Minegishi et al. 2005, PDF p.2；黄底为 27.7 ± 6.1 min 原句。"
}
```

`image` 可以写绝对路径，也可以写相对于 `spec.json` 的路径。

完整字段顺序、表格宽度、颜色和 schema 见：

```text
references/entry-spec.md
```

`verdict_level` 只接受：

- `keep`：可用；
- `relabel`：需要改标签；
- `rederive`：需要重算；
- `remove`：应删除；
- `missing`：找不到。

颜色规则：

- 红 `#AE3A3A`：数值/引用错误，必须改；
- 橙 `#915E0F`：模型设定或需要重标；
- 绿 `#236C4D`：已核对，可用。

---

## 8. 生成 Word

```bash
python scripts/build_evidence_docx.py spec.json 03_output/parameter_evidence_report.docx
```

成功时会输出：

```text
03_output/parameter_evidence_report.docx
entries N
```

导出 PDF：

- Word：打开 DOCX，另存为 PDF；
- LibreOffice：

```bash
libreoffice --headless --convert-to pdf --outdir 03_output 03_output/parameter_evidence_report.docx
```

---

## 9. 复现检查

逐项检查：

- 参数清单中的每一行是否只出现一次；
- A 类是否都有页码、英文原句和截图；
- B 类是否写明换算公式和输入值；
- C 类是否明确写“模型设定/代码设定”，没有伪装成实验值；
- `【找不到】` 是否说明缺什么，而不是留空；
- DOI/PMID 是否与标题、作者匹配；
- 截图是否包含 `±`、单位、图号，没有被裁掉；
- DOCX 和 PDF 的条目是否一致；
- 是否有空白页、跨页断表、孤立标题或图片裁切。

---

## 10. 让别人复现你的报告

需要共享：

1. 本仓库；
2. 你的 `spec.json`；
3. 条目中引用的截图文件；
4. 合法获得的 PDF，或明确的 DOI/页码线索；
5. 字体环境（Microsoft YaHei、Cambria）。

在同一份 `spec.json`、同一批截图和同一 Python 依赖下，生成器会复现相同的条目顺序、字体、颜色、表格、截图宽度和页脚。分页可能因 Word/LibreOffice 版本或字体缺失而略有差异。

证据本身不能脱离 PDF 复现。别人没有付费文献权限时，正确结果是 `【找不到全文】`，不是替代引用或伪造截图。

不要把没有授权的出版社 PDF 上传到 GitHub。仓库里只应放代码、模板和你有权共享的示例材料。

---

## 11. 常见问题

### `ModuleNotFoundError: No module named 'fitz'`

```bash
pip install -r requirements.txt
```

### `【找不到开放获取 PDF】`

换用机构订阅、手动下载或请求作者提供副本；不要抓取绕过付费墙的链接。

### `【找不到原文】`

缩短引文，确认页码，检查是否跨页，必要时 OCR。

### DOI 能打开但标题不对

运行：

```bash
python scripts/verify_refs.py <DOI> <PMID>
```

以标题、作者、期刊和页码为准，不要只信 DOI 可解析。

### Word 中文字体不对

安装 Microsoft YaHei；或者在不改变 house style 的前提下，由维护者统一修改 `build_evidence_docx.py` 的字体常量，不要逐条手动改。

### 图片路径找不到

`image` 相对路径是相对于 `spec.json` 所在目录解析的。把截图放在 spec 同级目录或改成绝对路径。

---

## 12. 安全边界

- 不绕过付费墙、CAPTCHA、Cloudflare、SSO；
- 不伪造 DOI、页码、原句或截图；
- 不把代码运行结果写成实验测量；
- 不把归一化阈值写成摩尔 `Kd`；
- 不把综述、摘要或会议摘要升级为原始实测；
- 找不到就写 `【找不到】` 或 `【找不到全文】`。

这套流程的目标不是“让每个数字都有引用”，而是让每个数字都能被读者核对，并且该标缺失的地方明确标缺失。