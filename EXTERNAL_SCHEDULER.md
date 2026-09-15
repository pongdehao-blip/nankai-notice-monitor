# 外部每小时触发

2026-09-15 切换：cron-job.org → GitHub workflow_dispatch → 现有 watch 程序。
GitHub 内置 schedule 在以下两阶段验收后移除；保留 workflow_dispatch 和工作流启用状态。

## 配置

- URL：`https://api.github.com/repos/pongdehao-blip/nankai-notice-monitor/actions/workflows/crawl.yml/dispatches`
- 方法：POST；JSON 正文：`{"ref":"main"}`。
- 时区：Asia/Shanghai；每天所有小时，分钟仅 42（`42 * * * *`）。
- Authorization：Bearer 加一个英文空格及专用 GitHub 令牌，仅在 cron-job.org 保存。
- Accept：`application/vnd.github+json`；Content-Type：`application/json`。
- X-GitHub-Api-Version：`2026-03-10`；Basic authentication 关闭。
- GitHub 细粒度令牌：Resource owner 为 pongdehao-blip；Only select repositories 选中 nankai-notice-monitor；Repository Actions 为 Read and write；保留自动附带的 Metadata 只读权限。无需 Interaction limits 账户权限。
- 保留响应以便查看历史；请求失败 1 次即邮件通知，并建议开启恢复及自动停用邮件。邮件设置已获用户授权，但本次未取得控制台设置证据，仍需用户确认已保存。

## 验收证据（北京时间）

| 阶段 | 证据 | 结果 |
|---|---|---|
| 手动外部测试 | [34943439613](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34943439613)，15:46:39 | workflow_dispatch，success；sent，source_failures=0；用户确认飞书收到 |
| 第二次外部测试 | [34943522136](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34943522136)，15:47:39 | cron-job.org 200；success，no_changes，source_failures=0 |
| 真实定时 | [34953955805](https://github.com/pongdehao-blip/nankai-notice-monitor/actions/runs/34953955805)，17:42:10 | 外部历史显示17:42:07执行，200正文直接返回同一运行ID；workflow_dispatch，success，no_changes，source_failures=0，notices=758 |

定时运行的生产状态提交：`ab0a89a4e635732c921167063da52ff93a655c05`（17:43:21）。
手动投递后的状态提交：`ead79fc8c8da6d62f815676545f41d4228ea77d8`（15:47:51）。
运行成功、状态持久化及按需通知已分别核对；无变化时不要求飞书消息。

## 403 原因与维护

原始错误为 `Resource not accessible by personal access token`，响应声明接口需要 `actions=write`。
用户截图显示原令牌只有公开仓库只读及账户 Interaction limits 权限；修正目标仓库和 Actions 写权限后测试成功。
无需修改 FEISHU_WEBHOOK、来源、state 或通知排版。

响应所示令牌到期时间为 2026-12-08 16:07:56 UTC，即北京时间 2026-12-09 00:07:56；到期前人工续期或更换。
修改同一令牌权限通常无需替换令牌字符串；生成或重新生成令牌后，必须在 cron-job.org 更新 Authorization 并保存，做一次测试及真实定时核验。令牌不写入仓库或聊天。

排错时关联外部历史与响应运行 ID；HTTP 200 仅表示 GitHub 接受请求。继续检查工作流完成状态、日志 sent/no_changes、source_failures 和 state 提交。
触发失败邮件不能发现 GitHub 后续采集失败；不另增长期监控或定期备份。
切勿 Disable 整个工作流；不得删除或清空生产 state。外部服务或 runner 可能延迟，本次验收不代表长期准点保证。
