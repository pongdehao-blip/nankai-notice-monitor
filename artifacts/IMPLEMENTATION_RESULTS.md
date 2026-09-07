# Phase B 实现与验收记录

## 2026-09-07 按需推送版本

本节为当前版本验收；下方固定日报记录仅保留历史背景。用户确认的规则见 [NOTIFICATION_POLICY.md](../config/NOTIFICATION_POLICY.md)。

- 部署提交 `75de8cb406d3266a65630c9155417ec0c6e8ca22`：每 3 小时采集后按待报 NEW、UPDATED 或采集异常发送，凌晨照常执行；无待报内容时安静。取消固定日报及每日一次限制。
- 本地 64 项测试通过，新增覆盖同日多批、夜间更新、日期单独更新、无公告变化时故障提醒、异常发送失败后恢复补报、旧版每日投递日期兼容，以及无新增发现时重试积压。
- [线上自动验收通过](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34112203196)。
- [首次实际运行通过](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34112283346)：北京时间约 18:37，command=watch，delivery=sent，source_failures=0，notices=717。当天 18:12 旧版已成功投递，本次仍成功发送，验证同日后续批次不受旧日期限制。
- 使用原 state 分支与机器人 Secret，未重建基线。固定日报的一次性 Codex 验收跟进已暂停；不增加长期检查或定期备份。GitHub 的计划触发延迟仍属现有平台限制。

## 旧版固定日报验收历史

本地实现已覆盖批准的 47 个来源；J21 保持 `/ddpj/list.htm`，四个批准空栏目 allow_empty=true，四个新增候选补充启用，`/533/` 未启用。

## 已验证

- 实时官网 dry-run：47/47 来源正常，去重后 715 条历史文章，待报事件为 0；未发送真实飞书消息。
- 离线解析：审计的全部 19 个代表性 HTML 样例由生产适配器复现，含三站五种布局、空页、置顶、拆分日期和短末页。
- 自动测试：58 项通过，覆盖来源配置、身份/去重、基线/更新、分页边界、溢出风险保留、条件请求、健康恢复、状态损坏/锁、日报拆分、第二分片失败补报、CLI、Git 状态冲突与工作流。
- 发布检查：3 个工作流配置通过，公开发布文件扫描未发现凭据；本地缓存和试运行状态不发布。
- 日报先持久化捕获状态，再发送；全部分片成功后才设置 reported_at。Git 推送不使用 force。
- 已保留 Phase A 原始 JSON/基线值及人审决策；生产来源表与审计拟议表分离。

## 生产环境验收

目标仓库：https://github.com/pongdehao-blip/nankai-notice-monitor

2026-09-06 已完成生产验证：

- 发布提交：`6fbb51f2650f8f39cf65d961a5d8d8d199604a08`；[Offline acceptance 通过](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34020080675)。
- 用户确认已配置 FEISHU_WEBHOOK 和机器人关键词；仅核验 Secret 名称，未读取密钥。
- [首次生产基线成功](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34022915737)：47/47 来源 initialized=true，715 条历史通知，events=0，来源异常为 0。
- [真实日报成功](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34023101252)：北京时间约 16:54，delivery=sent，来源异常为 0；飞书接口确认成功，最终状态提交为 `94b4f1ef622765696b0e7ad200352493d9f0b580`。
- 定时工作流处于 active。当天已成功投递，因此 9 月 6 日 17:42 仍采集但跳过重复日报；下一次应发送的定时日报为 9 月 7 日 17:42（GitHub 调度可能延迟）。

尚待用户确认群内消息可见，以及实际定时触发后的心跳到达。未观察到下一次定时投递前，不声明定时端到端验收全部完成。
