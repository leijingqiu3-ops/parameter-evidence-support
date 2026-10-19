# 怎么使用 parameter-evidence-support（小白版）

这是一个 Codex 技能的使用说明。

你不需要自己跑命令，也不需要懂 Python。你只需要把正文、SI 和输出位置告诉 Codex，再说一句明确的指令，剩下的检索、核验、截图和 Word 生成由技能完成。

---

## 这个技能帮你做什么

你给它：

- 论文正文；
- SI（补充材料）；
- 一个输出文件夹。

它帮你：

1. 从正文和 SI 中提取全部参数；
2. 判断每个参数是实测值、换算值、模型设定，还是找不到；
3. 找原始文献，核验 DOI/PMID；
4. 下载有权限的 PDF；
5. 找到文献中真正提到这个参数的句子、图或表；
6. 截取原文截图；
7. 按固定格式生成中文 Word；
8. 把找不到的内容明确写成 `【找不到】` 或 `【找不到全文】`。

---

## 第 1 步：准备文件

最好准备：

```text
D:\我的论文\
├─ 正文.pdf
└─ SI.pdf
```

Word 文件也可以。没有单独的参数表也没关系，技能会先从正文和 SI 中提取。

建议再准备一个空文件夹：

```text
D:\参数核验\
```

如果某篇文献你已经有 PDF，也可以放进一个本地文件夹，技能会优先使用。

---

## 第 2 步：确认技能已经安装

把整个 `parameter-evidence-support` 文件夹放到：

```text
C:\Users\<你的用户名>\.codex\skills\parameter-evidence-support
```

如果你已经能在 Codex 中看到这个技能，可以跳过这一步。

不确定时，直接问 Codex：

```text
你现在可以使用 parameter-evidence-support 技能吗？
```

---

## 第 2.5 步：检查内置文献栈（推荐）

这个技能已经内置了文献检索、下载和批量整理层，不需要你另外安装 `nature-downloader` 才能用学校权限下载。

让 Codex 跑一次检查：

```bash
python scripts/lit_stack.py doctor
```

你会看到四类信息：

1. Python、Node.js 是否可用；
2. Word/PDF/截图和文献整理所需的 Python 包是否齐全；
3. Chrome 远程调试代理（CDP，默认 `http://127.0.0.1:3456`）是否已经打开；
4. 内置下载器、内置 PDF 批量整理器，以及本机已安装的文献技能是否被识别。

查看完整组件清单和路径：

```bash
python scripts/lit_stack.py list
```

### 别人从 GitHub 下载后，怎么让 Codex 自动补齐文献技能

仓库地址：<https://github.com/leijingqiu3-ops/parameter-evidence-support>

核心 Word 流程不需要额外技能也能跑。缺少检索、阅读或引用适配器时，把下面这段直接发给 Codex：

```text
请使用 parameter-evidence-support 完成首次文献栈安装：
1. 运行 python scripts/lit_stack.py doctor；
2. 如果文献适配器缺失，运行 python scripts/install_literature_skills.py --install；
3. 安装完成后再次运行 doctor；
4. 安装失败的告诉我缺哪个技能、上游在哪里，不要伪造安装结果。
```

也可以自己运行：

```bash
python scripts/install_literature_skills.py --check
python scripts/install_literature_skills.py --install
```

安装器会：

- 跳过已经装好的技能；
- 从公开上游仓库下载缺失的技能；
- 需要时把 `nature-shared` 安装为 `~/.codex/skills/_shared`；
- 默认不覆盖已有技能，只有加 `--force` 才替换；
- 不索要密码、cookie 或短信验证码。

目前会自动安装的来源是：

| 技能 | 上游 |
|---|---|
| `nature-academic-search`、`nature-reader`、`nature-citation`、`nature-literature-pipeline`、`nature-shared` | `Yuan1z0825/nature-skills` |
| `literature-mapper` | `Zywang812/literature-mapper-skill` |
| `zotero-taxonomy-curator` | `ganzoth/zotero-taxonomy-curator` |

`nature-downloader` 和 `organize-research-literature` 已经内置，不需要再下载。

### 内置了什么

| 组件 | 作用 |
|---|---|
| `nature-downloader`（内置，MIT） | 用你已经登录的 Chrome / 交大 jAccount / CARSI 会话下载有权限的 PDF；遇到验证页会停下来让你本人处理 |
| `organize-research-literature`（内置，MIT） | 递归扫描本地 PDF，整理成 Excel 文献表 |
| `nature-academic-search`（本机适配） | 已安装时用于更广的多源检索、引文核验 |
| `nature-reader`（本机适配） | 已安装时用于整篇论文的中英文对照阅读 |
| `nature-citation`（本机适配） | 已安装时用于给正文找引用、导出 RIS/EndNote |
| `nature-literature-pipeline`（本机适配） | 已安装时用于每日/定期文献监控 |
| `literature-mapper`（本机适配） | 已安装时用于 arXiv + OpenAlex 的题目/摘要层面调研 |
| `zotero-taxonomy-curator`（本机适配） | 已安装时用于 Zotero 到 Obsidian 的精读笔记 |

没有安装的适配器不会影响核心流程，技能会自动回退到内置脚本。

### 第一次用交大图书馆权限

先确认 `~/.config/lit-dl/school.json` 已配置。没有配置时，可以直接让 Codex 执行：

```bash
python scripts/lit_stack.py school preset "上海交通大学"
python scripts/lit_stack.py school health --force
```

如果你的图书馆入口不是预设，改用你实际使用的电子资源入口链接：

```bash
python scripts/lit_stack.py school url "https://你的图书馆电子资源入口"
```

然后在 Chrome 里完成 jAccount / CARSI 登录，并打开 Chrome 远程调试和 CDP 代理。技能不会向你索要密码、cookie 或短信验证码。

### 用内置下载器下载一篇文献

```bash
python scripts/lit_stack.py download --doi 10.1371/journal.pcbi.1000771 --out-dir D:\参数核验\文献PDF --si
```

如果只是开放获取文献，也可以继续使用核心下载器：

```bash
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir D:\参数核验\文献PDF --email 你的邮箱
```

---

## 第 3 步：复制这段指令

把下面整段发给 Codex，只替换三个路径：

```text
使用 parameter-evidence-support 技能，核对我正文和 SI 的全部参数，
找原始文献、下载 PDF、截取原文，按固定格式生成 Word；
找不到的写【找不到】。

正文：D:\我的论文\正文.pdf
SI：D:\我的论文\SI.pdf
输出到：D:\参数核验

如果某篇文献没有访问权限，不要绕过付费墙，直接标【找不到全文】。
```

这段话已经足够启动任务。

如果你不想一次给完整路径，也可以先发：

```text
使用 parameter-evidence-support 技能，核对我正文和 SI 的全部参数，
找原始文献、下载 PDF、截取原文，按固定格式生成 Word；
找不到的写【找不到】。
```

Codex 会再问你正文、SI 和输出目录在哪里。

---

## 第 4 步：回答它的追问

技能在核对时可能会问你：

- “这个数值是实验测量，还是模型设定？”
- “这篇论文是不是你说的那一篇？”
- “这个 PDF 要不要用学校账号下载？”
- “这个参数找不到原始文献，是否保留并标 `【找不到】`？”
- “这一个是归一化阈值，还是摩尔 Kd？”

你不需要写正式答案，直接说清楚即可，例如：

```text
这个是模型设定，不是实验值。
```

```text
这篇没有全文，标【找不到全文】，不要找替代引用。
```

```text
这个 K 是归一化阈值，不能写成 Kd。
```

```text
这篇 PDF 我有，路径是 D:\文献\xxx.pdf。
```

---

## 第 5 步：它会自动做什么

技能会按这个顺序工作：

1. 读正文和 SI，列出参数清单；
2. 给每个参数分级：实测 / 换算 / 模型或代码设定 / 找不到；
3. 检索候选论文；
4. 核验 DOI、PMID、标题、作者、期刊和页码；
5. 优先下载开放获取 PDF；需要学校权限时，调用内置 `nature-downloader` 复用你已登录的 Chrome / jAccount / CARSI 会话；
6. 定位原文中的具体句子、图或表；
7. 截取包含原句的页面；
8. 如果一个参数需要两张截图（例如原句和参考文献列表），自动放进同一条目；
9. 超高截图自动缩放到页面内，并另起一页，避免图片和图注被拆开；
10. 把结果写进固定格式 Word；
11. 生成修订清单，标出必须改、建议改和可用项。

---

## 第 6 步：你最后拿到什么

通常会得到：

```text
D:\参数核验\
├─ 参数文献依据核验_完整版.docx
├─ 参数文献依据核验_完整版.pdf
├─ 原文截图\
└─ 找不到清单
```

Word 里每个参数会有：

- 参数名、公式、数值和单位；
- 文献信息；
- 英文原句；
- 中文核对；
- 核验结论；
- 可直接写进论文的英文句子；
- 本地 PDF 文件名和页码；
- 原文截图。

---

## 第 7 步：怎么检查 Word

你主要检查这几件事：

1. 正文和 SI 里的参数是否都出现了；
2. 实测值是否都有页码、原句和截图；
3. 模型设定是否明确写成“模型设定/代码设定”；
4. 红色“必须改”的项目是否处理；
5. `【找不到】` 是否说明了缺什么；
6. 截图是否包含 `±`、单位和图号，没有被裁掉；
7. 同一个参数的多张截图是否都在对应条目下，并且每张都有自己的图注；
8. 文献标题、作者、DOI 是否对得上。

你不需要逐条重做。看到问题就直接追问，例如：

```text
这个参数文献不对，按 PDF 第 2 页那句改。
```

```text
这个不是实验值，改成模型设定，并重新生成 Word。
```

```text
这个截图没有包含原句，重新截一张。
```

```text
这篇没有权限，标【找不到全文】。
```

---

## 重要规则

技能会遵守这些边界：

- 不伪造文献、页码、原句或截图；
- 不把代码运行结果写成实验测量；
- 不把归一化阈值写成摩尔 Kd；
- 不把综述、摘要或会议摘要当成原始实测；
- 不绕过付费墙、CAPTCHA、Cloudflare 或学校登录；
- 找不到就写 `【找不到】` 或 `【找不到全文】`。

## 下载失败时怎么看状态

技能不会只告诉你“下载失败”，而会区分原因：

| 状态 | 你应该做什么 |
|---|---|
| `cloudflare_challenge` | 在已登录的浏览器中打开该文献页面，手动完成人机验证，然后让 Codex 重试一次 |
| `publisher_verification` | 同上，手动完成出版社验证；不要要求自动绕过 |
| `institutional_access_required` | 使用交大图书馆 / jAccount / CARSI 会话，或标 `【找不到全文】` |
| `rate_limited` | 稍后重试 |
| `response_not_pdf` | 出版社返回的是网页而不是 PDF；需要检查落地页，不能把网页改名成 PDF |

如果看到 `【出版商验证待用户处理】`，说明文献本身可能可以获取，但当前被验证页拦住了；完成浏览器验证后可以继续，不需要重新找文献。

---

## 一句话总结

你只需要提供正文、SI、输出目录，再说：

```text
使用 parameter-evidence-support 技能，核对我正文和 SI 的全部参数，
找原始文献、下载 PDF、截取原文，按固定格式生成 Word；
找不到的写【找不到】。
```

剩下的查找、核对、截图和排版由技能完成。你负责最后检查 Word，并把不确定的地方告诉它。
