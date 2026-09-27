/* Guided presentation over the same immutable trace used by the overview. */
window.ExplainerGuide = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fields = {claim:'Claim',claim_date_raw:'日期',speaker:'说话者',reporting_source:'发布来源',location_ISO_code:'地区',original_claim_url:'原始发布链接'};
  const plans = {
    infact: {
      q:['生成核查问题','把一条 claim 拆成需要查证的问题。','Claim 与本系统使用的 metadata','pose_questions'],
      g:['为问题生成查询','同一模板，每次填入一个不同问题；按顺序处理。','当前问题 + claim 记录','propose_queries.'],
      s:['搜索并筛选网页','按查询取搜索结果，下载正文，再执行日期政策。','当前问题生成的查询','search.'],
      a:['根据网页尝试回答','每次处理“一个问题 + 一页正文”；返回 NONE 就继续，首次答出即停。','当前问题 + claim 记录 + 当前页面正文','answer.'],
      output:['汇总证据与判决','把答出的问答交给模型判决，再单独生成总结。','Claim + 已答出的问答与来源','judge.','summarize_doc']
    },
    hero2: {
      h:['写假想核查文章','这些是假想内容，不是证据，用于描述要寻找的信息。','Claim 文本','hyde.'],
      qq:['准备搜索查询','用 claim 原文和每篇假想文章的首句生成查询；这一步不调用模型。','Claim + 假想文章首句'],
      sf:['搜索并筛选网页','claim 查询请求 10 条结果，其他查询各请求 5 条。','已准备的查询','web_search'],
      r:['选择相关页面','用 GTE 向量比较 claim、假想文章与网页，选出候选。','放行网页 + claim 与假想文章'],
      sm:['为页面生成摘要','每篇单独生成一段摘要；不把摘要当作网页逐字原文。','检索选中的网页正文','summary.'],
      qg:['为证据生成问题','先有证据，再为摘要生成连接 claim 与证据的问题。','Claim + 摘要 + 训练集示例','qg.'],
      rw:['将摘要改写为回答','按问题改写摘要，模型返回 none 的结果丢弃。','Claim + 问题 + 摘要','rewrite.'],
      output:['根据问答判决','把保留下来的问答交给模型，生成判决及解释。','Claim + 保留的问答','vp.']
    },
    sanctuary: {
      hq:['生成假想问答','假想答案只指导检索，不作为最终证据。','Claim + 日期、说话者、地区、发布来源','qg.'],
      ss:['搜索并筛选网页','每个问题作为查询，请求 10 条结果，再抓取正文和过滤日期。','生成的问题','web_search'],
      bm:['用 BM25 筛选段落','每个问题结合假想答案检索段落，再按来源页面合并。','放行页面 + 问题和假想答案'],
      ck:['按语义切块','使用 Chonkie 与本地嵌入模型；大于 160 token 的块丢弃。','BM25 选中的文档'],
      ev:['选择证据片段','每问题先取相似度前 20 块，过滤低于 0.52 的块，再做近似去重。','问题 + 语义块'],
      output:['读取片段并判决','把问题、选中片段及来源一起送入模型。','Claim metadata + 各问题的真实片段','vp.']
    },
    aic_ctu_averitec: {
      as:['搜索并筛选网页','直接用 claim 原文查询，请求 20 条结果。','Claim 文本','web_search'],
      ch:['切块并检索','对候选块做向量检索，再用 MMR 兼顾相关性与多样性。','通过过滤的网页正文'],
      fs:['选择训练集示例','用 BM25 选择 10 条训练集 claim 和人工问答，作为格式示范。','Claim + 训练集'],
      gq:['生成问答与标签分数','同一次模型处理同时生成问答、来源编号和四类标签评分。','候选证据块 + 训练示例 + claim','generate.'],
      lk:['查看标签评分','这里展开上一阶段同一次响应中的四个分数，不增加模型调用。','同一次生成的 claim_veracity 字段'],
      output:['根据评分选择标签','将 Likert 分数映射、做 softmax，选择最大项；不是校准后的置信度。','四类 Likert 分数']
    }
  };
  const queryRows = (sd, system) => system === 'infact' ? sd.trace.questions.flatMap(q=>q.search) : system === 'sanctuary' ? sd.trace.hyde.flatMap(q=>q.search) : sd.trace.search || [];
  const stageRequests = (sd, spec) => (sd.requests || []).filter(r => spec.slice(3).some(prefix => r.stage.startsWith(prefix)));
  const totals = (sd, spec) => Object.entries(sd.execution?.by_stage || {}).filter(([s])=>spec.slice(3).some(p=>s.startsWith(p))).reduce((a,[,v])=>({http:a.http+v.http_attempts,cache:a.cache+v.cache_hits,failed:a.failed+v.failed_attempts}),{http:0,cache:0,failed:0});
  function inputHtml(sd, compact=false) {
    const u = sd.input_usage;
    if(compact) {
      const tags=k=>`${u.model_fields.includes(k)?'<span class="use">模型输入</span>':''}${u.filter_fields.includes(k)?'<span class="use">日期过滤</span>':''}${!u.model_fields.includes(k)&&!u.filter_fields.includes(k)?'<span class="faint">未使用</span>':''}`;
      return `<dl class="input-fields">${Object.entries(u.record).map(([k,v])=>`<div class="input-field"><dt>${fields[k]||esc(k)}</dt><dd class="field-use">${tags(k)}</dd><dd class="field-value">${esc(v ?? '未提供')}</dd></div>`).join('')}</dl><p class="support-note">${esc(u.note)}</p><p class="support-note">${esc(u.gold_note)}</p>`;
    }
    return `<div class="input-table"><table><thead><tr><th>字段</th><th>样本中的值</th><th>实际用途</th></tr></thead><tbody>${Object.entries(u.record).map(([k,v])=>`<tr><th>${fields[k]||esc(k)}</th><td>${esc(v ?? '未提供')}</td><td>${u.model_fields.includes(k)?'<span class="use">模型输入</span>':''}${u.filter_fields.includes(k)?'<span class="use">日期过滤</span>':''}${!u.model_fields.includes(k)&&!u.filter_fields.includes(k)?'<span class="faint">未使用</span>':''}</td></tr>`).join('')}</tbody></table></div><p class="support-note">${esc(u.note)}</p><p class="support-note">${esc(u.gold_note)}</p>`;
  }
  function enrich(model, doc, state) {
    const sd = doc.systems[state.sys];
    model.cols.forEach(col => {
      let spec = plans[state.sys][col.id];
      if(col.id === 'in' || col.items.some(x=>x.id === 'claim')) {
        spec=['共同样本，按系统取字段','四个系统使用同一条数据集记录，但加入模型的字段并不完全相同。','数据集原始 claim 与 metadata'];
        col.items[0].detail=()=>inputHtml(sd);
        col.t='查看本系统实际使用的字段'; col.s='Claim 原文直接读取；没有额外的模型清洗。';
      }
      if(!spec) spec=[col.n.replace(/^[①②③④⑤⑥⑦⑧]\s*/,''),'检索失败，本步没有执行。','无可用输入'];
      col.guide=spec;
      const reqs=stageRequests(sd,spec);
      if(reqs.length) col.calls=`${reqs.length} 次模型处理`;
      else if(spec.some(s=>s==='web_search'||s==='search.')) col.calls=`${queryRows(sd,state.sys).length} 次查询`;
      else col.calls=col.kind==='emb'||col.kind==='alg'?'本地计算':'';
      if(col.id==='lk') col.calls='复用同一次响应';
      if(col.id==='a') col.s=`${sd.trace.questions.reduce((n,q)=>n+q.tried.length,0)} 次问答尝试 · ${new Set(sd.trace.questions.flatMap(q=>q.tried.map(t=>t.url))).size} 个不同 URL`;
      if(col.kind==='llm'&&col.id!=='a') col.s='Gemma-4-26B · OpenRouter';
      if(col.id==='a') col.s+=' · 一次一个问题与页面';
    });
    model.out.guide=plans[state.sys].output;
    const outputRequests=stageRequests(sd, model.out.guide);
    model.out.calls=outputRequests.length?`${outputRequests.length} 次模型处理`:model.out.failed?'未执行模型处理':'本地规则';
  }
  function promptPanel(sd, spec, selectedIndex) {
    const list=stageRequests(sd,spec);
    if(!list.length) return '';
    const index=Math.max(0,Math.min(selectedIndex||0,list.length-1));
    const r=list[index];
    return `<details class="request-panel"><summary>查看实际 prompt 与原始输出 <span>${list.length} 条处理记录</span></summary><div class="request-body"><label for="request-choice">选择处理记录</label><select id="request-choice">${list.map((x,i)=>`<option value="${i}" ${i===index?'selected':''}>${esc(x.stage)}</option>`).join('')}</select><div id="request-content">${requestContent(r)}</div></div></details>`;
  }
  function requestContent(r) {
    if(r.status!=='verified') return `<p class="support-note">${esc(r.display_note)}</p>`;
    const p=r.params;
    return `<p class="request-note">${esc(r.display_note)}</p><dl class="request-params"><dt>模型</dt><dd>${esc(p.model)}</dd><dt>参数</dt><dd>${esc(Object.entries(p).filter(([k])=>k!=='model').map(([k,v])=>`${k}=${JSON.stringify(v)}`).join(' · '))}</dd></dl>${r.messages.map(m=>`<section class="message"><h4>${esc(m.role)}</h4><pre>${esc(m.content)}</pre></section>`).join('')}<section class="message"><h4>原始模型输出</h4><pre>${esc(r.output)}</pre></section><p class="support-note mono">原始消息 SHA256：${esc(r.request_sha256)}</p>`;
  }
  function searchPanel(doc,sd,system) {
    const rows=queryRows(sd,system),e=sd.execution?.search;
    return `<div class="search-stats"><div><strong>${rows.length}</strong><span>查询使用次数</span></div><div><strong>${new Set(rows.map(r=>r.q)).size}</strong><span>不同查询</span></div><div><strong>${e?.http_attempts ?? '—'}</strong><span>本次新 API 请求</span></div><div><strong>${e?.cache_hits ?? '—'}</strong><span>本次缓存复用</span></div></div><details class="method-panel"><summary>具体如何搜索与过滤</summary><ol><li>Serper Google web search；每条查询的请求条数见下方结果。区域 US，语言 en。</li><li>搜索日期参数：1990-01-01 至 ${esc(doc.claim_date)}，只作为预筛。</li><li>通过 URL 获取页面正文，必要时用浏览器抓取；过滤抓取失败、空正文、过短正文。</li><li>日期不明或晚于 claim 的页面排除；修订关键词锚定的明确截止后日期也排除，同日保留。</li><li>去重后交给各系统后续处理。当前版本网页通过筛选，不等于证明是历史版本。</li></ol><p class="support-note">本页是离线运行记录的回放，打开或切换页面不会请求模型或搜索 API。过滤分项由保存的页面数据复算。</p></details>`;
  }
  function outputHtml(doc,sd) {
    return `<div class="verdict-summary"><div><span>系统判决</span><strong>${esc(sd.predicted_label || '无判决')}</strong></div><div><span>Gold 标签</span><strong>${esc(doc.gold_label)}</strong></div><span class="result-status ${sd.label_correct?'correct':'incorrect'}">${sd.label_correct?'判决一致':sd.predicted_label?'判决不一致':'检索失败'}</span></div><p class="support-note">${sd.qa_pairs.length} 组最终问答 · 状态 ${esc(sd.status)} · 旧版 QA Hungarian-METEOR ${sd.legacy_scores?.qa_hu_meteor==null?'未评分':Number(sd.legacy_scores.qa_hu_meteor).toFixed(3)}。词汇匹配评分不验证事实真假。</p>${sd.status==='no_evidence'?'<p class="empty-note">没有问答证据；模型仍对 claim 给出了判决。</p>':''}${sd.status==='retrieval_failed'?'<p class="empty-note">没有可用证据块，后续生成未执行。本条仍保留在评估分母中。</p>':''}<div class="final-qa">${sd.qa_pairs.map((qa,i)=>`<details><summary>Q${i+1} · ${esc(qa.question)}</summary><p>${esc(qa.answer)}</p>${qa.url&&/^https?:\/\//i.test(qa.url)?`<a href="${esc(qa.url)}" target="_blank" rel="noopener noreferrer">${esc(qa.url)}</a>`:'<span class="support-note">未提供对应来源链接</span>'}</details>`).join('')}</div>${sd.trace.vp_text||sd.trace.judge_text?`<details class="method-panel"><summary>查看判决解释</summary><pre>${esc(sd.trace.vp_text||sd.trace.judge_text)}</pre></details>`:''}`;
  }
  function render({model,doc,state,go}) {
    const sd=doc.systems[state.sys], all=[...model.cols, {id:'output',guide:model.out.guide,items:[]}], step=Math.min(state.step,all.length-1), col=all[step], spec=col.guide;
    const host=document.getElementById('guide');
    const requests=stageRequests(sd,spec), network=totals(sd,spec);
    const index=Math.max(0,Math.min(state.focusIndex||0,col.items.length-1));
    const item=col.items[index];
    const isInput=col.items.some(i=>i.id==='claim');
    const isSearch=spec.slice(3).some(p=>p==='search.'||p==='web_search');
    const isOutput=col.id==='output';
    const intro=state.sys==='infact'?'问题按顺序处理：Q1 的查询 → 搜索 → 读页，再处理 Q2。下方按阶段归类展示。':'按本系统实际步骤展示；本地检索和模型生成分别标明。';
    host.innerHTML=`<div class="guide-nav" aria-label="流程步骤">${all.map((x,i)=>`<button data-step="${i}" ${i===step?'aria-current="step"':''}><span>${String(i+1).padStart(2,'0')}</span>${esc(x.guide[0])}</button>`).join('')}</div><div class="guide-heading"><div><p class="eyebrow">STEP ${String(step+1).padStart(2,'0')} / ${all.length}</p><h1>${esc(spec[0])}</h1><p>${esc(spec[1])}</p></div><div class="step-arrows"><button id="previous-step" aria-label="上一步" ${step===0?'disabled':''}>←</button><button id="next-step" aria-label="下一步" ${step===all.length-1?'disabled':''}>→</button></div></div><div class="guided-layout"><article class="work-panel"><div class="io-caption"><span>输入</span>${esc(spec[2])}</div>${isSearch?searchPanel(doc,sd,state.sys):''}${!isOutput&&col.items.length>1?`<div class="item-picker" aria-label="选择当前步骤的项目">${col.items.map((it,i)=>`<button data-item="${i}" ${i===index?'aria-pressed="true"':'aria-pressed="false"'}>${state.sys==='infact'&&col.id!=='q'||['hq','ss','ev'].includes(col.id)?'Q':'#'}${i+1}</button>`).join('')}</div>`:''}${state.sys==='hero2'&&['sm','qg','rw'].includes(col.id)?'<p class="retained-note support-note">这里列出最终保留问答对应的结果；全部处理记录（含丢弃项）可在下方展开。</p>':''}<div class="focus-content">${isOutput?outputHtml(doc,sd):item?.detail?item.detail():`<p class="empty-note">此步没有可展示的结果。</p>`}</div></article><aside class="step-context"><div class="context-card"><p class="eyebrow">这一步如何执行</p>${requests.length?`<strong class="operation-count">${requests.length}<small>次模型处理</small></strong><p>同一个 Gemma-4-26B 模型</p>${col.id==='a'?`<p class="support-note">${esc(col.s)}</p>`:''}<p class="support-note">通过 OpenRouter。${requests.length>1?'次数指处理记录，不是模型数量或并行 agent 数。':'一次处理对应一组消息；响应可能来自缓存。'}</p><dl class="accounting"><dt>该次运行的新 API 请求</dt><dd>${network.http}</dd><dt>复用已有模型响应</dt><dd>${network.cache}</dd>${network.failed?`<dt>其中失败请求</dt><dd>${network.failed}</dd>`:''}</dl>`:isSearch?'<strong>搜索与抓取</strong><p>Serper 搜索 + 本地网页处理</p>':isInput?'<strong>读取数据集记录</strong><p>这一阶段不调用生成模型。</p>':'<strong>本地处理 / 已有输出</strong><p>这一展示步骤不增加模型调用。</p>'}<p class="support-note">${esc(intro)}</p></div>${col.explain?.dev?`<details class="method-panel"><summary>与原系统的适配差异</summary><p>${esc(col.explain.dev)}</p></details>`:''}${!isInput?`<details class="method-panel"><summary>本系统实际使用哪些输入字段</summary>${inputHtml(sd,true)}</details>`:''}<p class="audit-note">读取冻结结果与缓存。调用统计来自产生该结果的运行账本；保留记录沿来源追溯，不代表历史累计费用。</p></aside></div>${promptPanel(sd,spec,state.requestIndex)}<div class="guide-bottom"><span>查看关系全图可切换“流程总览”。</span><button id="continue-step" ${step===all.length-1?'disabled':''}>${step===all.length-1?'已到最终结果':'下一步：'+esc(all[step+1].guide[0])} →</button></div>`;
    host.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>{state.requestIndex=0;go(+b.dataset.step)});
    host.querySelectorAll('[data-item]').forEach(b=>b.onclick=()=>{state.focusIndex=+b.dataset.item;state.requestIndex=0;if(state.sys==='infact'&&['a','g'].includes(col.id)){const prefix=(col.id==='a'?'answer.':'propose_queries.')+sd.trace.questions[state.focusIndex].i;const ri=requests.findIndex(r=>r.stage===prefix||r.stage.startsWith(prefix+'.'));state.requestIndex=Math.max(0,ri);}render({model,doc,state,go})});
    host.querySelector('#previous-step').onclick=()=>go(step-1);
    host.querySelector('#next-step').onclick=()=>go(step+1);
    host.querySelector('#continue-step').onclick=()=>go(step+1);
    const nav=host.querySelector('.guide-nav'),active=nav.querySelector('[aria-current]');if(active)nav.scrollLeft=Math.max(0,active.offsetLeft-nav.offsetLeft-(nav.clientWidth-active.clientWidth)/2);
    const chooser=host.querySelector('#request-choice');
    if(chooser) chooser.onchange=()=>{state.requestIndex=+chooser.value;host.querySelector('#request-content').innerHTML=requestContent(requests[state.requestIndex])};
  }
  return {enrich,render};
})();
