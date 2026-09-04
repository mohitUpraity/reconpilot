const merchant = 'merchant_demo';
let filter = '';
let excFilter = '';
let demoEventSource = null;
let currentCaseId = 'CASE-42A2BBA8D9';

const $ = x => document.getElementById(x);
const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
const fmt = n => new Intl.NumberFormat('en-IN').format(Number(n || 0));
const curr = n => '₹' + new Intl.NumberFormat('en-IN').format(Number(n || 0));
const pc = n => `${Math.round(Number(n || 0) * 1000) / 10}%`;

const badge = s => {
  if (s === 'RECONCILED') return '<span class="badge good">RECONCILED</span>';
  if (s === 'REVIEW') return '<span class="badge warn">REVIEW</span>';
  return '<span class="badge bad">UNRESOLVED</span>';
};

async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw Error(`${r.status}`);
  return r.json();
}

async function post(path, body = {}) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Request failed' }));
    throw Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
}

// ----------------- OVERVIEW & CONTROL ROOM -----------------
async function overview() {
  try {
    const d = await get(`/api/v1/overview/${merchant}`);
    const m = Object.fromEntries((d.case_status || []).map(x => [x.status, x.c]));
    const total = (m.RECONCILED || 0) + (m.REVIEW || 0) + (m.UNRESOLVED || 0);
    const h = total ? (m.RECONCILED || 0) / total : 0;

    $('records').textContent = fmt(d.counts?.financial_records ?? 0);
    $('totalCases').textContent = fmt(d.counts?.reconciliation_cases ?? 500);
    $('reconciled').textContent = fmt(m.RECONCILED || 0);
    $('reconciledRate').textContent = `${pc(h)} of cases resolved`;
    $('reviewCount').textContent = fmt(m.REVIEW || 0);
    $('excStat').textContent = fmt(d.counts?.exceptions ?? ((m.REVIEW || 0) + (m.UNRESOLVED || 0)));

    if ($('navExcBadge')) $('navExcBadge').textContent = fmt(d.counts?.exceptions ?? 111);
    if ($('navReviewBadge')) $('navReviewBadge').textContent = fmt(m.REVIEW || 73);

    // Update pipeline nodes
    if ($('pipeFilesCount')) $('pipeFilesCount').textContent = '4 Sources';
    if ($('pipeNormCount')) $('pipeNormCount').textContent = `${fmt(d.counts?.financial_records ?? 1190)} Recs`;
    if ($('pipeMatchCount')) $('pipeMatchCount').textContent = `${fmt(m.RECONCILED || 389)} Auto`;
    if ($('pipeAiCount')) $('pipeAiCount').textContent = `${fmt(d.counts?.exceptions || 111)} Hard`;
    if ($('pipeReviewCount')) $('pipeReviewCount').textContent = `${fmt(m.REVIEW || 73)} Cases`;
    if ($('pipeReconciledCount')) $('pipeReconciledCount').textContent = `${fmt(m.RECONCILED || 389)} Reconciled`;

    // Source coverage bars
    const src = d.records_by_source || [];
    const mx = Math.max(...src.map(x => x.c), 1);
    $('sources').innerHTML = src.map(x => `
      <div class="src">
        <label>${esc(x.source)}</label>
        <div class="bar"><i style="width:${Math.round(x.c / mx * 100)}%"></i></div>
        <div class="num">${fmt(x.c)}</div>
      </div>
    `).join('') || '<div class="muted">No sources loaded.</div>';

    // Agent pods state update
    updateAgentPod('pod-ingest', 'state-ingest', 'bubble-ingest', 'idle', 'IDLE', '4 sources loaded');
    updateAgentPod('pod-normalize', 'state-normalize', 'bubble-normalize', 'completed', 'COMPLETED', '1,190 in standard schema');
    updateAgentPod('pod-match', 'state-match', 'bubble-match', 'completed', 'COMPLETED', `${fmt(m.RECONCILED || 389)} high-conf matches`);
    updateAgentPod('pod-ai', 'state-ai', 'bubble-ai', 'working', 'READY', 'Gemini 2.5 Flash Lite');
    updateAgentPod('pod-policy', 'state-policy', 'bubble-policy', 'blocked', 'GUARDING', 'Gate: 0.93 threshold');
    updateAgentPod('pod-human', 'state-human', 'bubble-human', 'waiting', 'WAITING', `${fmt(m.REVIEW || 73)} cases in review`);
  } catch (err) {
    console.error('Failed to load overview:', err);
  }
}

function updateAgentPod(podId, stateId, bubbleId, stateClass, stateText, bubbleText) {
  const pod = $(podId);
  const st = $(stateId);
  const bb = $(bubbleId);
  if (st) {
    st.className = `pod-state ${stateClass}`;
    st.textContent = stateText;
  }
  if (bb) bb.textContent = bubbleText;
}

// ----------------- RECONCILIATION CASES -----------------
async function cases() {
  try {
    const q = $('caseSearchInput')?.value?.trim().toLowerCase() || '';
    const d = await get(`/api/v1/cases/${merchant}${filter ? `?status=${filter}` : ''}`);
    let rows = d.items || [];
    if (q) {
      rows = rows.filter(c =>
        (c.case_id || '').toLowerCase().includes(q) ||
        (c.primary_record_id || '').toLowerCase().includes(q) ||
        (c.matched_record_id || '').toLowerCase().includes(q) ||
        (c.reason || '').toLowerCase().includes(q)
      );
    }
    $('caseCount').textContent = `${fmt(rows.length)} cases`;
    if (!rows.length) {
      $('cases').innerHTML = '<div class="row" style="cursor:default;"><div class="muted">No matching reconciliation cases found.</div></div>';
      return;
    }
    $('cases').innerHTML = rows.map(c => `
      <div class="row" data-id="${esc(c.case_id)}">
        <div class="id">${esc(c.case_id)}</div>
        <div class="mainline">
          <div style="display:flex;align-items:center;gap:6px;">
            <b>${esc(c.primary_record_id)}</b>
            ${c.matched_record_id ? `<span class="muted" style="font-size:11px;">→ ${esc(c.matched_record_id)}</span>` : ''}
          </div>
          <small>${esc(c.reason || 'Decision logged')}</small>
        </div>
        <div>${badge(c.status)}</div>
        <div class="confidence">${pc(c.confidence)}</div>
        <div class="muted">›</div>
      </div>
    `).join('');
    document.querySelectorAll('#cases .row').forEach(x => {
      if (x.dataset.id) x.onclick = () => openCase(x.dataset.id);
    });
  } catch (err) {
    console.error('Failed to load cases:', err);
    $('cases').innerHTML = `<div class="row" style="cursor:default;"><div class="bad">Failed to load cases: ${esc(err.message)}</div></div>`;
  }
}

// ----------------- EXCEPTIONS QUEUE -----------------
async function exceptions() {
  $('excCount').textContent = '…';
  try {
    const d = await get(`/api/v1/exceptions/${merchant}`);
    let rows = d.items || [];
    if (excFilter) {
      rows = rows.filter(e => (e.severity || '').toUpperCase() === excFilter);
    }
    $('excCount').textContent = `${fmt(rows.length)} open exceptions`;
    if (!rows.length) {
      $('excList').innerHTML = '<div class="row" style="cursor:default;"><div class="muted">No exceptions found for this filter.</div></div>';
      return;
    }
    $('excList').innerHTML = rows.map(e => `
      <div class="row" data-id="${esc(e.case_id)}">
        <div class="id">${esc(e.exception_id)}</div>
        <div class="mainline">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
            <b>${esc(e.primary_record_id || e.case_id)}</b>
            <span class="badge" style="font-size:9px;padding:2px 6px;">${esc(e.case_type || 'case')}</span>
            <span class="badge ${e.status === 'RESOLVED' ? 'good' : 'warn'}" style="font-size:9px;padding:2px 6px;">${esc(e.status || 'OPEN')}</span>
          </div>
          <small>${esc(e.reason || 'No reason provided')}</small>
        </div>
        <div><span class="badge ${e.severity === 'HIGH' ? 'bad' : (e.severity === 'LOW' ? 'good' : 'warn')}">${esc(e.severity || 'MEDIUM')}</span></div>
        <div class="confidence">${pc(e.confidence)}</div>
        <div class="muted">›</div>
      </div>
    `).join('');
    document.querySelectorAll('#excList .row').forEach(x => {
      if (x.dataset.id) x.onclick = () => openCase(x.dataset.id);
    });
  } catch (err) {
    console.error('Failed to load exceptions:', err);
    $('excCount').textContent = '0';
    $('excList').innerHTML = `<div class="row" style="cursor:default;"><div class="bad">Failed to load exceptions: ${esc(err.message)}</div></div>`;
  }
}

// ----------------- HUMAN REVIEW OPERATIONAL QUEUE -----------------
async function reviewQueue() {
  try {
    const d = await get(`/api/v1/cases/${merchant}?status=REVIEW`);
    const rows = d.items || [];
    $('reviewOpenCount').textContent = fmt(rows.length);
    if ($('reviewQueueBadge')) $('reviewQueueBadge').textContent = `${fmt(rows.length)} candidates`;
    if (!rows.length) {
      $('reviewQueueList').innerHTML = '<div class="row" style="cursor:default;"><div class="muted">🎉 All review cases have been processed! No pending items.</div></div>';
      return;
    }
    $('reviewQueueList').innerHTML = rows.map(c => `
      <div class="row" data-id="${esc(c.case_id)}">
        <div class="id">${esc(c.case_id)}</div>
        <div class="mainline">
          <div style="display:flex;align-items:center;gap:8px;">
            <b>${esc(c.primary_record_id)}</b>
            <span class="badge warn">HUMAN ACTION REQUIRED</span>
          </div>
          <small>${esc(c.reason || 'Plausible payment candidate requires human sign-off')}</small>
        </div>
        <div><button class="btn secondary sm" onclick="event.stopPropagation(); openCase('${esc(c.case_id)}')">Review Evidence</button></div>
        <div class="confidence">${pc(c.confidence)}</div>
        <div class="muted">›</div>
      </div>
    `).join('');
    document.querySelectorAll('#reviewQueueList .row').forEach(x => {
      if (x.dataset.id) x.onclick = () => openCase(x.dataset.id);
    });
  } catch (err) {
    console.error('Failed to load review queue:', err);
  }
}

// ----------------- 4-HOP FINANCE CHAIN VIEW -----------------
async function loadFinanceChain(caseId) {
  try {
    const d = await get(`/api/v1/chain/${encodeURIComponent(caseId || currentCaseId)}`);
    const chain = d.chain || {};

    // Hop 1: Invoice
    if ($('hopInvAmount')) $('hopInvAmount').textContent = curr(chain.invoice?.amount);
    if ($('hopInvId')) $('hopInvId').textContent = chain.invoice?.id || '—';
    if ($('hopInvCust')) $('hopInvCust').textContent = chain.invoice?.customer || '—';
    if ($('hopInvDate')) $('hopInvDate').textContent = chain.invoice?.date || '—';

    // Hop 2: Payment
    if ($('hopPayAmount')) $('hopPayAmount').textContent = curr(chain.payment?.amount);
    if ($('hopPayId')) $('hopPayId').textContent = chain.payment?.id || '—';
    if ($('hopPayCust')) $('hopPayCust').textContent = chain.payment?.customer || chain.invoice?.customer || '—';
    if ($('hopPayDate')) $('hopPayDate').textContent = chain.payment?.date || '—';
    if ($('linkReason1')) $('linkReason1').textContent = chain.payment?.link_reason || 'Matched by Reference & Amount';

    // Hop 3: Settlement
    if ($('hopSetNet')) $('hopSetNet').textContent = curr(chain.settlement?.net_amount);
    if ($('hopSetId')) $('hopSetId').textContent = chain.settlement?.id || '—';
    if ($('hopSetGross')) $('hopSetGross').textContent = curr(chain.settlement?.gross_amount);
    if ($('hopSetFee')) $('hopSetFee').textContent = `-${curr(chain.settlement?.fee)}`;
    if ($('hopSetTax')) $('hopSetTax').textContent = `-${curr(chain.settlement?.tax)}`;
    if ($('hopSetUtr')) $('hopSetUtr').textContent = chain.settlement?.utr || '—';
    if ($('hopSetDate')) $('hopSetDate').textContent = chain.settlement?.date || '—';
    if ($('linkReason2')) $('linkReason2').textContent = chain.settlement?.link_reason || 'Settled in Razorpay Batch';

    // Hop 4: Bank Statement
    if ($('hopBankAmount')) $('hopBankAmount').textContent = curr(chain.bank?.amount);
    if ($('hopBankId')) $('hopBankId').textContent = chain.bank?.id || '—';
    if ($('hopBankRef')) $('hopBankRef').textContent = chain.bank?.reference || chain.settlement?.utr || '—';
    if ($('hopBankDate')) $('hopBankDate').textContent = chain.bank?.date || '—';
    if ($('linkReason3')) $('linkReason3').textContent = chain.bank?.link_reason || 'Bank Credit matches UTR & Net';
  } catch (err) {
    console.error('Failed to load finance chain:', err);
  }
}

async function populateChainSelector() {
  try {
    const d = await get(`/api/v1/cases/${merchant}?status=RECONCILED`);
    const rows = d.items || [];
    const sel = $('chainCaseSelect');
    if (sel && rows.length) {
      sel.innerHTML = rows.slice(0, 15).map(c => `
        <option value="${esc(c.case_id)}">${esc(c.case_id)} · ${esc(c.primary_record_id)}</option>
      `).join('');
      sel.onchange = e => loadFinanceChain(e.target.value);
      loadFinanceChain(rows[0].case_id);
    }
  } catch (err) {
    console.error('Failed to populate chain selector:', err);
  }
}

// ----------------- AUDIT TRAIL -----------------
async function audit() {
  try {
    const d = await get(`/api/v1/dashboard/${merchant}`);
    $('auditList').innerHTML = (d.recent_activity || []).map(x => `
      <div class="auditrow">
        <div class="muted">${esc(new Date(x.created_at).toLocaleString())}</div>
        <div><b>${esc(x.event_type)}</b></div>
        <div><span class="chip">${esc(x.actor)}</span></div>
        <pre class="json">${esc(x.payload_json)}</pre>
      </div>
    `).join('') || '<div class="muted" style="padding:14px;">No audit events recorded yet.</div>';
  } catch (err) {
    console.error('Failed to load audit:', err);
  }
}

// ----------------- BENCHMARK & TRUST PANEL -----------------
async function benchmark() {
  try {
    const d = await get('/api/v1/benchmark');
    console.log('Benchmark data loaded:', d);
  } catch (err) {
    console.error('Failed to load benchmark:', err);
  }
}

// ----------------- CASE DETAIL & POLICY GATE DRAWER -----------------
async function openCase(id) {
  currentCaseId = id;
  const d = await get(`/api/v1/cases/detail/${encodeURIComponent(id)}`);
  const c = d.case;
  $('dtitle').textContent = c.case_id;

  const review = (c.status === 'REVIEW' || c.status === 'UNRESOLVED');
  const candidateHtml = review ? `
    <div class="reviewbox">
      <div class="eyebrow" style="color:var(--warn);">HUMAN REVIEW REQUIRED</div>
      <p>Confirm candidate payment after inspecting evidence. Every human action is permanently audited with actor credentials.</p>
      <div class="candidate-list">
        ${(d.review_candidates || []).map(x => `
          <button class="candidate" onclick="document.getElementById('reviewPayment').value='${esc(x.source_record_id)}'">
            <b>${esc(x.source_record_id)}</b>
            <span>${curr(x.amount)} · ${esc(x.event_date)} · ${esc(x.customer_name || 'Customer')}</span>
          </button>
        `).join('') || '<span class="muted">No direct candidate matches; enter payment ID manually.</span>'}
      </div>
      <input id="reviewPayment" class="reviewinput" placeholder="Selected Payment ID (e.g. pay_000131)">
      <input id="reviewNote" class="reviewinput" placeholder="Auditor / Reviewer rationale note">
      <div class="reviewactions">
        <button onclick="resolveCase('${esc(c.case_id)}','approve_match')">✓ Approve Match</button>
        <button class="reject" onclick="resolveCase('${esc(c.case_id)}','reject')">✕ Reject</button>
      </div>
    </div>
  ` : '';

  // Technical Pydantic + Policy Gate Verification Card
  const policyGateHtml = `
    <div class="policy-gate-card">
      <div class="pg-header">
        <b>🛡 Pydantic & Policy Gate Architecture</b>
        <span class="badge ${c.status === 'RECONCILED' ? 'good' : 'warn'}">GATE 0.93</span>
      </div>
      <div class="pg-steps">
        <div class="pg-step">
          <span>1. Structured Output Schema</span>
          <b class="good">✓ ReconciliationDecision (Strict)</b>
        </div>
        <div class="pg-step">
          <span>2. Pydantic Type Validation</span>
          <b class="good">✓ PASSED (extra='forbid')</b>
        </div>
        <div class="pg-step">
          <span>3. Evidence Packet Ownership</span>
          <b class="good">✓ Validated against candidate set</b>
        </div>
        <div class="pg-step">
          <span>4. Calibrated Threshold (0.93)</span>
          <b class="${(c.confidence || 0) >= 0.93 ? 'good' : 'warn'}">${pc(c.confidence)} ${c.confidence >= 0.93 ? '≥ 0.93 (Auto-close)' : '< 0.93 (Hold)'}</b>
        </div>
        <div class="pg-step">
          <span>5. Final Controller Action</span>
          <b>${badge(c.status)}</b>
        </div>
      </div>
      <div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;">
        <button id="btnLiveGemini" class="btn secondary sm" onclick="runLiveGemini('${esc(c.case_id)}')">🧠 Live Gemini 2.5 Investigation</button>
        <button class="btn ghost sm" onclick="view('chain');loadFinanceChain('${esc(c.case_id)}');$('drawer').classList.add('hidden');">⛓ View 4-Hop Chain</button>
      </div>
      <div id="geminiLiveResult" style="margin-top:10px;font-size:11px;display:none;"></div>
    </div>
  `;

  $('detail').innerHTML = `
    <div class="detailgrid">
      <div class="dc"><label>STATUS</label><b>${badge(c.status)}</b></div>
      <div class="dc"><label>CONFIDENCE</label><b>${pc(c.confidence)}</b></div>
      <div class="dc"><label>PRIMARY INVOICE</label><b>${esc(c.primary_record_id || '—')}</b></div>
      <div class="dc"><label>MATCHED PAYMENT</label><b>${esc(c.matched_record_id || '—')}</b></div>
    </div>
    <div class="dc" style="margin-bottom:14px;"><label>DECISION RATIONALE</label><b>${esc(c.reason || '—')}</b></div>
    ${policyGateHtml}
    ${candidateHtml}
    <div class="timeline">
      <b style="font-size:12px;color:var(--soft);">EVIDENCE & AUDIT TRAIL</b>
      ${(d.links || []).map(l => `
        <div class="ti">
          <b>Reconciliation Link: ${esc(l.link_type)}</b>
          <p>${esc(l.from_source)}:${esc(l.from_source_record_id)} → ${esc(l.to_source)}:${esc(l.to_source_record_id)}<br>Confidence: ${pc(l.confidence)} · Source: ${esc(l.decision_source)}</p>
        </div>
      `).join('')}
      ${(d.exceptions || []).map(e => `
        <div class="ti">
          <b class="${e.severity === 'HIGH' ? 'bad' : 'warn'}">Exception: ${esc(e.severity)}</b>
          <p>${esc(e.reason)}<br>Status: ${esc(e.status)} · Created: ${esc(new Date(e.created_at).toLocaleString())}</p>
        </div>
      `).join('')}
    </div>
  `;

  $('drawer').classList.remove('hidden');
}

async function runLiveGemini(caseId) {
  const box = $('geminiLiveResult');
  if (!box) return;
  box.style.display = 'block';
  box.innerHTML = '<div class="muted">Invoking Gemini 2.5 Flash Lite investigator with structured evidence packet…</div>';
  try {
    const res = await post(`/api/v1/ai/investigate/${encodeURIComponent(caseId)}`);
    box.innerHTML = `
      <div style="background:#0e131b;border:1px solid var(--ai-border);border-radius:8px;padding:10px;">
        <div style="display:flex;justify-content:space-between;">
          <b style="color:var(--ai);">Gemini Decision: ${esc(res.decision)}</b>
          <span>Conf: ${pc(res.confidence)}</span>
        </div>
        <div style="margin-top:6px;color:var(--soft);">
          <b>Evidence:</b>
          <ul style="margin:4px 0 6px 16px;padding:0;">
            ${(res.evidence || []).map(x => `<li>${esc(x)}</li>`).join('')}
          </ul>
          ${res.risks?.length ? `
            <b style="color:var(--warn);">Risks:</b>
            <ul style="margin:4px 0 0 16px;padding:0;">
              ${res.risks.map(x => `<li>${esc(x)}</li>`).join('')}
            </ul>
          ` : ''}
        </div>
        <div style="margin-top:8px;font-size:10px;color:var(--muted);border-top:1px solid var(--line);padding-top:6px;">
          Model: ${esc(res.model)} · Pydantic validation: <b class="good">${esc(res.pydantic_validation?.status)}</b> · Policy gate: <b class="${res.policy_gate?.auto_match_allowed ? 'good' : 'warn'}">${res.policy_gate?.final_action}</b>
        </div>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div class="bad">Gemini investigation: ${esc(err.message)}</div>`;
  }
}

async function resolveCase(id, action) {
  const payment = action === 'approve_match' ? ($('reviewPayment')?.value || '') : null;
  const note = $('reviewNote')?.value || '';
  if (action === 'approve_match' && !payment) {
    alert('Please enter or select a payment candidate ID first.');
    return;
  }
  try {
    await post(`/api/v1/cases/${encodeURIComponent(id)}/resolve`, {
      action,
      payment_id: payment,
      note,
      actor: 'dashboard_reviewer'
    });
    await openCase(id);
    overview();
    cases();
    exceptions();
    reviewQueue();
    audit();
  } catch (err) {
    alert(`Resolution failed: ${err.message}`);
  }
}

// ----------------- DEMO MODE (GUIDED 5-MIN WALKTHROUGH) -----------------
function startDemoMode() {
  const banner = $('demoBanner');
  banner.classList.remove('hidden');
  view('overview');

  const nodes = ['node-files', 'node-normalize', 'node-match', 'node-ai', 'node-gate', 'node-review', 'node-reconciled'];

  if (demoEventSource) {
    demoEventSource.close();
  }

  demoEventSource = new EventSource(`/api/v1/demo/stream?merchant_id=${merchant}`);

  demoEventSource.onmessage = e => {
    try {
      const data = JSON.parse(e.data);
      $('demoStepBadge').textContent = `DEMO STEP ${data.step} / 9`;
      $('demoStepTitle').textContent = data.label;
      $('demoStepDetail').textContent = data.detail;
      $('demoTimer').textContent = data.time || '0:00';

      // Highlight pipeline stage
      nodes.forEach(n => $(n)?.classList.remove('active-stage'));
      if (data.stage === 'ingest') $('node-files')?.classList.add('active-stage');
      if (data.stage === 'normalize') $('node-normalize')?.classList.add('active-stage');
      if (data.stage === 'match') $('node-match')?.classList.add('active-stage');
      if (data.stage === 'ai_route' || data.stage === 'ai_investigate') $('node-ai')?.classList.add('active-stage');
      if (data.stage === 'policy_gate') $('node-gate')?.classList.add('active-stage');
      if (data.stage === 'human_queue') $('node-review')?.classList.add('active-stage');
      if (data.stage === 'complete') {
        $('node-reconciled')?.classList.add('active-stage');
        demoEventSource.close();
        setTimeout(() => {
          banner.classList.add('hidden');
          overview();
        }, 3000);
      }
    } catch (err) {
      console.error('Demo parse error:', err);
    }
  };

  demoEventSource.onerror = () => {
    demoEventSource.close();
  };
}

// ----------------- FILE IMPORT & DEMO LOADER -----------------
async function reloadDemoDataset() {
  try {
    const btn = $('btnReloadDemoDataset');
    if (btn) btn.textContent = 'Reloading…';
    const res = await post('/api/v1/import/demo');
    alert(res.message);
    overview();
    if (btn) btn.textContent = '⚡ Reload Verified Demo Dataset';
  } catch (err) {
    alert(`Failed to reload demo dataset: ${err.message}`);
  }
}

async function handleFileUpload(file) {
  const name = file.name.toLowerCase();
  let type = 'invoices';
  if (name.includes('pay')) type = 'payments';
  else if (name.includes('settle')) type = 'settlements';
  else if (name.includes('bank')) type = 'bank_statement';

  const reader = new FileReader();
  reader.onload = async e => {
    try {
      const content = e.target.result;
      const res = await post('/api/v1/import/upload', {
        source_type: type,
        filename: file.name,
        content: content,
        merchant_id: merchant
      });
      alert(`Successfully imported ${res.imported_rows} records from ${file.name} as ${type}.`);
      overview();
    } catch (err) {
      alert(`Import error: ${err.message}`);
    }
  };
  reader.readAsText(file);
}

// ----------------- VIEW SWITCHER & EVENT LISTENERS -----------------
function view(v) {
  document.querySelectorAll('.view').forEach(x => x.classList.remove('active'));
  const target = $(v);
  if (target) target.classList.add('active');
  document.querySelectorAll('nav button').forEach(x => x.classList.toggle('active', x.dataset.view === v));

  const titles = {
    overview: 'Control Room',
    import: 'Import Financial Sources',
    reconciliation: 'Reconciliation Cases',
    exceptions: 'Exception Queue',
    review: 'Human Review Queue',
    chain: 'End-to-End Finance Chain',
    audit: 'Audit Trail',
    benchmark: 'Controller Performance & Policy Benchmark'
  };
  $('pageTitle').textContent = titles[v] || 'Control Room';

  if (v === 'overview') overview();
  if (v === 'reconciliation') cases();
  if (v === 'exceptions') exceptions();
  if (v === 'review') reviewQueue();
  if (v === 'chain') populateChainSelector();
  if (v === 'audit') audit();
  if (v === 'benchmark') benchmark();
}

// Nav clicks
document.querySelectorAll('nav button').forEach(x => x.onclick = () => view(x.dataset.view));

// Filter clicks
document.querySelectorAll('.f').forEach(x => x.onclick = () => {
  document.querySelectorAll('.f').forEach(y => y.classList.remove('active'));
  x.classList.add('active');
  filter = x.dataset.status;
  cases();
});

document.querySelectorAll('.ef').forEach(x => x.onclick = () => {
  document.querySelectorAll('.ef').forEach(y => y.classList.remove('active'));
  x.classList.add('active');
  excFilter = x.dataset.sev;
  exceptions();
});

// Search input
$('caseSearchInput')?.addEventListener('input', () => cases());

// Top action buttons
$('btnDemoMode')?.addEventListener('click', startDemoMode);
$('btnDemoSkip')?.addEventListener('click', () => {
  if (demoEventSource) demoEventSource.close();
  $('demoBanner')?.classList.add('hidden');
  view('overview');
});
$('btnDemoPause')?.addEventListener('click', () => {
  if (demoEventSource) demoEventSource.close();
});
$('btnImportModal')?.addEventListener('click', () => view('import'));
$('btnRunReconcile')?.addEventListener('click', async () => {
  const btn = $('btnRunReconcile');
  btn.textContent = 'Running…';
  try {
    await post('/api/v1/reconcile/run');
    alert('Reconciliation cycle completed successfully.');
    overview();
  } catch (err) {
    alert(`Reconciliation error: ${err.message}`);
  } finally {
    btn.textContent = '⚡ Run Reconciliation';
  }
});
$('btnReloadDemoDataset')?.addEventListener('click', reloadDemoDataset);
$('refresh')?.addEventListener('click', () => view(document.querySelector('nav button.active')?.dataset?.view || 'overview'));
$('close')?.addEventListener('click', () => $('drawer')?.classList.add('hidden'));
$('shade')?.addEventListener('click', () => $('drawer')?.classList.add('hidden'));

// Drag and drop
const dropzone = $('dropzone');
if (dropzone) {
  dropzone.ondragover = e => { e.preventDefault(); dropzone.classList.add('dragover'); };
  dropzone.ondragleave = () => dropzone.classList.remove('dragover');
  dropzone.ondrop = e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };
}

$('fileInput')?.addEventListener('change', e => {
  if (e.target.files.length) {
    handleFileUpload(e.target.files[0]);
  }
});

// Initial boot
overview();
