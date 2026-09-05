# 来源审批记录 — 2026-09-05

用户已明确审核 Phase A 并授权实施：

1. J21 URL 保持 `https://jwc.nankai.edu.cn/ddpj/list.htm`，不采用审计提出的替代地址。
2. allow_empty 仅 J09/J10/J13/J14 为 true，其余 false；曾经出现文章的栏目突然归零必须报错。原始基线值保留在 source_baseline.json、审计 JSON 及批准注册表内。
3. 补充四个候选 C01–C04；Physics `/533/` 暂不启用，曝光台未获启用批准。
4. 保留官网列表上的标题、日期和链接，外站链接不请求。
5. 按批准栏目整流采集，不做正文分类。

J22 使用审计核实的官网名称“教学督导”；仅名称修订，不改变 URL/范围。

`sources.yaml` 是批准后的 47 来源注册表。`sources.audit-proposed.yaml` 与 `artifacts/source_audit.json` 保留原始审计时刻的待审批快照，不能据其旧字段重新阻止已批准的 Phase B，也不能将它们当作生产配置。

任何新的栏目启用仍须独立审计并获批准。
