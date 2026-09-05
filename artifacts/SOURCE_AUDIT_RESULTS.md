# 南开通知监测：Phase A 实时来源审计

审计生成时间：2026-09-05T14:55:45.379409+00:00（UTC；每个请求另有实际抓取时间）。

**当前仅完成审计交付，Phase B 未获批准。未创建正式监控、飞书投递、状态分支或定时工作流。**

## 结论

43 个基线 ID 完整保留。状态：{"pass": 37, "pass_empty": 4, "redirected": 0, "structure_changed": 2, "missing": 0, "other_failures": 0}。所有基线首页 HTTP 200，无 HTTP 重定向或失效来源。

四个有效空栏目：J09 实习实践、J10 语言文字、J13 试卷印刷、J14 课程思政通知。证据是明确选中导航、正确标题、已知列表容器实际空白且没有翻页；不是单凭选择器返回零。
所有非空基线的分页已核验：有第二页的实际请求第二页；不足一页且无翻页控件的标为 none。采购其他类第二页分别只有 12 和 7 条，是正常末页。

## 需要审核的具体方案

1. J21 保留 ID，将 https://jwc.nankai.edu.cn/ddpj/list.htm 改为 https://jwc.nankai.edu.cn/kcddypj/list.htm。前者是父栏目默认视图，后者是导航明确子栏目；近期 7 条相同。J22 名称由“课程督导”改为“教学督导”，URL 不变。
2. 建议 allow_empty 仅对上述四个已证实空栏目设 true，其余设 false；已存在文章的栏目突然为零应报错。基线值全部保留在 JSON 中。
3. 审核下表四个新增候选；建议补充而不替换既有流。另 /533/ 学术活动含讲座和较多回顾，曝光台为空，二者范围存疑，暂不启用。
4. 物理科研/教育列表有指向新闻站、微信公众号等外链。建议保留官网列表提供的标题、日期和链接，但不请求外站；请确认是否接受这一解释。
5. P03/J01 等有置顶或非严格日期排序，必须使用稳健已知边界，不能“遇到第一条旧文章就停止”。列出的教学工作流中也夹有规章和工作回顾：建议按批准栏目整流采集，不做正文分类。

## 43 个基线来源

| ID | 栏目 | 状态 | 首页条数 | 分页 | 备注 |
|---|---|---|---:|---|---|
| P01 | [通知公告](https://physics.nankai.edu.cn/572/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date |
| P02 | [本科生教育](https://physics.nankai.edu.cn/574/list.htm) | PASS | 10 | path | Mixed news explicitly accepted by frozen product policy；URL path date differs from displayed publish date; use displayed date |
| P03 | [研究生教育](https://physics.nankai.edu.cn/576/list.htm) | PASS | 10 | path | Nonchronological ordering / possible sticky item: frontier must not stop on first known item；External article links observed; do not fetch external destinations；Mixed news explicitly accepted by frozen product policy；URL path date differs from displayed publish date; use displayed date |
| P04 | [学术活动/讲座](https://physics.nankai.edu.cn/573/list.htm) | PASS | 10 | path | External article links observed; do not fetch external destinations；URL path date differs from displayed publish date; use displayed date |
| P05 | [本科招生](https://physics.nankai.edu.cn/bkzs/list.htm) | PASS | 2 | none | External article links observed; do not fetch external destinations |
| P06 | [硕士招生](https://physics.nankai.edu.cn/sszs/list.htm) | PASS | 10 | path | Nonchronological ordering / possible sticky item: frontier must not stop on first known item；External article links observed; do not fetch external destinations；URL path date differs from displayed publish date; use displayed date |
| P07 | [博士招生](https://physics.nankai.edu.cn/bszs/list.htm) | PASS | 10 | path | Nonchronological ordering / possible sticky item: frontier must not stop on first known item；External article links observed; do not fetch external destinations；URL path date differs from displayed publish date; use displayed date |
| P08 | [博士后](https://physics.nankai.edu.cn/bsh/list.htm) | PASS | 2 | none | 已验证 |
| P09 | [科研动态](https://physics.nankai.edu.cn/dbxkycg/list.htm) | PASS | 10 | path | External article links observed; do not fetch external destinations；Mixed news explicitly accepted by frozen product policy |
| J01 | [通知公告](https://jwc.nankai.edu.cn/tzgg/list.htm) | PASS | 10 | path | Nonchronological ordering / possible sticky item: frontier must not stop on first known item；URL path date differs from displayed publish date; use displayed date |
| J02 | [课程建设·工作动态](https://jwc.nankai.edu.cn/gzdt/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date |
| J03 | [专业建设·工作动态](https://jwc.nankai.edu.cn/gzdt_36062/list.htm) | PASS | 10 | path | 已验证 |
| J04 | [通识选修课·工作动态](https://jwc.nankai.edu.cn/gzdt_36064/list.htm) | PASS | 10 | path | 已验证 |
| J05 | [推免研究生·工作动态](https://jwc.nankai.edu.cn/gzdt_36067/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date |
| J06 | [毕业论文·工作动态](https://jwc.nankai.edu.cn/gzdt_36069/list.htm) | PASS | 10 | path | 已验证 |
| J07 | [学科竞赛·工作动态](https://jwc.nankai.edu.cn/gzdt_36071/list.htm) | PASS | 3 | none | 已验证 |
| J08 | [创新创业·工作动态](https://jwc.nankai.edu.cn/gzdt_36073/list.htm) | PASS | 10 | path | Dormant recent sample; retain baseline source, do not infer missing；Dormant recent sample; retain baseline source, do not infer missing |
| J09 | [实习实践·工作动态](https://jwc.nankai.edu.cn/gzdt_36075/list.htm) | PASS_EMPTY | 0 | none | Recognized empty container + matching selected navigation + column heading; no older-page/archive link within column. Current emptiness only, not proof of perpetual emptiness. |
| J10 | [语言文字·工作动态](https://jwc.nankai.edu.cn/gzdt_36078/list.htm) | PASS_EMPTY | 0 | none | Recognized empty container + matching selected navigation + column heading; no older-page/archive link within column. Current emptiness only, not proof of perpetual emptiness. |
| J11 | [教材建设与管理·工作动态](https://jwc.nankai.edu.cn/gzdt_36084/list.htm) | PASS | 10 | path | 已验证 |
| J12 | [课程思政建设·工作动态](https://jwc.nankai.edu.cn/gzdt_36087/list.htm) | PASS | 10 | path | 已验证 |
| J13 | [试卷印刷·工作动态](https://jwc.nankai.edu.cn/gzdt_36090/list.htm) | PASS_EMPTY | 0 | none | Recognized empty container + matching selected navigation + column heading; no older-page/archive link within column. Current emptiness only, not proof of perpetual emptiness. |
| J14 | [课程思政·通知公告](https://jwc.nankai.edu.cn/tzgg_35523/list.htm) | PASS_EMPTY | 0 | none | Recognized empty container + matching selected navigation + column heading; no older-page/archive link within column. Current emptiness only, not proof of perpetual emptiness. |
| J15 | [选课管理](https://jwc.nankai.edu.cn/xkgl/list.htm) | PASS | 10 | path | 已验证 |
| J16 | [辅修](https://jwc.nankai.edu.cn/fx/list.htm) | PASS | 7 | none | 已验证 |
| J17 | [四六级考试](https://jwc.nankai.edu.cn/sljks/list.htm) | PASS | 10 | path | 已验证 |
| J18 | [转专业](https://jwc.nankai.edu.cn/zzy/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date |
| J19 | [助教管理](https://jwc.nankai.edu.cn/zjgl_35937/list.htm) | PASS | 10 | path | 已验证 |
| J20 | [学籍及毕业管理](https://jwc.nankai.edu.cn/xjjbygl/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date |
| J21 | [课堂评价](https://jwc.nankai.edu.cn/ddpj/list.htm) | STRUCTURE_CHANGED | 7 | none | 基线 /ddpj/ 是“督导评价”父栏目，当前显示“课堂评价”默认子流；首页/侧栏明确链接 /kcddypj/。二者近期 7 条完全相同。建议保留 J21 ID，改用明确子栏目 URL；这不是 HTTP 重定向。 |
| J22 | [课程督导](https://jwc.nankai.edu.cn/zyrz/list.htm) | STRUCTURE_CHANGED | 6 | none | 官网栏目名为“教学督导”，基线“课程督导”应更名；URL 保持不变。 |
| J23 | [考试与档案管理](https://jwc.nankai.edu.cn/ksydagl/list.htm) | PASS | 10 | path | Dormant recent sample; retain baseline source, do not infer missing；Dormant recent sample; retain baseline source, do not infer missing |
| J24 | [智慧书院](https://jwc.nankai.edu.cn/zhsy/list.htm) | PASS | 10 | path | URL path date differs from displayed publish date; use displayed date；Dormant recent sample; retain baseline source, do not infer missing；Dormant recent sample; retain baseline source, do not infer missing |
| J25 | [拔尖人才](https://jwc.nankai.edu.cn/blb/list.htm) | PASS | 4 | none | 已验证 |
| Z01 | [采购公告·货物](https://nkzbb.nankai.edu.cn/cghw/index.chtml) | PASS | 15 | query | 已验证 |
| Z02 | [采购公告·工程](https://nkzbb.nankai.edu.cn/cggc/index.chtml) | PASS | 15 | query | 已验证 |
| Z03 | [采购公告·服务](https://nkzbb.nankai.edu.cn/cgfw/index.chtml) | PASS | 15 | query | 已验证 |
| Z04 | [采购公告·其他](https://nkzbb.nankai.edu.cn/cgqt/index.chtml) | PASS | 15 | query | 已验证 |
| Z05 | [结果公告·货物](https://nkzbb.nankai.edu.cn/jghw/index.chtml) | PASS | 15 | query | 已验证 |
| Z06 | [结果公告·工程](https://nkzbb.nankai.edu.cn/jggc/index.chtml) | PASS | 15 | query | 已验证 |
| Z07 | [结果公告·服务](https://nkzbb.nankai.edu.cn/jgfw/index.chtml) | PASS | 15 | query | 已验证 |
| Z08 | [结果公告·其他](https://nkzbb.nankai.edu.cn/jgqt/index.chtml) | PASS | 15 | query | 已验证 |
| Z09 | [意向公开](https://nkzbb.nankai.edu.cn/yxgk/index.chtml) | PASS | 15 | query | 已验证 |

## 新增候选（全部未启用）

| ID | 栏目 | 理由 |
|---|---|---|
| C01 | [学科竞赛（父栏目直属流）](https://jwc.nankai.edu.cn/xkjs/list.htm) | 包含 2026-09-04 竞赛通知，J07 子栏目未覆盖；建议新增而非替换。 |
| C02 | [本科生教育（导航旧流）](https://physics.nankai.edu.cn/536/list.htm) | 同名独立通知流，近期样本停于 2021 年；不能因陈旧而静默丢弃。 |
| C03 | [研究生教育（导航独立流）](https://physics.nankai.edu.cn/547/list.htm) | 包含 2024 年论文答辩通知，与 P03 当前首页不同。 |
| C04 | [科研动态（首页流）](https://physics.nankai.edu.cn/575/list.htm) | 包含奖励申报公示，与 P09 近期内容部分重合但不是完整别名。 |

## 模板、分页与离线证据

五种 DOM 布局：Physics `#wp_news_w6`；JWC `.page-con-list-news` 拆分年月日和 `.page-con-list-news1` 整体日期；NKZBB `#datab > dd` 与意向公开 `dl.llist > dd`。另保存有效空、单页、置顶、第二页和末页样例。
Physics/JWC：跟随官网 list2.htm，后续路径 list{n}.htm。NKZBB：9 个栏目实测 GET `index.chtml?curPage=2`，返回第二页范围与不同文章。UI 虽用 AJAX/POST，但无需浏览器、Cookie 或不透明表单字段；所有请求都为公开 GET。
标题优先取 a/@title（防止采购意向正文截断），其次锚文本。日期取列表展示值，不能从文章 URL 的年月日推断。JSON 中逐条保留分页 URL、第二页样本、排序、跨页重复证据。
当前保存 19 个代表性 fixture，清单见 fixture_manifest.json。已删除脚本、输入字段、图片、追踪与无关属性；不存响应 Cookie/Authorization。

## 身份与重复分析

Physics/JWC 建议同站点 `article_id`：`/c\d+a(\d+)/page\.htm$`。类别 c 编号不参与身份；不匹配时保留规范 URL。NKZBB 用完整规范 URL，未证明数字 ID 可跨分类合并。
Physics 的普通、_t12、不同 c 类别三种 URL 元数据标题一致；JWC 不同 c 类别标题一致，但 _t12 返回 302，未跟随，因此不批准 JWC 通用模板路径剥离。完整 URL/状态/时间在 identity_evidence.json。
基线内首屏重合结果如下。高重合只是候选，不自动合并；样本窗口不能证明整个历史流冗余。

| 来源对 | 相同身份数 | 重合率（除以较大集合） | 源冗余候选 |
|---|---:|---:|---|
| P01 / P02 | 1 | 10% | 否，仅文章去重 |
| P03 / P06 | 5 | 50% | 否，仅文章去重 |
| P03 / P07 | 4 | 40% | 否，仅文章去重 |
| P06 / P07 | 6 | 60% | 否，仅文章去重 |
| J01 / J05 | 1 | 10% | 否，仅文章去重 |
| J01 / J15 | 1 | 10% | 否，仅文章去重 |
| J01 / J19 | 1 | 10% | 否，仅文章去重 |
| J01 / J25 | 1 | 10% | 否，仅文章去重 |

导航别名候选：
- https://jwc.nankai.edu.cn/kcszjs/list.htm → J12；首屏文章标识集合完全一致；仅证明当前窗口重合，不保证长期等价，不自动合并。
- https://jwc.nankai.edu.cn/kcddypj/list.htm → J21；首屏文章标识集合完全一致；仅证明当前窗口重合，不保证长期等价，不自动合并。
- https://jwc.nankai.edu.cn/bjrc/list.htm → J25；首屏文章标识集合完全一致；仅证明当前窗口重合，不保证长期等价，不自动合并。
- https://physics.nankai.edu.cn/535/list.htm → C02；与新增候选首屏文章标识相同；父栏目默认视图不重复启用。

## 范围复核与限制

- 包含物理科研动态。
- 本科/研究生教育整流允许少量新闻。
- 包含学术活动/讲座。
- 包含教学管理工作。
- 排除历史教学成果档案数据库。
- 排除 NKZBB 工作动态。
- 只读取三站同主机公开页面；外链只记录，不扩展采集。

已检查三首页主导航和相关二级导航；全部发现链接和处理理由见 source_audit.json/discovery_review。规则库、表格、教学成果库按标题/导航语义排除，未深爬。

审计仅为当时页面快照；身份/别名和排序结论均限定于样本。无法保证未来改版不变。未解析正文/PDF/Word，未访问外链、认证端点或使用浏览器。robots.txt 三站均返回 404，逐主机顺序低频请求。
审计使用 Python 标准库 urllib 与 lxml；生产阶段仍按 SPEC 使用 requests。拟议 registry 为 JSON 语法的合法 YAML 1.2，全部 enabled=false，明确等待人工审批。

## 验证与人工关口

执行 `python scripts/validate_audit.py`：检查 43 ID、时间、状态证据、代表模板复现、分页与安全；`python -m unittest discover -s tests -v` 验证关键提取与异常反例。
请明确批准上述来源修订与新增候选选择后再进入 Phase B；本次没有隐含批准。
