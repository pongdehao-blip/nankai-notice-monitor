# CODEX_PROMPT — Nankai Notice Watch v1

You are implementing a public GitHub project named **Nankai Notice Watch v1**.

Before doing anything, read these files in order:

1. `SPEC.md`
2. `SOURCE_AUDIT.md`
3. `ACCEPTANCE.md`

Treat them as the authoritative product contract.

## Non-negotiable execution model

This work has two phases and a mandatory human gate.

### PHASE A — LIVE SOURCE AUDIT

Your task in Phase A is to validate the 43 candidate Sources against the live official websites.

You may:
- write a small audit utility;
- make polite HTTP requests;
- inspect HTML;
- create `source_audit.json`;
- create `SOURCE_AUDIT_RESULTS.md`;
- save representative sanitized HTML fixtures;
- propose a corrected Source Registry.

You must:
- audit every one of the 43 baseline Source IDs;
- inspect the three entry sites for missing in-scope columns;
- verify final URLs, selectors, pagination and identity behavior;
- distinguish valid empty sources from broken parsing;
- record contradictions rather than hiding them;
- keep all probing same-host and public;
- protect the public repository from secrets/cookies.

You must **not**:
- implement the production monitoring pipeline;
- implement Feishu delivery;
- implement state-branch automation;
- implement final scheduled GitHub Actions;
- silently delete or replace a Source;
- auto-enable newly discovered Sources;
- use Playwright/Selenium unless the audit only records that a Source is JS-required.

### Required Phase A outputs

Produce:
- `artifacts/source_audit.json`
- `artifacts/SOURCE_AUDIT_RESULTS.md`
- `config/sources.audit-proposed.yaml`
- representative sanitized HTML fixtures under `tests/fixtures/audit/`
- an audit validation test/script

Then run validation and summarize:
- PASS/PASS_EMPTY count;
- redirects;
- changed/missing sources;
- duplicate-source candidates;
- new in-scope candidate sources;
- layout groups;
- identity evidence;
- user decisions required.

### HARD STOP

After Phase A output is complete:

**STOP. Do not start Phase B.**

Ask the user to review the audit. There is no implied approval.

---

## PHASE B — IMPLEMENTATION

Start only after the user explicitly approves Phase A and the approved Source Registry is available.

Implement only against the approved audit.

Recommended order:

1. models and configuration;
2. site adapters + offline fixture tests;
3. URL normalization + identity + deduplication;
4. state + baseline + event detection;
5. frontier crawling + health;
6. report builder + Feishu client;
7. one-shot CLI;
8. GitHub Actions;
9. integration tests;
10. README and final acceptance run.

## Frozen product decisions

Do not change these:

- public GitHub repository;
- zero-cost first;
- standard GitHub-hosted Actions runner;
- three official hosts only;
- 43 baseline Sources must be audited;
- Physics research updates included;
- Physics undergraduate/graduate education collected as whole streams, allowing limited news;
- academic activities/lectures included;
- teaching-management work included;
- historical teaching-result/archive databases excluded;
- NKZBB 工作动态 excluded;
- crawl every 3 hours;
- daily report at Beijing 17:42;
- 17:42 run crawls before reporting;
- errors appear only in the fixed daily report;
- heartbeat report is sent even with zero new notices;
- no AI;
- no article/PDF/Word content analysis;
- no browser automation in production v1;
- no REMOVED event;
- no external-domain expansion;
- no real-time alerts.

## Engineering priorities

In order:
1. no silent notice loss;
2. no duplicate notices;
3. observable failures;
4. polite site access;
5. maintainability;
6. zero cost;
7. simplicity.

Prefer limited, explicit, testable code over generic framework abstractions.

## Security

The repository is public.

Never commit or print:
- `FEISHU_WEBHOOK`;
- GitHub tokens;
- cookies or Authorization headers;
- environment dumps;
- non-public data.

Use mocked webhook calls in tests.

## Change control

If live sites contradict the documents:
- preserve product semantics;
- make the smallest technical proposal;
- record evidence;
- stop for user approval if scope changes.

Never expand requirements simply because a library makes it convenient.

## Definition of success

Phase A success is **a trustworthy, reviewable live Source Audit and a hard stop**.

Phase B success is the complete acceptance criteria in `ACCEPTANCE.md`.

Do not claim completion merely because a live crawl “seems to work”.
