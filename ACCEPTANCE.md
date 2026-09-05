# Nankai Notice Watch v1 — ACCEPTANCE

This document defines pass/fail gates for Phase A and Phase B.

## 1. Global rule

A partial system that hides uncertainty is a failure.

When the live website contradicts assumptions, record the contradiction and require review rather than silently adapting scope.

---

# Phase A — Source Audit acceptance

## A1. Coverage

PASS only if:
- all 43 baseline Source IDs have exactly one audit record;
- all three entry sites were inspected for in-scope list sources;
- missing/redirected sources are reported rather than skipped.

FAIL if:
- any baseline Source is absent from the audit output;
- audit stops early because a URL changed;
- newly discovered source is silently auto-approved.

## A2. Evidence quality

For every non-missing Source, audit must provide enough evidence to reproduce extraction:
- final URL;
- HTTP/content type;
- server-rendered determination;
- item count;
- title/date/link extraction;
- pagination evidence;
- identity strategy;
- fixture/layout group or explicit justification.

FAIL if selectors are “works on live page” but cannot be represented/tested offline.

## A3. Status validity

`PASS` requires:
- page is a valid time-series list;
- representative items have correct title/link/date;
- pagination behavior is understood or explicitly `none`;
- no browser automation is needed.

`PASS_EMPTY` requires:
- valid list page;
- empty state confirmed structurally, not inferred from a broken selector.

## A4. Source-policy review

Audit must explicitly report:
- Physics research updates included;
- Physics undergraduate/graduate sources allowed to contain limited news;
- academic activities/lectures included;
- teaching-management work included;
- historical teaching-result databases excluded;
- NKZBB 工作动态 excluded.

Any discovered conflict is a human decision, not Codex’s decision.

## A5. Audit machine validation

`source_audit.json` must:
- parse as JSON;
- have `schema_version`;
- contain 43 unique baseline Source IDs;
- have no duplicate `source_id`;
- use ISO-8601 timestamps;
- contain no credentials/cookies/secrets.

## A6. Security

FAIL immediately if committed artifacts contain:
- real Feishu webhook;
- GitHub token;
- Cookie/Authorization credentials;
- non-public personal data;
- raw environment dumps.

## A7. Phase A gate

Phase A is complete only when:
1. automated audit validation passes;
2. human-readable results exist;
3. proposed registry exists;
4. representative fixtures exist;
5. Codex stops and asks for user approval.

There is no implicit approval.

---

# Phase B — Implementation acceptance

Phase B may start only after explicit approval of Phase A.

## B1. Architecture

Required:
- source registry separate from parser code;
- site-level adapters, not 43 hand-written parsers;
- fetch/parse/normalize/identity/event/state/report responsibilities separated;
- one-shot CLI; no in-process scheduler.

FAIL if the application grows into a general crawler framework or web service.

## B2. Parsing

For every approved Source:
- correct adapter;
- title extracted;
- link absolute/canonicalizable;
- publish date extracted when present;
- offline fixture tests exist for every layout class.

Live integration smoke test must not be the only test.

## B3. Identity and deduplication

Automated tests must cover:
- same article linked from different Sources → one Notice;
- Physics/JWC stable CMS ID when audit approved it;
- `_t12` or presentation-path normalization when audit proved equivalence;
- canonical URL fallback;
- no false merge for similar titles with different article identities.

## B4. Event semantics

Tests:
- baseline notice → no NEW event;
- new identity → NEW;
- unchanged identity/title/date → no event;
- same identity + changed title → UPDATED;
- same identity + changed publish date → UPDATED;
- disappearing list item → no REMOVED event.

## B5. Frontier crawling

Tests:
- known frontier on page 1 stops;
- all-new page advances;
- maximum page cap works;
- cap without known frontier produces `OVERFLOW_RISK`;
- pagination duplicate items do not duplicate notices.

## B6. Empty sources

Tests:
- `allow_empty=true` + valid empty layout → OK;
- previously non-empty source suddenly parses zero → health warning/error;
- selector failure cannot masquerade as valid empty.

## B7. Health

Health statuses must be persisted for the daily period.

Tests:
- timeout;
- HTTP error;
- parser error;
- unexpected empty;
- temporary failure followed by recovery;
- overflow risk.

No test should produce immediate Feishu error alert.

## B8. Reporting

Daily report must:
- include all unreported events, not only “today”;
- order sites: Physics → JWC → NKZBB;
- show source, title, date if available, original URL;
- mark UPDATED;
- include health summary;
- send heartbeat even with zero events;
- split long reports without truncation.

## B9. Delivery semantics

Tests:
- all report chunks succeed → mark events reported;
- any chunk fails → events stay pending;
- retry later includes pending events;
- no code path marks `reported_at` before successful complete delivery.

## B10. Feishu secret handling

- real webhook only via `FEISHU_WEBHOOK` secret;
- no secret logging;
- unit tests use fake webhook/mocked HTTP;
- README examples use placeholders.

## B11. State persistence

Required:
- JSON state schema version;
- timezone-aware timestamps;
- bounded run history;
- atomic local write;
- state branch workflow avoids destructive overwrite;
- concurrency group configured with `cancel-in-progress: false`.

Tests:
- missing state initializes;
- corrupted state fails safely;
- schema mismatch fails explicitly;
- local state path works on Windows;
- no Git logic embedded deeply into business logic.

## B12. GitHub Actions

Required:
- public-repo compatible standard runner;
- crawl schedule 7 times/day;
- daily schedule 17:42 Asia/Shanghai;
- `daily` performs crawl before report;
- manual `workflow_dispatch`;
- minimum needed permissions;
- state branch handling documented.

Operational documentation must mention:
- schedule may run late;
- public scheduled workflows can be disabled after prolonged repository inactivity;
- how to confirm the heartbeat;
- how to re-enable workflow.

## B13. Polite crawling

Review:
- reasonable User-Agent;
- no high concurrency;
- retry/backoff;
- bounded pages;
- no auth bypass/browser automation;
- no unnecessary detail-page/attachment downloads.

## B14. Test matrix

Minimum automated suites:

```text
test_config
test_parser_physics
test_parser_jwc
test_parser_nkzbb
test_url_normalization
test_identity
test_dedup
test_events
test_baseline
test_frontier
test_empty_source
test_health
test_state
test_report_builder
test_feishu_delivery
test_cli
```

## B15. Documentation

README must include:
- project purpose and scope;
- 43-source/audit model;
- Phase A/Phase B workflow;
- local Windows setup;
- local crawl and daily commands;
- test commands;
- GitHub public repo deployment;
- `FEISHU_WEBHOOK` secret setup;
- state branch initialization;
- manual workflow run;
- recovery after a failed report;
- scheduled-workflow inactivity caveat;
- adding/editing a Source through audit first.

## B16. Final done criteria

v1 is done only when:
1. approved Source Registry is implemented;
2. all tests pass;
3. local dry run succeeds without Feishu secret;
4. mocked daily delivery succeeds;
5. GitHub workflows lint/parse;
6. public-repo secret scan finds no credential;
7. first production deployment creates baseline without notice flood;
8. next successful 17:42 report provides heartbeat;
9. README is sufficient for re-deployment from scratch.

Any intentionally deferred item must be listed in `KNOWN_LIMITATIONS.md`; it cannot be silently omitted.
