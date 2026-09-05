"""Apply explicit audit interpretations; never approves a registry."""
from build_audit import *

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def main():
    data=load('artifacts/source_audit.json')
    discovery=load('artifacts/discovery_inspection.json')
    evidence=load('artifacts/identity_evidence.json')
    fixtures=load('artifacts/fixture_manifest.json')
    sources=data['sources']
    byid={r['source_id']:r for r in sources}
    # Semantic corrections are proposals, separate from observed HTTP final URLs.
    byid['J21'].update(audit_status='STRUCTURE_CHANGED',proposed_url='https://jwc.nankai.edu.cn/kcddypj/list.htm',notes='基线 /ddpj/ 是“督导评价”父栏目，当前显示“课堂评价”默认子流；首页/侧栏明确链接 /kcddypj/。二者近期 7 条完全相同。建议保留 J21 ID，改用明确子栏目 URL；这不是 HTTP 重定向。')
    byid['J22'].update(audit_status='STRUCTURE_CHANGED',proposed_name='教学督导',notes='官网栏目名为“教学督导”，基线“课程督导”应更名；URL 保持不变。')
    overlap=[]
    for pos,a in enumerate(sources):
        for b in sources[pos+1:]:
            if a['site_id']!=b['site_id']:
                continue
            aa={identity(i,a['site_id']) for i in a['items_page1']}
            bb={identity(i,b['site_id']) for i in b['items_page1']}
            common=aa&bb
            if not common:
                continue
            titlea={(i['title'].strip(),i['publish_date']) for i in a['items_page1']}
            titleb={(i['title'].strip(),i['publish_date']) for i in b['items_page1']}
            ratio=len(common)/max(len(aa),len(bb))
            row=dict(source_ids=[a['source_id'],b['source_id']],shared_identities=sorted(common),overlap_ratio=ratio,exact_url_overlap=len({i['url'] for i in a['items_page1']}&{i['url'] for i in b['items_page1']}),title_date_overlap=len(titlea&titleb),redundant_candidate=ratio>=.8)
            overlap.append(row)
            if ratio>=.8:
                a['duplicate_source_candidates'].append(b['source_id'])
                b['duplicate_source_candidates'].append(a['source_id'])
    candidates=[]
    candidate_slugs={'536':('本科生教育（导航旧流）','同名独立通知流，近期样本停于 2021 年；不能因陈旧而静默丢弃。'),
        '547':('研究生教育（导航独立流）','包含 2024 年论文答辩通知，与 P03 当前首页不同。'),
        '575':('科研动态（首页流）','包含奖励申报公示，与 P09 近期内容部分重合但不是完整别名。'),
        'xkjs':('学科竞赛（父栏目直属流）','包含 2026-09-04 竞赛通知，J07 子栏目未覆盖；建议新增而非替换。')}
    ambiguous={'533':'包含讲座预告，也有大量学术会议回顾；是否按学术活动整流纳入需审核。',
               'pgt':'曝光台为空，是否属于采购公示范围需要用户决定；不自动列为已验证新增来源。'}
    for row in discovery:
        slug=urlsplit(row['url']).path.split('/')[1]
        if row.get('decision')!='review':
            continue
        site=urlsplit(row['url']).hostname.split('.')[0]
        matches=[]
        ids={identity(i,site) for i in row['items']}
        for r in sources:
            old={identity(i,site) for i in r['items_page1']}
            if ids and ids==old and r['site_id']==site:
                matches.append(r['source_id'])
        if matches:
            row.update(decision='alias_candidate',matching_source_ids=matches,reason='首屏文章标识集合完全一致；仅证明当前窗口重合，不保证长期等价，不自动合并。')
        elif slug in candidate_slugs:
            name,reason=candidate_slugs[slug]
            row.update(decision='in_scope_candidate',name=name,reason=reason)
            rec=audit(dict(source_id='C'+str(len(candidates)+1).zfill(2),site_id=site,name=name,candidate_url=row['url'],source_type='education' if slug in ('536','547') else 'research_mixed' if slug=='575' else 'student_affairs',allow_empty_baseline=False,priority=999),fixtures)
            rec.update(enabled=False,approval_status='pending',rationale=reason)
            candidates.append(rec)
        elif slug in ambiguous:
            row.update(decision='scope_decision_required',reason=ambiguous[slug])
        elif row['items']:
            row.update(decision='excluded',reason='样本为规章/成果档案或一般活动回顾，按冻结范围排除。')
        else:
            row.update(decision='not_confirmed_stream',reason='父栏目/空服务入口，没有发现未覆盖的实际通知；已检查二级导航，不因零提取推断有效空源。')
    # Compare navigation aliases against newly discovered candidates too.
    for row in discovery:
        if row.get('decision')!='excluded' or not row.get('items'):
            continue
        site=urlsplit(row['url']).hostname.split('.')[0]
        ids={identity(i,site) for i in row['items']}
        for candidate in candidates:
            if candidate['site_id']==site and ids=={identity(i,site) for i in candidate['items_page1']}:
                row.update(decision='alias_candidate',matching_source_ids=[candidate['source_id']],reason='与新增候选首屏文章标识相同；父栏目默认视图不重复启用。')
    # Preserve page-2 evidence for each pagination/layout variant, plus pinned/identity case.
    for sid in ('P01','P02','P03','J01','J02','Z01','Z04','Z09'):
        r=byid[sid]
        for page,u in [(1,r['final_url']),(2,r['pagination']['page2_url'])]:
            if not u:
                continue
            if page==1 and sid not in ('P02','P03','J01'):
                continue
            rr=fetch(u)
            _,_,items=parse(rr['html'],r['site_id'],u)
            key=sid+'-page'+str(page)
            p='tests/fixtures/audit/'+key+'.html'
            (ROOT/p).write_text(rr['html'],encoding='utf-8')
            fixtures[key]=dict(path=p,source_id=sid,url=u,items=items,site_id=r['site_id'],fetched_at=rr['fetched_at'])
    for r in sources:
        r['allow_empty_proposed']=r['allow_empty_observed']
        r['allow_empty_rationale']='仅对本次证实为空的栏目允许空；已有文章栏目突然变空应报警。休眠不等于允许解析失败。'
        r['article_identity']['fallback']='normalized canonical URL, preserve unproven query parameters'
        r['article_identity']['evidence_file']='artifacts/identity_evidence.json'
        if r['site_id']=='jwc':
            r['article_identity']['template_normalization']='_t12 probe returned HTTP 302 without following; do not approve generic JWC template stripping'
        elif r['site_id']=='physics':
            r['article_identity']['template_normalization']='_t12 and ordinary article URLs returned 200 with matching document titles; evidence limited to tested sample'
        for i in r['items_page1']+r['pagination']['items_page2']:
            match=re.search(r'/(\d{4})/(\d{2})(\d{2})/',i['url'])
            if match and '-'.join(match.groups())!=i['publish_date']:
                warning='URL path date differs from displayed publish date; use displayed date'
                if warning not in r['warnings']:
                    r['warnings'].append(warning)
        if r['items_page1'] and max(i['publish_date'] or '' for i in r['items_page1'])<'2025-01-01':
            r['warnings'].append('Dormant recent sample; retain baseline source, do not infer missing')
    data['new_candidate_sources']=candidates
    data['discovery_review']=discovery
    data['identity_evidence']=evidence
    data['source_overlap']=overlap
    data['summary']={key:0 for key in ('pass','pass_empty','redirected','structure_changed','missing','other_failures')}
    for r in sources:
        key=r['audit_status'].lower()
        data['summary'][key if key in data['summary'] else 'other_failures']+=1
    data['phase_b_approved']=False
    data['scope_policy']=['包含物理科研动态','本科/研究生教育整流允许少量新闻','包含学术活动/讲座','包含教学管理工作','排除历史教学成果档案数据库','排除 NKZBB 工作动态','只读取三站同主机公开页面；外链只记录，不扩展采集']
    dump('artifacts/source_audit.json',data)
    dump('artifacts/fixture_manifest.json',fixtures)
    registry=dict(schema_version=1,approval_status='pending_human_review',production_ready=False,sources=[],new_candidate_sources=[])
    for r in sources:
        registry['sources'].append(dict(source_id=r['source_id'],site_id=r['site_id'],name=r.get('proposed_name',r['name']),url=r.get('proposed_url',r['final_url']),baseline_url=r['candidate_url'],source_type=r['source_type'],priority=r['priority'],allow_empty=r['allow_empty_proposed'],enabled=False,approval_status='pending',audit_status=r['audit_status'],layout_group=r['layout_group'],selectors={k:r[k] for k in ('list_selector','item_selector','title_selector','date_selector','link_selector')},pagination=r['pagination']['transformation'] if 'transformation' in r['pagination'] else None,notes=r['notes']))
    registry['new_candidate_sources']=[dict(source_id=r['source_id'],name=r['name'],url=r['candidate_url'],enabled=False,approval_status='pending') for r in candidates]
    (ROOT/'config').mkdir(exist_ok=True)
    # JSON is valid YAML 1.2, avoiding a second serialization dependency in Phase A.
    dump('config/sources.audit-proposed.yaml',registry)
    write_report(data,fixtures)
    print(data['summary'], 'new candidates',len(candidates), 'fixtures',len(fixtures))

def write_report(data,fixtures):
    rows=['# 南开通知监测：Phase A 实时来源审计','',f"审计生成时间：{data['audited_at']}（UTC；每个请求另有实际抓取时间）。",'',
        '**当前仅完成审计交付，Phase B 未获批准。未创建正式监控、飞书投递、状态分支或定时工作流。**','',
        '## 结论','',f"43 个基线 ID 完整保留。状态：{json.dumps(data['summary'],ensure_ascii=False)}。所有基线首页 HTTP 200，无 HTTP 重定向或失效来源。",'',
        '四个有效空栏目：J09 实习实践、J10 语言文字、J13 试卷印刷、J14 课程思政通知。证据是明确选中导航、正确标题、已知列表容器实际空白且没有翻页；不是单凭选择器返回零。',
        '所有非空基线的分页已核验：有第二页的实际请求第二页；不足一页且无翻页控件的标为 none。采购其他类第二页分别只有 12 和 7 条，是正常末页。','',
        '## 需要审核的具体方案','',
        '1. J21 保留 ID，将 https://jwc.nankai.edu.cn/ddpj/list.htm 改为 https://jwc.nankai.edu.cn/kcddypj/list.htm。前者是父栏目默认视图，后者是导航明确子栏目；近期 7 条相同。J22 名称由“课程督导”改为“教学督导”，URL 不变。',
        '2. 建议 allow_empty 仅对上述四个已证实空栏目设 true，其余设 false；已存在文章的栏目突然为零应报错。基线值全部保留在 JSON 中。',
        '3. 审核下表四个新增候选；建议补充而不替换既有流。另 /533/ 学术活动含讲座和较多回顾，曝光台为空，二者范围存疑，暂不启用。',
        '4. 物理科研/教育列表有指向新闻站、微信公众号等外链。建议保留官网列表提供的标题、日期和链接，但不请求外站；请确认是否接受这一解释。',
        '5. P03/J01 等有置顶或非严格日期排序，必须使用稳健已知边界，不能“遇到第一条旧文章就停止”。列出的教学工作流中也夹有规章和工作回顾：建议按批准栏目整流采集，不做正文分类。','',
        '## 43 个基线来源','',
        '| ID | 栏目 | 状态 | 首页条数 | 分页 | 备注 |','|---|---|---|---:|---|---|']
    for r in data['sources']:
        notes=r['notes'] or '；'.join(r['warnings']) or '已验证'
        rows.append(f"| {r['source_id']} | [{r['name']}]({r['final_url']}) | {r['audit_status']} | {r['item_count_page1']} | {r['pagination']['kind']} | {notes} |")
    rows += ['', '## 新增候选（全部未启用）','','| ID | 栏目 | 理由 |','|---|---|---|']
    for r in data['new_candidate_sources']:
        rows.append(f"| {r['source_id']} | [{r['name']}]({r['candidate_url']}) | {r['rationale']} |")
    rows += ['', '## 模板、分页与离线证据','',
        '五种 DOM 布局：Physics `#wp_news_w6`；JWC `.page-con-list-news` 拆分年月日和 `.page-con-list-news1` 整体日期；NKZBB `#datab > dd` 与意向公开 `dl.llist > dd`。另保存有效空、单页、置顶、第二页和末页样例。',
        'Physics/JWC：跟随官网 list2.htm，后续路径 list{n}.htm。NKZBB：9 个栏目实测 GET `index.chtml?curPage=2`，返回第二页范围与不同文章。UI 虽用 AJAX/POST，但无需浏览器、Cookie 或不透明表单字段；所有请求都为公开 GET。',
        '标题优先取 a/@title（防止采购意向正文截断），其次锚文本。日期取列表展示值，不能从文章 URL 的年月日推断。JSON 中逐条保留分页 URL、第二页样本、排序、跨页重复证据。',
        f'当前保存 {len(fixtures)} 个代表性 fixture，清单见 fixture_manifest.json。已删除脚本、输入字段、图片、追踪与无关属性；不存响应 Cookie/Authorization。','',
        '## 身份与重复分析','',
        r'Physics/JWC 建议同站点 `article_id`：`/c\d+a(\d+)/page\.htm$`。类别 c 编号不参与身份；不匹配时保留规范 URL。NKZBB 用完整规范 URL，未证明数字 ID 可跨分类合并。',
        'Physics 的普通、_t12、不同 c 类别三种 URL 元数据标题一致；JWC 不同 c 类别标题一致，但 _t12 返回 302，未跟随，因此不批准 JWC 通用模板路径剥离。完整 URL/状态/时间在 identity_evidence.json。',
        '基线内首屏重合结果如下。高重合只是候选，不自动合并；样本窗口不能证明整个历史流冗余。','',
        '| 来源对 | 相同身份数 | 重合率（除以较大集合） | 源冗余候选 |','|---|---:|---:|---|']
    for row in data['source_overlap']:
        rows.append(f"| {' / '.join(row['source_ids'])} | {len(row['shared_identities'])} | {row['overlap_ratio']:.0%} | {'是' if row['redundant_candidate'] else '否，仅文章去重'} |")
    rows+=['','导航别名候选：']
    for row in data['discovery_review']:
        if row['decision']=='alias_candidate':
            rows.append(f"- {row['url']} → {', '.join(row['matching_source_ids'])}；{row['reason']}")
    rows+=['','## 范围复核与限制','']+[f'- {p}。' for p in data['scope_policy']]
    rows+=['','已检查三首页主导航和相关二级导航；全部发现链接和处理理由见 source_audit.json/discovery_review。规则库、表格、教学成果库按标题/导航语义排除，未深爬。','',
        '审计仅为当时页面快照；身份/别名和排序结论均限定于样本。无法保证未来改版不变。未解析正文/PDF/Word，未访问外链、认证端点或使用浏览器。robots.txt 三站均返回 404，逐主机顺序低频请求。',
        '审计使用 Python 标准库 urllib 与 lxml；生产阶段仍按 SPEC 使用 requests。拟议 registry 为 JSON 语法的合法 YAML 1.2，全部 enabled=false，明确等待人工审批。','',
        '## 验证与人工关口','',
        '执行 `python scripts/validate_audit.py`：检查 43 ID、时间、状态证据、代表模板复现、分页与安全；`python -m unittest discover -s tests -v` 验证关键提取与异常反例。',
        '请明确批准上述来源修订与新增候选选择后再进入 Phase B；本次没有隐含批准。']
    (ROOT/'artifacts/SOURCE_AUDIT_RESULTS.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
