# Nankai Notice Watch v1 — SOURCE_AUDIT

**Purpose:** Phase A execution contract.  
**Critical rule:** Audit first; production implementation later.

## 1. Objective

Live-test all 43 candidate Sources plus the three site entry pages. The audit must answer:

1. Does the Source exist and resolve?
2. Is it a genuine time-series list source?
3. Is content available in server-rendered HTML?
4. Can title/date/link be extracted reliably?
5. What is the pagination contract?
6. What constitutes stable notice identity?
7. Is the Source empty by design?
8. Does it duplicate another Source?
9. Does the site expose additional in-scope sources that the baseline missed?
10. Can a representative offline fixture reproduce the parser?

Phase A must **not** build the final monitor.

## 2. Entry sites

Start navigation discovery from:

```text
https://physics.nankai.edu.cn/
https://jwc.nankai.edu.cn/
https://nkzbb.nankai.edu.cn/
```

Discovery is audit-only. It may identify new candidates, but must never auto-enable them.

Stay on the same host. External subdomains are reported as out-of-scope links.

## 3. Baseline Source list

Every row below must receive an audit record. A missing/redirected Source is still an audit result and must never be silently skipped.

| ID | Site | Name | Candidate URL | Type | allow_empty baseline |
|---|---|---|---|---|---|
| P01 | physics | 通知公告 | `https://physics.nankai.edu.cn/572/list.htm` | notice | no |
| P02 | physics | 本科生教育 | `https://physics.nankai.edu.cn/574/list.htm` | education | no |
| P03 | physics | 研究生教育 | `https://physics.nankai.edu.cn/576/list.htm` | education | no |
| P04 | physics | 学术活动/讲座 | `https://physics.nankai.edu.cn/573/list.htm` | academic_event | no |
| P05 | physics | 本科招生 | `https://physics.nankai.edu.cn/bkzs/list.htm` | admission | yes |
| P06 | physics | 硕士招生 | `https://physics.nankai.edu.cn/sszs/list.htm` | admission | no |
| P07 | physics | 博士招生 | `https://physics.nankai.edu.cn/bszs/list.htm` | admission | no |
| P08 | physics | 博士后 | `https://physics.nankai.edu.cn/bsh/list.htm` | recruitment | yes |
| P09 | physics | 科研动态 | `https://physics.nankai.edu.cn/dbxkycg/list.htm` | research_mixed | no |
| J01 | jwc | 通知公告 | `https://jwc.nankai.edu.cn/tzgg/list.htm` | notice | no |
| J02 | jwc | 课程建设·工作动态 | `https://jwc.nankai.edu.cn/gzdt/list.htm` | teaching_management | no |
| J03 | jwc | 专业建设·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36062/list.htm` | teaching_management | no |
| J04 | jwc | 通识选修课·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36064/list.htm` | teaching_management | no |
| J05 | jwc | 推免研究生·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36067/list.htm` | student_affairs | no |
| J06 | jwc | 毕业论文·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36069/list.htm` | student_affairs | no |
| J07 | jwc | 学科竞赛·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36071/list.htm` | student_affairs | no |
| J08 | jwc | 创新创业·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36073/list.htm` | student_affairs | yes |
| J09 | jwc | 实习实践·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36075/list.htm` | student_affairs | yes |
| J10 | jwc | 语言文字·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36078/list.htm` | teaching_management | yes |
| J11 | jwc | 教材建设与管理·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36084/list.htm` | teaching_management | no |
| J12 | jwc | 课程思政建设·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36087/list.htm` | teaching_management | yes |
| J13 | jwc | 试卷印刷·工作动态 | `https://jwc.nankai.edu.cn/gzdt_36090/list.htm` | teaching_management | yes |
| J14 | jwc | 课程思政·通知公告 | `https://jwc.nankai.edu.cn/tzgg_35523/list.htm` | teaching_management | yes |
| J15 | jwc | 选课管理 | `https://jwc.nankai.edu.cn/xkgl/list.htm` | student_affairs | no |
| J16 | jwc | 辅修 | `https://jwc.nankai.edu.cn/fx/list.htm` | student_affairs | yes |
| J17 | jwc | 四六级考试 | `https://jwc.nankai.edu.cn/sljks/list.htm` | student_affairs | yes |
| J18 | jwc | 转专业 | `https://jwc.nankai.edu.cn/zzy/list.htm` | student_affairs | yes |
| J19 | jwc | 助教管理 | `https://jwc.nankai.edu.cn/zjgl_35937/list.htm` | teaching_management | yes |
| J20 | jwc | 学籍及毕业管理 | `https://jwc.nankai.edu.cn/xjjbygl/list.htm` | student_affairs | no |
| J21 | jwc | 课堂评价 | `https://jwc.nankai.edu.cn/ddpj/list.htm` | teaching_management | yes |
| J22 | jwc | 课程督导 | `https://jwc.nankai.edu.cn/zyrz/list.htm` | teaching_management | yes |
| J23 | jwc | 考试与档案管理 | `https://jwc.nankai.edu.cn/ksydagl/list.htm` | teaching_management | yes |
| J24 | jwc | 智慧书院 | `https://jwc.nankai.edu.cn/zhsy/list.htm` | teaching_management | yes |
| J25 | jwc | 拔尖人才 | `https://jwc.nankai.edu.cn/blb/list.htm` | student_affairs | yes |
| Z01 | nkzbb | 采购公告·货物 | `https://nkzbb.nankai.edu.cn/cghw/index.chtml` | procurement_notice | no |
| Z02 | nkzbb | 采购公告·工程 | `https://nkzbb.nankai.edu.cn/cggc/index.chtml` | procurement_notice | no |
| Z03 | nkzbb | 采购公告·服务 | `https://nkzbb.nankai.edu.cn/cgfw/index.chtml` | procurement_notice | no |
| Z04 | nkzbb | 采购公告·其他 | `https://nkzbb.nankai.edu.cn/cgqt/index.chtml` | procurement_notice | no |
| Z05 | nkzbb | 结果公告·货物 | `https://nkzbb.nankai.edu.cn/jghw/index.chtml` | procurement_result | no |
| Z06 | nkzbb | 结果公告·工程 | `https://nkzbb.nankai.edu.cn/jggc/index.chtml` | procurement_result | no |
| Z07 | nkzbb | 结果公告·服务 | `https://nkzbb.nankai.edu.cn/jgfw/index.chtml` | procurement_result | no |
| Z08 | nkzbb | 结果公告·其他 | `https://nkzbb.nankai.edu.cn/jgqt/index.chtml` | procurement_result | no |
| Z09 | nkzbb | 意向公开 | `https://nkzbb.nankai.edu.cn/yxgk/index.chtml` | procurement_intent | no |

## 4. Required audit record

For every Source produce one JSON object with at least:

```json
{
  "source_id": "P01",
  "site_id": "physics",
  "name": "通知公告",
  "candidate_url": "...",
  "final_url": "...",
  "audit_status": "PASS",
  "http_status": 200,
  "content_type": "text/html",
  "server_rendered": true,
  "is_time_series_list": true,
  "allow_empty_observed": false,
  "item_count_page1": 10,
  "sample_titles": ["...", "..."],
  "sample_dates": ["2026-09-05", "..."],
  "list_selector": "...",
  "item_selector": "...",
  "title_selector": "...",
  "date_selector": "...",
  "link_selector": "...",
  "pagination": {
    "kind": "path|query|none|unknown",
    "page1_url": "...",
    "page2_url": "...",
    "page_size_observed": 10
  },
  "detail_url_pattern": "...",
  "article_identity": {
    "method": "webplus_article_id|canonical_url|other",
    "regex": "...",
    "samples": ["..."]
  },
  "duplicate_source_candidates": [],
  "js_required": false,
  "fixture_path": "tests/fixtures/audit/...",
  "fetched_at": "ISO-8601",
  "notes": ""
}
```

Selectors may be CSS or XPath. They must be reproducible and no broader than needed.

## 5. Audit statuses

Use one primary status:

- `PASS` — source works as expected.
- `PASS_EMPTY` — valid source currently has zero items.
- `REDIRECTED` — source exists but canonical URL differs.
- `STRUCTURE_CHANGED` — source exists but baseline assumptions are wrong.
- `MISSING` — expected source not found.
- `NOT_A_LIST` — page is not a time-series list.
- `DUPLICATE_SOURCE` — source is effectively redundant with another approved source.
- `JS_REQUIRED` — meaningful list content requires JS/browser rendering.
- `BLOCKED` — access denied, anti-bot, robots/policy or other restriction.
- `OUT_OF_SCOPE` — candidate resolves to content outside v1 scope.
- `ERROR` — unexpected audit failure.

A secondary `warnings[]` array may include:
- inconsistent dates;
- malformed links;
- mixed news/notices;
- unstable selectors;
- pagination ambiguity;
- duplicate items within a page.

## 6. Discovery of missed sources

For each entry site, inspect main navigation and relevant second-level navigation.

A newly discovered candidate is in-scope only if all are true:
1. same host;
2. public;
3. time-ordered or continuously updated list;
4. fits the frozen inclusion policy;
5. not merely a news archive/static database/download page;
6. not redundant with an approved source.

Do not add it to production automatically. Record it under:

```json
"new_candidate_sources": [...]
```

and stop for human review.

## 7. Duplicate-source analysis

Compare:
- identical detail URLs;
- WebPlus article IDs;
- normalized title/date overlap;
- recent N-item overlap ratio.

Flag likely redundant Sources but do not merge them without approval.

Important distinction:
- same Notice appearing in multiple Sources is normal and should be deduplicated at Notice level;
- two Sources whose entire recent streams are essentially identical may be redundant Source definitions.

## 8. Identity audit

For Physics and JWC, explicitly test whether article URLs expose a stable CMS article ID, including cases where:
- the category portion differs;
- presentation path such as `_t12/` differs;
- the same article is linked by multiple list pages.

Record evidence with multiple sample URLs before approving a regex.

For NKZBB, determine the most stable identity available. Do not assume WebPlus semantics.

## 9. Pagination audit

For each Source determine:
- whether page 1 has a special path;
- page 2 URL;
- page number transformation;
- page size;
- item ordering;
- whether pinned/sticky items break strict chronology;
- whether duplicate items appear across pages.

This evidence informs frontier crawling in Phase B.

## 10. Empty-source audit

Do not trust the baseline `allow_empty` blindly.

If a page is empty:
- verify the page is structurally valid;
- verify navigation labels;
- inspect whether older pages or archives exist;
- distinguish “valid dormant column” from “broken parser”.

Propose `allow_empty` correction when needed.

## 11. HTML fixtures

Do not save 43 full fixtures by default.

Save representative fixtures sufficient to cover every distinct layout variant, including:
- each site’s dominant list layout;
- at least one empty-valid layout;
- any special pagination variant;
- any special item/date markup;
- a known cross-source duplicate identity example where feasible.

Sanitize public fixtures before commit:
- cookies;
- session IDs;
- transient tracking parameters if embedded;
- irrelevant huge scripts.

Keep enough HTML to reproduce selectors offline.

## 12. Live probing etiquette

- low concurrency;
- reasonable timeout;
- clear User-Agent;
- no authenticated endpoints;
- no bypass of access controls;
- no deep crawl;
- no attachment download unless necessary to understand the list structure;
- obey obvious site restrictions.

## 13. Phase A outputs

Required:

### `artifacts/source_audit.json`

Top-level shape:

```json
{
  "schema_version": 1,
  "audited_at": "...",
  "entry_sites": [...],
  "sources": [43 audit objects],
  "new_candidate_sources": [...],
  "summary": {
    "pass": 0,
    "pass_empty": 0,
    "redirected": 0,
    "structure_changed": 0,
    "missing": 0,
    "other_failures": 0
  }
}
```

### `artifacts/SOURCE_AUDIT_RESULTS.md`

Human-readable summary containing:
- 43-row status table;
- exact changed URLs;
- selector/layout groups;
- duplicate-source findings;
- new candidate Sources;
- identity strategy evidence;
- pagination evidence;
- decisions required from user.

### Fixtures

Representative files under:
`tests/fixtures/audit/`

### Proposed registry

A proposed `config/sources.audit-proposed.yaml`, never silently replacing the frozen baseline.

## 14. Mandatory stop

After Phase A:
- run audit validation;
- present results;
- **STOP**.

Do not implement:
- production crawler;
- state branch workflow;
- event detector;
- Feishu delivery;
- final GitHub Actions schedules.

Wait for explicit human approval.
