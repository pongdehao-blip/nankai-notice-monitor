# Phase B 实现与验收记录

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
