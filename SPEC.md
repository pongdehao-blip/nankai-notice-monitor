# Nankai Notice Watch v1 — SPEC

**Status:** Frozen product specification; implementation is gated by live Source Audit.  
**Repository:** Public GitHub repository.  
**Runtime:** GitHub Actions, standard GitHub-hosted runner.  
**Timezone:** `Asia/Shanghai`.  
**Notification:** Feishu group custom bot webhook.  
**AI:** Not used in v1.

## 1. Product goal

Build a small, Nankai-specific structured notice monitor. It monitors approved public list pages under three official hosts, detects new/updated notices, deduplicates the same notice across multiple columns, and sends exactly one logical daily report at **17:42 Beijing time**. Crawling occurs every 3 hours.

The system optimizes in this order:

1. do not miss notices;
2. avoid duplicate reporting;
3. detect monitor failures;
4. be polite to official sites;
5. be maintainable;
6. remain zero-cost;
7. stay simple.

This is **not** a general web-change monitoring platform.

## 2. Scope

Only these hosts are in v1:

- `physics.nankai.edu.cn`
- `jwc.nankai.edu.cn`
- `nkzbb.nankai.edu.cn`

The user-provided homepages are entry points, not single monitored URLs. v1 monitors a manually approved Source Registry of 43 candidate time-series sources.

Included content:
- notices, announcements, public notices, selection/result lists;
- undergraduate and graduate education;
- teaching administration and teaching-management work;
- selection, exams, transfer, recommendation, competitions, thesis, internships;
- academic activities, seminars, lectures and reports;
- admissions and postdoctoral information;
- physics-school research updates, accepting limited news-like items;
- procurement notices, results and procurement intentions.

Explicitly excluded:
- ordinary news streams and event recaps;
- rules/regulation archives;
- downloads, static forms and static service guides;
- historical teaching-award/course/project databases;
- NKZBB “工作动态”;
- external Nankai subdomains reached by hyperlinks;
- authenticated pages;
- AI summarization/classification;
- full article/PDF/Word attachment parsing;
- JavaScript browser automation;
- deletion/removal events.

## 3. Two-stage delivery model

### Phase A — Live Source Audit only

Codex must live-test all 43 baseline Sources and the three entry sites. It may create audit scripts and fixtures, but **must not implement the production monitor**.

Required outputs:
- `artifacts/source_audit.json`
- `artifacts/SOURCE_AUDIT_RESULTS.md`
- representative HTML fixtures under `tests/fixtures/audit/`
- proposed corrections to `config/sources.yaml`
- list of newly discovered in-scope candidate Sources, if any

**Mandatory gate:** stop after Phase A and request human review. Phase B must not start until the user explicitly approves the audit.

### Phase B — Production implementation

Only after approval, implement against the **approved live audit**, not against assumptions in the baseline registry.

## 4. Schedule

Beijing time:

- 02:42 — crawl
- 05:42 — crawl
- 08:42 — crawl
- 11:42 — crawl
- 14:42 — crawl
- **17:42 — crawl, build daily report, send Feishu**
- 20:42 — crawl
- 23:42 — crawl

The Python package contains no internal scheduler. Use one-shot CLI commands:

```bash
python -m nankai_watch crawl --state-path ...
python -m nankai_watch daily --state-path ...
```

`daily` means: load state → crawl → detect events → build health summary → send report → persist delivery state.

GitHub Actions scheduling is not a hard real-time SLA. Small delays are acceptable.

## 5. GitHub Actions design

Use:
- `.github/workflows/crawl.yml`
- `.github/workflows/daily-report.yml`

All workflows that mutate state use the same concurrency group, e.g.:

```yaml
concurrency:
  group: nankai-notice-state
  cancel-in-progress: false
```

Use `Asia/Shanghai` in the schedule if supported by the current GitHub syntax used during implementation.

Public repository requirement:
- only public-site metadata may be committed;
- no secrets in source, fixture, state or logs;
- `FEISHU_WEBHOOK` exists only as a GitHub Actions Secret;
- workflows need only the minimum repository permissions required to update state.

Operational caveat: GitHub can disable scheduled workflows in public repositories after a long period without repository activity. README must document how to re-enable them and how to verify the heartbeat.

## 6. Persistence

v1 uses a dedicated `state` branch with machine-generated JSON state. Do not use SQLite/MySQL/PostgreSQL/Redis.

Core state concepts:

### Notice
```text
id
site_id
title
canonical_url
publish_date
source_ids[]
first_seen_at
last_observed_at
```

### Event
```text
event_id
notice_id
type = NEW | UPDATED
detected_at
reported_at | null
```

### SourceHealth
```text
source_id
last_success_at
last_status
last_item_count
consecutive_failures
last_error
etag | null
last_modified | null
```

### Run
```text
run_id
scheduled_at
started_at
finished_at
source_results[]
```

Keep only a bounded run history (default: 7 days).

All timestamps must be timezone-aware ISO 8601.

## 7. Baseline behavior

On an empty state:
1. crawl approved Sources;
2. register current notices as baseline;
3. do **not** create `NEW` events for baseline notices;
4. save state;
5. daily report may state that initialization occurred.

This prevents hundreds of historical notices from being reported as new.

## 8. HTTP fetcher boundary

Production v1 uses `requests.Session`.

Recommended defaults:
- connect/read timeout around 15 seconds;
- up to 2 retries for transient failures;
- modest backoff;
- sequential access per host;
- small delay between requests;
- explicit, non-deceptive User-Agent;
- conditional requests using ETag/Last-Modified when the server supports them.

No Playwright, Selenium, browser automation, CAPTCHA bypass or aggressive concurrency.

If a Source becomes JS-only, mark it unhealthy and surface this in the daily report. Do not expand v1 automatically.

## 9. Parsing architecture

Implement site-level adapters, not one parser per Source:

```text
PhysicsAdapter
JwcAdapter
NkzbbAdapter
```

Every approved Source is configuration plus adapter selection.

Parser output:

```python
@dataclass
class ParsedItem:
    source_id: str
    site_id: str
    title: str
    url: str
    publish_date: str | None
```

Parsers only transform HTML into structured items. They do not decide baseline, novelty, delivery or persistence.

## 10. URL normalization and notice identity

Normalize:
- relative → absolute URL;
- scheme/host casing;
- fragments;
- known presentation/template paths such as physics `_t12/`;
- meaningless query parameters when proven safe.

Identity resolver priority:

1. For WebPlus-style Physics/JWC article URLs, extract stable article ID when live audit proves the pattern.
2. Else use normalized canonical URL.
3. Last-resort fallback: `site_id + normalized title + publish_date`.

The audit, not this document, decides the exact article-ID regex.

One Notice may have multiple `source_ids`. Same notice in multiple columns is reported once.

## 11. Event semantics

v1 emits:
- `NEW`
- `UPDATED`

`UPDATED` when a known stable notice identity has a materially changed title or publish date.

Do not emit `REMOVED`. Pagination movement, unpinning and CMS reorganization create false deletion signals.

## 12. Frontier crawling

Normal run:
1. fetch page 1;
2. parse items;
3. if sufficient known frontier is encountered, stop;
4. if the page is mostly/all unknown, fetch next page;
5. hard limit `max_pages_per_run`, default 3.

If the hard limit is reached while the frontier remains unknown, do not continue indefinitely. Record `OVERFLOW_RISK` and show it in the next daily report.

Initial baseline may use two pages per Source unless the live audit justifies another value.

## 13. Empty-source policy

`item_count == 0` is not always failure.

Each Source has `allow_empty`. Phase A must determine whether the baseline flag is correct.

For a Source historically non-empty, a sudden parse result of zero should become `EMPTY_UNEXPECTED` or `PARSE_ERROR`, not “no new notices”.

## 14. Health model

Suggested statuses:
- `OK`
- `HTTP_ERROR`
- `TIMEOUT`
- `PARSE_ERROR`
- `EMPTY_UNEXPECTED`
- `JS_REQUIRED`
- `OVERFLOW_RISK`
- `STATE_ERROR`

No immediate Feishu alert is sent for these. All errors are summarized only in the 17:42 report.

## 15. Reporting semantics

Report window is **not** calendar day 00:00–17:42.

Include every Event with `reported_at == null`.

This guarantees later recovery after:
- a missed run;
- delayed Action scheduling;
- Feishu failure;
- temporary site failure.

Even with zero events, send a heartbeat report.

Logical report order:
1. Physics School
2. Academic Affairs Office
3. Procurement Office
4. System health

Each item shows:
- title;
- source/column;
- official publish date if available;
- original link;
- event type if `UPDATED`.

No AI summary.

A logical report may be split into multiple Feishu messages/cards when needed. Never silently truncate. Only after **all** chunks succeed may events be marked reported.

## 16. Delivery guarantee

Use at-least-once semantics:

```text
build → send → confirm success → mark reported → persist
```

Never mark events reported before successful send.

Rare duplicates are acceptable; silent loss is not.

## 17. Source Registry baseline

The following 43 entries are **candidate baselines for Phase A**, not automatically trusted production URLs.

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

Phase A may propose corrected URLs, merges, or replacements, but must never silently drop an entry.

## 18. Public repository security

Never commit:
- Feishu webhook;
- Authorization/Cookie headers;
- private tokens;
- raw environment dumps;
- authenticated HTML;
- personal data not already public on the monitored pages.

Fixtures should contain only public pages needed to reproduce parsers. If an HTML page embeds analytics/session identifiers, sanitize them before commit.

## 19. Project structure

Recommended:

```text
nankai-notice-watch/
├── src/nankai_watch/
│   ├── models.py
│   ├── config.py
│   ├── fetcher.py
│   ├── normalize.py
│   ├── identity.py
│   ├── events.py
│   ├── state.py
│   ├── health.py
│   ├── adapters/
│   │   ├── base.py
│   │   ├── physics.py
│   │   ├── jwc.py
│   │   └── nkzbb.py
│   ├── report/
│   │   ├── builder.py
│   │   └── feishu.py
│   └── cli.py
├── config/sources.yaml
├── tests/
├── artifacts/
├── .github/workflows/
├── pyproject.toml
├── README.md
├── SPEC.md
├── SOURCE_AUDIT.md
├── ACCEPTANCE.md
└── CODEX_PROMPT.md
```

## 20. Dependencies

Prefer:
- `requests`
- `beautifulsoup4`
- `lxml`
- `PyYAML`

Use standard library for data structures, JSON, hashing, dates, URL parsing, logging and pathlib.

No large framework unless Phase A proves a hard necessity and the user approves it.

## 21. Explicit non-goals

Do not implement in v1:
- AI/LLM;
- article-body or attachment analysis;
- personalized ranking;
- deadline extraction;
- web GUI/API server;
- browser automation;
- authenticated/CAS pages;
- automatic source enablement;
- external-site expansion;
- removal monitoring;
- real-time error alerts;
- Docker/VPS deployment;
- email/Telegram/WeChat.

## 22. Change-control rule

If live behavior conflicts with this specification:
- preserve product semantics;
- make the smallest technical correction;
- record it in Phase A results;
- stop at the human gate if the correction changes monitored scope.

Codex must not expand scope for convenience.
