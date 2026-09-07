# Nankai Notice Watch v1

日常维护入口：[一页操作清单](MAINTENANCE_CHECKLIST.md)。

监测南开大学物理科学学院、教务部、招投标管理办公室的公开通知列表，每 3 小时采集，**每轮结束后按需推送 NEW 新增、UPDATED 更新或采集异常**，凌晨同样发送。无待报变化且无异常时保持安静。

生产来源表是 [config/sources.yaml](config/sources.yaml)：43 个基线来源加上经用户批准的 4 个候选，共 **47 个来源**。
J21 保留 `/ddpj/list.htm`，只允许 J09/J10/J13/J14 当前为空；`/533/` 和曝光台未启用。
审批决定见 [APPROVAL.md](config/APPROVAL.md)，历史审计见 [SOURCE_AUDIT_RESULTS.md](artifacts/SOURCE_AUDIT_RESULTS.md)。审计快照中的 pending 字段保留历史含义，不是当前生产审批状态。

## 采集和报告范围

- 包含科研动态、完整本科/研究生教育栏目、学术讲座、教学管理工作、采购公告/结果/意向。
- 按批准栏目整流采集，不使用 AI、不做正文分类，不读取文章正文或 PDF/Word 附件。
- 列表中的外链仅保留标题、日期和链接，不访问外站；不自动扩展来源。
- 新状态先建立每来源最多两页的历史基线，历史文章不发 NEW；失败来源在恢复后单独初始化。
- Physics/JWC 使用经审计验证的同站 CMS 文章 ID 去重，NKZBB 用规范 URL；同一文章关联多个栏目只展示一次。
- 同一栏目内已有文章的标题或日期改变产生 UPDATED；消失不产生 REMOVED。跨栏目旧副本差异不会反复产生更新。
- 每次推送包含所有未报告事件，包括前几天积压事件。多次变更合并展示当前版本及变更数；状态中保留各事件。

消息保留“南开通知日报”固定前缀以兼容现有机器人关键词，并显示本轮采集开始时间。当前不是固定日报；同一天可以发送多批通知。

## Windows 本地安装

安装 Python 3.11 或更新版本，在项目根目录运行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/validate_audit.py
.\.venv\Scripts\python.exe scripts/check_release.py
```

所有测试使用公开脱敏样例和模拟 HTTP；没有测试会向真实飞书机器人发消息。
本程序只有一次性命令，无常驻调度服务。请从项目根目录运行，或通过 `--config` 指定来源表。

```powershell
# 真实访问批准的官网，建立本地历史基线
.\.venv\Scripts\python.exe -m nankai_watch crawl --state-path .runtime/state.json

# 再次采集并预览通知；无需飞书密钥，不发送，也不把事件标记为已报告
.\.venv\Scripts\python.exe -m nankai_watch watch --state-path .runtime/state.json --dry-run --report-path .runtime/daily-preview.json

# 已在当前进程安全配置 FEISHU_WEBHOOK 时，执行按需推送
.\.venv\Scripts\python.exe -m nankai_watch watch --state-path .runtime/state.json
```

`--dry-run` 会保存采集状态，仅跳过发送和报告确认。
`watch` 会发送所有待报 NEW/UPDATED 和异常，包括此前发送失败的积压；没有待报内容则输出 `no_changes`，不调用飞书。兼容命令 `daily` 采用相同规则，不再有每日一次限制。`--force-report` 仅供人工显式发送无变化心跳，不会重发已确认事件；自动工作流不使用此参数。
退出码：0 成功；2 有来源异常但状态已保存；1 配置、状态或投递失败。日志不打印凭据或原始响应。

## GitHub 部署

目标公开仓库：[pongdehao-blip/nankai-notice-monitor](https://github.com/pongdehao-blip/nankai-notice-monitor)。使用标准 GitHub 托管 runner，无需服务器、数据库或付费服务。

1. 将项目文件放在默认分支根目录，确认 **Offline acceptance** 工作流通过。
2. 在飞书目标群添加自定义机器人，关键词配置为 **南开通知日报**。复制 Webhook 后，只填入 GitHub 仓库 **Settings → Secrets and variables → Actions → New repository secret**，名称 `FEISHU_WEBHOOK`。不要放到代码、聊天、Issue 或仓库文件中。
3. 在 **Actions** 中启用工作流。仓库须允许工作流写入 contents；程序只请求状态分支持久化需要的写权限。
4. 手动运行 **Collect and notify → Run workflow**。首次自动创建独立 `state` 分支，建立历史基线；无异常时不发送历史通知或心跳。已有生产状态直接沿用，不重新初始化。
5. 检查 `state` 分支的 `state.json`：47 个 sources 的 initialized 应为 true；全新基线 events 应为空，已有状态则保留原事件和报告标记。
6. 运行后查看日志：`sent` 表示本批通知获飞书确认；`no_changes` 表示没有待报内容，保持安静。**Manual collect and notify** 是采用相同规则的手动备用入口，不另设定时任务。首次真实新增或故障到来时核对群内消息。

不需要预建 state 分支。若 state 分支已经存在却缺少/损坏 state.json，程序拒绝静默重建。
定时和手动入口共享 `nankai-notice-state` 并发组，`cancel-in-progress: false`。状态推送采用普通快进；有竞争修改时失败并保留恢复文件，绝不强推覆盖。

日报在发送前先提交捕获的待报状态到 state 分支。只有所有飞书分片确认成功，才标记事件已报告并再次保存。
发送失败时事件和异常保持待报，下一轮或手动重试会补报，即使下一轮没有新发现。远端最终保存失败时，可能重复发送已经送达的分片；这是优先不漏报的至少一次语义。

## 定时与运行检查

北京时间计划采集时间：02:42、05:42、08:42、11:42、14:42、17:42、20:42、23:42。每轮采集后按需发送，全天执行；`daily-report.yml` 仅保留手动入口，取消独立 17:42 日报。
工作流使用 `timezone: Asia/Shanghai`，与当前 [GitHub schedule 文档](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)一致。

GitHub 调度可能延迟。公开仓库长期无活动时，定时工作流可能自动停用；检查 Actions 是否显示 disabled，点击 **Enable workflow** 后手动运行一次，确认执行结果恢复。
无消息不等于故障：优先查看 Actions 最近运行和 state.json 的来源 `last_success_at`。`delivery.last_success_at` 只在实际发送成功时更新，不能用来判断安静期间的采集是否正常。每轮存在采集故障时，即使无公告变化也单独报告；同一故障持续会每轮提醒，恢复后无其他待报内容则安静。若异常消息此前未送达，恢复后仍补报并注明已恢复。整个工作流未触发时，程序自身无法发送异常提醒。按用户决定，不增加长期自动运行检查或状态定期备份。

## 故障恢复

- **暂时网络/解析错误**：其余来源继续采集。待报队列保留尚未成功送达的异常及其恢复信息；即使运行历史清理，尚未报告的异常也保留。
- **飞书拒绝/超时**：检查 Secret、机器人关键词设置，手动运行 Collect and notify。所有分片未全部成功前，不清空任何待报事件。
- **采集溢出**：默认每来源最多 3 页。未到达原有已知边界时保留 OVERFLOW_RISK，后续正常运行也不会因刚采到的内容成为“已知”而误清除警告。通过提高有限页数恢复，不能无界深爬。
- **状态竞争/推送失败**：从失败运行的 public-state-recovery-* 下载公开状态样本，与 state 分支核对；不要用较旧文件覆盖较新分支。先解决竞争写入再重跑。
- **状态损坏**：从 state 分支上一有效提交恢复 state.json，保留损坏文件供排查；不要删除整个状态来“解决”错误。
- **本地进程异常退出留下锁**：确认没有采集进程运行后，才删除对应 .lock 文件重试。

恢复页数命令（在批准的本地状态副本上执行，范围 1–100）：

```powershell
.\.venv\Scripts\python.exe -m nankai_watch crawl --state-path .runtime/state.json --max-pages 20
```

本地 CLI 不含 Git 操作，不会自动把本地状态同步回生产分支。生产恢复须审核状态差异后提交至 state 分支，或调整工作流的有界恢复参数后执行；不要把本地测试基线覆盖生产状态。

## 数据与项目结构

状态使用 JSON：notices、events、sources、incidents、runs、delivery。运行历史保留最近 7 天且最多 100 次；通知身份、事件及未报告异常保留，避免去重信息丢失。
本地写入为同目录临时文件 + fsync + 原子替换，并有排他锁。

src/nankai_watch/ 中解析、URL/身份、事件、状态、HTTP、日报各自分离；scripts/state_branch.py 与 scripts/run_action.py 负责 GitHub 基础设施。
tests/fixtures/audit/ 是代表性脱敏页面；.audit-cache/ 和 .runtime/ 是忽略的本地数据，不发布。

## 来源修改流程

先审计再启用。新栏目必须检查同主机、列表结构、空源、分页、身份和范围，并补充离线样例。审核后更新 config/sources.yaml 与审批记录。
原审计工具仍可运行，输出保持独立，不覆盖生产来源表：

```powershell
.\.venv\Scripts\python.exe scripts/audit_sources.py
.\.venv\Scripts\python.exe scripts/build_audit.py
.\.venv\Scripts\python.exe scripts/discover_sources.py
.\.venv\Scripts\python.exe scripts/identity_evidence.py
.\.venv\Scripts\python.exe scripts/finalize_audit.py
```

审计工具会复用 .audit-cache/，每条保留实际抓取时间。重新实时审计前先将缓存目录改名留档；审计解释脚本针对本次网站证据，未来必须重新审查。

验收证据见 [IMPLEMENTATION_RESULTS.md](artifacts/IMPLEMENTATION_RESULTS.md)，限制见 [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)。飞书接口依据 [官方自定义机器人指南](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)，JSON 按 UTF-8 字节保守拆分为不超过 18 KB 的分片。
