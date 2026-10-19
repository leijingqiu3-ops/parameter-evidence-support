import argparse
import csv
import json
import re
import shutil
import unicodedata
from copy import copy
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

try:
    import fitz
except Exception:
    fitz = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SPACE_RE = re.compile(r"\s+")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{3,}")
RELEVANCE_LABELS = {"high": "强相关", "medium": "中等相关", "low": "弱相关"}
RELEVANCE_COLORS = {"high": "C00000", "medium": "4472C4", "low": "7F7F7F"}


def compact(value):
    return SPACE_RE.sub(" ", str(value or "")).strip()


def normalize_title(title):
    value = unicodedata.normalize("NFKD", compact(title)).lower()
    value = value.replace("&", "and")
    return re.sub(r"[\W_]+", "", value)


def normalize_doi(doi):
    doi = compact(doi).lower().rstrip(".,;)")
    return doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")


def split_terms(value):
    raw = re.split(r"[,;，；\n]+", value or "")
    return [compact(x).lower() for x in raw if len(compact(x)) >= 2]


def read_profile(path):
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def profile_terms(profile_text):
    terms = []
    for line in (profile_text or "").splitlines():
        line = compact(line.strip("-*# "))
        if not line or line.lower().startswith(("input excel", "output excel", "target sheet")):
            continue
        if len(line) <= 80:
            terms.append(line.lower())
    return terms[:80]


def scan_pdfs(root):
    out = []
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower() == ".pdf":
            out.append(path)
    return sorted(out, key=lambda p: str(p).lower())


def extract_with_fitz(path):
    if fitz is None:
        return "", [], {}, "fitz_unavailable", 0
    try:
        doc = fitz.open(path)
        meta = {k: str(v) for k, v in (doc.metadata or {}).items() if v}
        pages = [page.get_text("text") or "" for page in doc]
        count = len(doc)
        doc.close()
        return "\n\n".join(pages), pages, meta, "fitz_ok", count
    except Exception as exc:
        return "", [], {}, f"fitz_failed:{exc}", 0


def extract_with_pypdf(path):
    if PdfReader is None:
        return "", [], {}, "pypdf_unavailable", 0
    try:
        reader = PdfReader(str(path))
        meta = {str(k): str(v) for k, v in (reader.metadata or {}).items() if v}
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n\n".join(pages), pages, meta, "pypdf_ok", len(reader.pages)
    except Exception as exc:
        return "", [], {}, f"pypdf_failed:{exc}", 0


def extract_with_pdfplumber(path):
    if pdfplumber is None:
        return "", [], {}, "pdfplumber_unavailable", 0
    try:
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
        return "\n\n".join(pages), pages, {}, "pdfplumber_ok", len(pages)
    except Exception as exc:
        return "", [], {}, f"pdfplumber_failed:{exc}", 0


def extract_pdf(path):
    best = ("", [], {}, "failed", 0)
    statuses = []
    for fn in [extract_with_fitz, extract_with_pypdf, extract_with_pdfplumber]:
        text, pages, meta, status, count = fn(path)
        statuses.append(status)
        if len(text or "") > len(best[0] or ""):
            best = (text, pages, meta, ";".join(statuses), count)
        if len(text or "") >= 5000:
            break
    return best


def first_lines(text, limit=80):
    lines = []
    for line in (text or "").splitlines():
        line = compact(line)
        if line:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def likely_title_line(line):
    low = line.lower()
    bad = [
        "abstract",
        "keywords",
        "article info",
        "received",
        "accepted",
        "available online",
        "copyright",
        "journal homepage",
        "contents lists",
        "doi ",
        "http",
        "www.",
    ]
    if any(x in low for x in bad):
        return False
    if len(line) < 8 or len(line) > 220:
        return False
    if DOI_RE.search(line):
        return False
    return sum(ch.isalpha() for ch in line) >= 6


def extract_title(text, meta):
    for key in ["/Title", "title", "Title"]:
        title = compact((meta or {}).get(key))
        if likely_title_line(title):
            return title
    candidates = []
    for line in first_lines(text, 80):
        if likely_title_line(line):
            candidates.append(line)
            if len(candidates) >= 3:
                break
    if not candidates:
        return ""
    return re.sub(r"\s+", " ", " ".join(candidates)).strip(" -")[:300]


def extract_doi(text, meta):
    blob = " ".join(list((meta or {}).values())) + "\n" + (text or "")[:10000]
    match = DOI_RE.search(blob)
    return normalize_doi(match.group(0)) if match else ""


def extract_year(text, meta):
    blob = " ".join(list((meta or {}).values())) + "\n" + (text or "")[:6000]
    years = [int(m.group(0)) for m in YEAR_RE.finditer(blob)]
    years = [y for y in years if 1900 <= y <= 2100]
    return str(min(years)) if years else ""


def extract_abstract(text):
    match = re.search(
        r"\bAbstract\b\s*[:.]?\s*(.+?)(?:\n\s*(?:Keywords|Key words|1\.?\s+Introduction|Introduction|Nomenclature)\b)",
        text or "",
        re.I | re.S,
    )
    return compact(match.group(1))[:2500] if match else ""


def extract_first_author(text, title):
    lines = first_lines(text, 60)
    title_norm = normalize_title(title)
    for i, line in enumerate(lines):
        if title_norm and normalize_title(line) and normalize_title(line) in title_norm:
            for cand in lines[i + 1 : i + 8]:
                if any(x in cand.lower() for x in ["department", "university", "institute", "abstract", "received"]):
                    continue
                cand = re.split(r"[,·;]", cand)[0].strip()
                cand = re.sub(r"[*†‡\d]+", "", cand).strip()
                if 2 <= len(cand) <= 80:
                    return cand
    return "未明确给出"


def extract_source(text):
    for line in first_lines(text, 80):
        low = line.lower()
        if any(x in low for x in ["journal", "proceedings", "transactions", "conference", "letters", "science", "engineering"]):
            if len(line) <= 160 and not any(x in low for x in ["homepage", "contents lists"]):
                return line
    return "未明确给出"


def identify_paper(text, page_count):
    low = (text or "")[:5000].lower()
    if page_count <= 1 and len(text or "") < 1200:
        return False, "单页或文本过少，疑似封面/目录/附件"
    if any(x in low for x in ["editorial board", "aims and scope", "guide for authors"]):
        return False, "明显为期刊信息页或非论文正文"
    if len(text or "") < 1500 and sum(x in low for x in ["abstract", "introduction", "conclusion", "references"]) < 2:
        return False, "可读正文不足，无法确认独立论文"
    return True, ""


def classify(title, abstract, text, high_terms, medium_terms, profile_text):
    blob = f"{title}\n{abstract}\n{(text or '')[:12000]}".lower()
    title_abs = f"{title}\n{abstract}".lower()
    high_hits = [t for t in high_terms if t and t in blob]
    medium_hits = [t for t in medium_terms if t and t in blob]
    profile_hits = [t for t in profile_terms(profile_text) if len(t) >= 4 and t in title_abs]
    if high_hits:
        return "high", "命中强相关关键词：" + "；".join(high_hits[:6])
    if medium_hits or profile_hits:
        hits = medium_hits[:4] + profile_hits[:4]
        return "medium", "命中中等相关或课题画像关键词：" + "；".join(hits[:6])
    return "low", "未命中强相关或中等相关证据，按背景文献处理"


def duplicate_status(record, seen, existing):
    doi = record["doi"]
    title_norm = record["title_norm"]
    first = compact(record["first_author"]).lower()
    for prev in seen:
        if doi and doi == prev.get("doi"):
            return "duplicate", "DOI 与已扫描文件重复", prev
        if title_norm and title_norm == prev.get("title_norm"):
            return "duplicate", "标题与已扫描文件重复", prev
        sim = SequenceMatcher(None, title_norm, prev.get("title_norm", "")).ratio() if title_norm and prev.get("title_norm") else 0
        if sim > 0.93 and first and first == compact(prev.get("first_author")).lower():
            return "suspected_duplicate", f"与已扫描文件疑似重复，相似度 {sim:.3f}", prev
    for row in existing:
        if doi and doi == row.get("doi"):
            return "existing_in_excel", f"DOI 已存在于 Excel 第 {row['row']} 行", row
        if title_norm and title_norm == row.get("title_norm"):
            return "existing_in_excel", f"标题已存在于 Excel 第 {row['row']} 行", row
        sim = SequenceMatcher(None, title_norm, row.get("title_norm", "")).ratio() if title_norm and row.get("title_norm") else 0
        if sim > 0.94 and first and first == compact(row.get("first_author")).lower():
            return "suspected_duplicate", f"与 Excel 第 {row['row']} 行疑似重复，相似度 {sim:.3f}", row
    return "new", "", None


def chinese_topic(topic):
    topic = compact(topic)
    if not topic or ENGLISH_WORD_RE.search(topic):
        return "当前研究课题"
    return topic


def draft_summary(record, topic):
    topic = chinese_topic(topic)
    level = record.get("relevance_level", "low")
    partial = "当前文件未能完整解析，以下内容主要依据首页、摘要及可读取的局部内容整理。" if record.get("text_length", 0) < 5000 else ""
    title_translation = f"{topic}相关文献题名待人工精译"
    if level == "high":
        remark = f"【相关度判断依据】该文与{topic}直接相关，能够为当前研究对象、方法、模型、数据或实验设计提供核心证据。【可直接借鉴的方法/证据】后续应优先核查其方法部分、关键图表、变量定义、验证方式和局限性，提取可复用的实验、计算、统计或理论流程。【对当前课题的具体启示】可将该文作为核心文献，用于设计研究方案、比较模型或支撑综述论证。【限制与迁移风险】引用时需确认研究对象、工况、样本、数据来源和适用范围是否与当前课题一致。【后续可执行动作】1. 精读方法和结果章节。2. 摘录关键参数、公式或评价指标。3. 将可迁移方法纳入后续实验、模型或写作计划。"
    elif level == "medium":
        remark = f"【中等相关原因】该文与{topic}存在方法、理论、参数、背景或应用层面的间接联系。【可借鉴内容】可作为相邻研究背景、变量定义、模型比较或方法设计参考。【建议阅读重点】优先查看引言、方法、结论和与当前课题关键词相关的图表。"
    else:
        remark = f"该文与{topic}关联较弱，主要可作为背景、相邻方法或应用场景参考；不建议直接作为核心实验设计、模型验证或论证依据。"
    return {
        "标题": record["title"],
        "标题翻译": title_translation,
        "作者": record["first_author"],
        "来源": record["source"],
        "创新点": f"{partial}该文的主要贡献在于围绕其研究对象提出或整理了特定方法、模型、数据、实验结果或应用认识。写入正式综述前，应结合原文进一步确认其新增贡献、解决的局限、验证范围和相对于已有工作的差异。",
        "全文概要": f"{partial}论文围绕其研究主题展开，通常包括研究背景、核心问题、研究路线、数据或实验条件、主要结果和结论。当前整理已从本地文件提取题名、作者、来源、摘要和正文线索；正式使用时，应进一步核对方法、结果、图表、公式和局限性，避免把摘要性信息误写成全文结论。",
        "研究重点": f"该文的阅读重点应围绕其核心问题、关键变量、方法路径、评价指标、模型或理论依据、结果对比和局限性展开。与{topic}相关的内容应优先标记，包括可迁移的方法、可比较的数据、可引用的概念框架和需要谨慎转换的适用条件。",
        "研究意义": f"该文的意义在于为相关研究方向提供背景、方法、数据或理论支撑。对{topic}的价值取决于其研究对象、方法和证据是否能够直接迁移；若仅为相邻背景，应在综述中作为辅助文献使用，而不宜承担核心论证。",
        "研究方法": f"研究方法需回到原文方法章节逐项核查，包括研究对象、样本或材料、实验或数据来源、变量设置、仪器或模型、计算或统计方法、验证流程、误差和局限性。当前自动整理只提供保守草稿，后续应由 Codex 结合全文证据进行精读型补充。",
        "备注": remark,
    }


def load_workbook_index(path):
    wb = load_workbook(path)
    ws = wb["研究方向1"] if "研究方向1" in wb.sheetnames else wb[wb.sheetnames[0]]
    existing = []
    for row in range(2, ws.max_row + 1):
        title = compact(ws.cell(row, 1).value)
        if not title:
            continue
        existing.append(
            {
                "row": row,
                "title": title,
                "title_norm": normalize_title(title),
                "first_author": compact(ws.cell(row, 3).value),
                "source": compact(ws.cell(row, 4).value),
                "doi": "",
            }
        )
    return wb, ws, existing


def ensure_headers(ws, mark_relevance):
    defaults = {
        1: "标题",
        2: "标题翻译",
        3: "作者",
        4: "来源",
        5: "创新点",
        6: "全文概要",
        7: "研究重点",
        8: "研究意义",
        9: "研究方法",
        10: "备注",
    }
    for col, header in defaults.items():
        if not compact(ws.cell(1, col).value):
            ws.cell(1, col).value = header
    if mark_relevance and not compact(ws.cell(1, 11).value):
        ws.cell(1, 11).value = "相关度（阅读优先级）"
    return {
        "标题": 1,
        "标题翻译": 2,
        "作者": 3,
        "来源": 4,
        "创新点": 5,
        "全文概要": 6,
        "研究重点": 7,
        "研究意义": 8,
        "研究方法": 9,
        "备注": 10,
    }


def copy_row_style(ws, source_row, target_row, max_col=11):
    for col in range(1, max_col + 1):
        src = ws.cell(source_row, col)
        dst = ws.cell(target_row, col)
        if src.has_style:
            dst._style = copy(src._style)
        dst.number_format = src.number_format
        dst.font = copy(src.font)
        dst.fill = copy(src.fill)
        dst.border = copy(src.border)
        dst.alignment = copy(src.alignment)
        dst.protection = copy(src.protection)
    if ws.row_dimensions[source_row].height:
        ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height


def write_relevance(ws, row, level):
    if level not in RELEVANCE_LABELS:
        return
    cell = ws.cell(row, 11)
    if compact(cell.value):
        return
    cell.value = RELEVANCE_LABELS[level]
    cell.fill = PatternFill(fill_type="solid", fgColor=RELEVANCE_COLORS[level])
    cell.font = Font(color="FFFFFF", bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.column_dimensions["K"].width = max(ws.column_dimensions["K"].width or 0, 17)


def sort_by_relevance(ws):
    weights = {"强相关": 1, "中等相关": 2, "弱相关": 3, "": 4}
    max_col = ws.max_column
    rows = []
    for row in range(2, ws.max_row + 1):
        cells = []
        for col in range(1, max_col + 1):
            cell = ws.cell(row, col)
            cells.append((cell.value, copy(cell._style), cell.number_format, copy(cell.font), copy(cell.fill), copy(cell.border), copy(cell.alignment)))
        rows.append((weights.get(compact(ws.cell(row, 11).value), 4), row, cells, ws.row_dimensions[row].height))
    rows.sort(key=lambda x: (x[0], x[1]))
    for target, (_, _, cells, height) in enumerate(rows, start=2):
        if height:
            ws.row_dimensions[target].height = height
        for col, saved in enumerate(cells, start=1):
            value, style, number_format, font, fill, border, alignment = saved
            cell = ws.cell(target, col)
            cell.value = value
            cell._style = copy(style)
            cell.number_format = number_format
            cell.font = copy(font)
            cell.fill = copy(fill)
            cell.border = copy(border)
            cell.alignment = copy(alignment)


def process(args):
    root = Path(args.root)
    input_excel = Path(args.input_excel)
    output_excel = input_excel if args.in_place else Path(args.output_excel)
    log_csv = Path(args.log_csv)
    cache_json = Path(args.cache_json) if args.cache_json else output_excel.with_suffix(".cache.json")
    profile_text = read_profile(args.profile)
    topic = args.topic or "当前研究课题"
    high_terms = split_terms(args.high_keywords)
    medium_terms = split_terms(args.medium_keywords)
    if not high_terms and profile_text:
        high_terms = profile_terms(profile_text)[:20]
    add_levels = {"high"} if args.high_only and not args.include_medium_low else {"high", "medium", "low"}

    if args.in_place:
        backup = input_excel.with_name(f"{input_excel.stem}_backup_before_research_literature_{datetime.now().strftime('%Y%m%d_%H%M%S')}{input_excel.suffix}")
        shutil.copy2(input_excel, backup)
    else:
        backup = ""
        shutil.copy2(input_excel, output_excel)

    wb, ws, existing = load_workbook_index(output_excel)
    cols = ensure_headers(ws, args.mark_relevance)
    pdfs = scan_pdfs(root)
    records = []
    logs = []
    seen = []

    for path in pdfs:
        text, pages, meta, status, page_count = extract_pdf(path)
        paper_ok, failure = identify_paper(text, page_count)
        title = extract_title(text, meta) if paper_ok else ""
        doi = extract_doi(text, meta)
        abstract = extract_abstract(text)
        first_author = extract_first_author(text, title) if title else "未明确给出"
        source = extract_source(text)
        year = extract_year(text, meta)
        record = {
            "file_path": str(path),
            "file_name": path.name,
            "folder": str(path.parent),
            "file_size_mb": round(path.stat().st_size / 1024 / 1024, 3),
            "page_count": page_count,
            "text_extraction_status": status,
            "paper_identified": bool(paper_ok and title),
            "title": title,
            "title_norm": normalize_title(title),
            "doi": doi,
            "first_author": first_author,
            "source": source,
            "year": year,
            "abstract": abstract,
            "text_length": len(text or ""),
            "failure_reason": failure,
        }
        if not record["paper_identified"]:
            record["duplicate_status"] = "skipped"
            record["relevance_level"] = "unreadable_or_manual_review"
            record["duplicate_reason"] = ""
            record["excel_action"] = "skipped"
        else:
            level, evidence = classify(title, abstract, text, high_terms, medium_terms, profile_text)
            record["relevance_level"] = level
            record["relevance_evidence"] = evidence
            dup, reason, match = duplicate_status(record, seen, existing)
            record["duplicate_status"] = dup
            record["duplicate_reason"] = reason
            record["duplicate_match"] = match
            record["summary"] = draft_summary(record, topic)
            if dup in {"new", "suspected_duplicate"}:
                seen.append(record)
            action = "skipped"
            row = ""
            if dup == "new" and record["relevance_level"] in add_levels and not args.fill_blanks_only:
                row = ws.max_row + 1
                copy_row_style(ws, max(2, ws.max_row), row, max_col=max(11, ws.max_column))
                for field, col in cols.items():
                    ws.cell(row, col).value = record["summary"].get(field, "")
                    if col >= 5:
                        ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
                if args.mark_relevance:
                    write_relevance(ws, row, level)
                action = "added"
            elif dup == "existing_in_excel" and not args.only_new and isinstance(match, dict):
                row = match["row"]
                changed = False
                for field, col in cols.items():
                    cell = ws.cell(row, col)
                    if not compact(cell.value) and compact(record["summary"].get(field)):
                        cell.value = record["summary"][field]
                        if col >= 5:
                            cell.alignment = Alignment(wrap_text=True, vertical="top")
                        changed = True
                if args.mark_relevance:
                    before = compact(ws.cell(row, 11).value)
                    write_relevance(ws, row, level)
                    changed = changed or before != compact(ws.cell(row, 11).value)
                action = "updated_blank_cells" if changed else "skipped"
            record["excel_action"] = action
            record["excel_row"] = row
        logs.append(record)
        records.append(record)

    if args.sort_by_relevance and args.mark_relevance:
        sort_by_relevance(ws)
    wb.save(output_excel)
    wb.close()

    fieldnames = [
        "file_path",
        "file_name",
        "folder",
        "file_size_mb",
        "page_count",
        "text_extraction_status",
        "paper_identified",
        "title",
        "doi",
        "first_author",
        "source",
        "year",
        "duplicate_status",
        "duplicate_reason",
        "excel_action",
        "excel_row",
        "relevance_level",
        "relevance_evidence",
        "failure_reason",
        "processed_at",
    ]
    now = datetime.now().isoformat(timespec="seconds")
    with log_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in logs:
            writer.writerow({k: (now if k == "processed_at" else row.get(k, "")) for k in fieldnames})
    cache_json.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return output_excel, log_csv, cache_json, backup, records


def verify(path):
    wb = load_workbook(path)
    ws = wb["研究方向1"] if "研究方向1" in wb.sheetnames else wb[wb.sheetnames[0]]
    residues = []
    blank_titles = []
    invalid_labels = []
    for row in range(2, ws.max_row + 1):
        if not compact(ws.cell(row, 1).value):
            blank_titles.append(row)
        for col in [2, 5, 6, 7, 8, 9, 10]:
            value = ws.cell(row, col).value
            if value and ENGLISH_WORD_RE.search(str(value)):
                residues.append((row, col))
        label = compact(ws.cell(row, 11).value)
        if label and label not in {"强相关", "中等相关", "弱相关"}:
            invalid_labels.append((row, label))
    result = {
        "sheetnames": wb.sheetnames,
        "max_row": ws.max_row,
        "max_column": ws.max_column,
        "blank_title_rows": blank_titles,
        "english_residue_cells_B_E_to_J": len(residues),
        "invalid_relevance_labels": invalid_labels[:10],
        "k_header": ws.cell(1, 11).value,
    }
    wb.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="Generic offline PDF literature organizer for research-topic Excel workbooks.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--input-excel", required=True)
    parser.add_argument("--output-excel", default=None)
    parser.add_argument("--log-csv", default=None)
    parser.add_argument("--cache-json", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--topic", default="当前研究课题")
    parser.add_argument("--high-keywords", default="")
    parser.add_argument("--medium-keywords", default="")
    parser.add_argument("--only-new", action="store_true")
    parser.add_argument("--fill-blanks-only", action="store_true")
    parser.add_argument("--high-only", action="store_true")
    parser.add_argument("--include-medium-low", action="store_true")
    parser.add_argument("--mark-relevance", action="store_true")
    parser.add_argument("--sort-by-relevance", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    input_excel = Path(args.input_excel)
    if args.in_place:
        args.output_excel = str(input_excel)
    elif not args.output_excel:
        args.output_excel = str(input_excel.with_name(f"{input_excel.stem}_整理完成{input_excel.suffix}"))
    if not args.log_csv:
        args.log_csv = str(Path(args.root) / "research_literature_processing_log.csv")

    output_excel, log_csv, cache_json, backup, records = process(args)
    report = {
        "pdf_total": len(records),
        "paper_identified": sum(1 for r in records if r.get("paper_identified")),
        "main_text_extracted": sum(1 for r in records if r.get("text_length", 0) >= 8000),
        "added": sum(1 for r in records if r.get("excel_action") == "added"),
        "updated": sum(1 for r in records if r.get("excel_action") == "updated_blank_cells"),
        "duplicates": sum(1 for r in records if r.get("duplicate_status") in {"duplicate", "existing_in_excel"}),
        "suspected_duplicates": sum(1 for r in records if r.get("duplicate_status") == "suspected_duplicate"),
        "relevance": {
            "high": sum(1 for r in records if r.get("relevance_level") == "high"),
            "medium": sum(1 for r in records if r.get("relevance_level") == "medium"),
            "low": sum(1 for r in records if r.get("relevance_level") == "low"),
            "manual_review": sum(1 for r in records if r.get("relevance_level") == "unreadable_or_manual_review"),
        },
        "backup": str(backup) if backup else "",
        "output_excel": str(output_excel),
        "log_csv": str(log_csv),
        "cache_json": str(cache_json),
        "verification": verify(output_excel),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
