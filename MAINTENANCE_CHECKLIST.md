# 南开通知监测｜一页维护清单

**运行位置：GitHub Actions 云端。电脑关机不影响采集和日报；本地文件用于修改与测试。**

**计划时间（北京时间）：**02:42、05:42、08:42、11:42、14:42、17:42、20:42、23:42 采集；每轮结束后有新增、更新或采集异常就发送，凌晨同样执行；无待报内容时不发消息。计划触发和执行可能延迟。

**常用入口：**[运行记录 Actions](https://github.com/pongdehao-blip/nankai-notice-monitor/actions) · [飞书 Secret 设置](https://github.com/pongdehao-blip/nankai-notice-monitor/settings/secrets/actions) · [生产状态及历史](https://github.com/pongdehao-blip/nankai-notice-monitor/blob/state/state.json)

## 日常检查

- [ ] 收到消息时查看新增、标注“更新”的公告及“系统健康”；无消息可能只是没有变化。
- [ ] 每月人工查看 Actions 最近运行是否正常、工作流是否启用；本清单不创建提醒。

## 出现异常时

| 看到的情况 | 操作 |
|---|---|
| 想确认是否正常运行 | 打开 Actions → **Collect and notify**，查看最近运行。排队或运行中先等待；成功日志 `no_changes` 表示无待报内容，`sent` 表示发送成功。 |
| 红色失败标记 | 打开失败运行及失败步骤，记录错误和运行链接。网络偶发失败可待恢复后手动运行一次；持续失败交给维护者排查。红色标记也可能只是某栏目异常，需同时查看投递结果。 |
| 定时工作流被停用 | 在对应工作流页面选择 **Enable workflow**，然后手动运行一次并确认结果。 |
| 飞书发送失败或机器人更换 | 更新 Secret **FEISHU_WEBHOOK**；确认机器人关键词为 **南开通知日报**，然后手动运行 Collect and notify。密钥只填在 Secret 中。 |
| 栏目持续异常、突然为空或出现 OVERFLOW_RISK | 提供栏目编号和运行链接，排查官网改版、网络或分页边界；不要为消除报警直接放宽 allow_empty。 |
| 出现 STATE_ERROR 或状态推送失败 | 保留运行链接和恢复文件，交给维护者检查状态历史与冲突；不要删除 state 分支、清空 state.json 或用本地试运行状态覆盖生产状态。 |

**手动运行：**Actions → 选择工作流 → **Run workflow** → 分支选 **main** → 确认运行。**Collect and notify** 为定时/手动主入口；**Manual collect and notify** 为手动备用入口。两者均先采集，再按待报事件或异常决定是否发送，同日可以发送多批。一次失败后重试可能重复已送达的部分消息，程序优先保留待报信息。

## 修改与交接

- [ ] 改栏目：先审核官网列表，再更新 `config/sources.yaml` 和审批记录；保留原基线值及批准范围。
- [ ] 改程序或时间：修改对应代码或工作流，完成适当测试并推送 `main`；确认 **Offline acceptance** 通过，再检查实际运行。本地修改不会自动上线。
- [ ] 求助时提供：**异常时间、栏目编号（如有）、Actions 运行链接、飞书现象**；不要提供 Webhook。

**已确认的维护范围：**暂不设置长期自动运行检查，不增加状态文件定期备份；原有 `state` 分支运行状态提交和 Git 历史继续保留。固定日报及其一次性验收已由本次按需推送方案取代。持续采集故障每轮提醒；程序本身未启动时无法发送提醒。

详细流程见 [README](README.md)。本清单更新于 2026-09-07。
