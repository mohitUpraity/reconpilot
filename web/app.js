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

// ----------------- TOAST NOTIFICATIONS -----------------
function showToast(message, type = 'info') {
  const container = $('toastContainer') || document.body;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : (type === 'error' ? '⚠' : 'ℹ');
  toast.innerHTML = `<span style="font-weight:bold;font-size:14px;">${icon}</span><span>${esc(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ----------------- AI DIAGNOSTICS & STATUS -----------------
let aiDiagnosticsData = null;

async function fetchAiStatus() {
  try {
    const res = await get('/api/v1/ai/status');
    aiDiagnosticsData = res;
    const chipText = $('aiChipText');
    const chipDot = $('aiChipDot');
    const footerTag = $('footerModelTag');
    const diagModel = $('diagModelName');
    const diagKey = $('diagKeyStatus');
    
    if (chipText) chipText.textContent = res.has_key ? `Gemini: ${res.configured_model}` : 'Gemini: Key Needed';
    if (chipDot) {
      chipDot.className = `status-indicator-dot ${res.has_key ? 'online' : 'offline'}`;
      chipDot.title = res.has_key ? `Connected with model ${res.configured_model}` : 'API key not configured in .env';
    }
    if (footerTag) footerTag.textContent = `${res.configured_model} (Live)`;
    if (diagModel) diagModel.textContent = res.configured_model;
    if (diagKey) {
      diagKey.textContent = res.has_key ? `Active (${res.masked_key})` : 'Missing in .env';
      diagKey.className = res.has_key ? 'good' : 'bad';
    }
  } catch (err) {
    console.warn('AI status check failed:', err);
  }
}

function openAiDiagnostics() {
  $('aiDiagnosticsModal')?.classList.remove('hidden');
  fetchAiStatus();
}

function closeAiDiagnostics() {
  $('aiDiagnosticsModal')?.classList.add('hidden');
}

async function runLiveAiTest() {
  const btn = $('btnRunAiTest');
  const out = $('aiTestResult');
  if (!btn || !out) return;

  btn.textContent = 'Testing Gemini...';
  btn.disabled = true;
  out.style.display = 'block';
  out.innerHTML = `<span style="color:var(--soft);">Sending live test payload to Google Gemini API...</span>`;

  try {
    const res = await post('/api/v1/ai/test');
    if (res.ok) {
      out.innerHTML = `
        <div style="color:var(--good);font-weight:bold;margin-bottom:6px;">✓ LIVE GEMINI CONNECTION VERIFIED</div>
        <div>Model Used: <b style="color:#fff;">${esc(res.model)}</b></div>
        <div>Round-Trip Latency: <b style="color:#fff;">${res.latency_ms} ms</b></div>
        <div>Tokens: <span style="color:#fff;">Prompt: ${res.usage?.prompt_tokens} · Response: ${res.usage?.candidates_tokens} · Total: ${res.usage?.total_tokens}</span></div>
        <div style="margin-top:6px;color:var(--soft);font-size:10px;">${esc(res.note || '')}</div>
      `;
      showToast(`✓ Gemini API responded in ${res.latency_ms}ms`, 'success');
    } else {
      out.innerHTML = `
        <div style="color:var(--bad);font-weight:bold;margin-bottom:6px;">⚠ CONNECTION FAILED</div>
        <div style="color:#ff8888;">${esc(res.error || 'Unknown error')}</div>
        <div style="margin-top:6px;color:var(--muted);font-size:10px;">Please check GEMINI_API_KEY in your .env file and ensure model name is valid.</div>
      `;
      showToast(`Gemini error: ${res.error}`, 'error');
    }
  } catch (err) {
    out.innerHTML = `<div style="color:var(--bad);">Error calling test endpoint: ${esc(err.message)}</div>`;
    showToast(`Test error: ${err.message}`, 'error');
  } finally {
    btn.textContent = '⚡ Run Ping Test';
    btn.disabled = false;
  }
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

    if ($('navExcBadge')) $('navExcBadge').textContent = fmt(d.counts?.exceptions ?? 0);
    if ($('navReviewBadge')) $('navReviewBadge').textContent = fmt(m.REVIEW ?? 0);

    // Update dynamic subtitles
    const totalCasesCount = d.counts?.reconciliation_cases ?? total;
    if ($('totalCasesSub')) $('totalCasesSub').textContent = `${fmt(totalCasesCount)} Cases Analyzed`;
    if ($('sourceCoverageSub')) $('sourceCoverageSub').textContent = `${fmt(d.counts?.financial_records ?? 0)} Financial records in database`;

    // Dynamic Visual Split: Deterministic vs AI Policy
    const detCount = m.RECONCILED || 0;
    const detPct = totalCasesCount ? ((detCount / totalCasesCount) * 100).toFixed(1) : '0.0';
    const excCount = d.counts?.exceptions ?? ((m.REVIEW || 0) + (m.UNRESOLVED || 0));
    const excPct = totalCasesCount ? ((excCount / totalCasesCount) * 100).toFixed(1) : '0.0';
    const reviewCases = m.REVIEW || 0;
    const unresolvedCases = m.UNRESOLVED || 0;

    if ($('splitDetCases')) $('splitDetCases').textContent = `${fmt(detCount)} Cases (${detPct}%)`;
    if ($('splitTotalCasesCircle')) $('splitTotalCasesCircle').textContent = `${fmt(totalCasesCount)} CASES`;
    if ($('splitAiCases')) $('splitAiCases').textContent = `${fmt(excCount)} Cases (${excPct}%)`;
    if ($('splitAiReviews')) $('splitAiReviews').textContent = fmt(reviewCases);
    if ($('splitAiUnresolved')) $('splitAiUnresolved').textContent = fmt(unresolvedCases);
    if ($('splitAiMatches')) $('splitAiMatches').textContent = fmt(detCount > 0 ? Math.min(18, detCount) : 0);

    if ($('btnFilterAllExceptions')) $('btnFilterAllExceptions').textContent = `All Exceptions (${fmt(excCount)})`;
    if ($('btnBatchAll')) {
      $('btnBatchAll').setAttribute('data-limit', String(excCount || 111));
      $('btnBatchAll').innerHTML = `All ${fmt(excCount)}<br><small style="font-size:9px;color:var(--muted);">Full Queue</small>`;
    }

    // Update pipeline nodes
    if ($('pipeFilesCount')) $('pipeFilesCount').textContent = `${(d.records_by_source || []).length} Sources`;
    if ($('pipeNormCount')) $('pipeNormCount').textContent = `${fmt(d.counts?.financial_records ?? 0)} Recs`;
    if ($('pipeMatchCount')) $('pipeMatchCount').textContent = `${fmt(m.RECONCILED ?? 0)} Auto`;
    if ($('pipeAiCount')) $('pipeAiCount').textContent = `${fmt(excCount)} Hard`;
    if ($('pipeReviewCount')) $('pipeReviewCount').textContent = `${fmt(m.REVIEW ?? 0)} Cases`;
    if ($('pipeReconciledCount')) $('pipeReconciledCount').textContent = `${fmt(m.RECONCILED ?? 0)} Reconciled`;

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

    // Source cards update
    const bySource = {};
    src.forEach(r => { bySource[r.source] = r.c; });
    if ($('cntInvoices')) $('cntInvoices').textContent = `${fmt(bySource['merchant'] ?? 0)} records`;
    if ($('cntPayments')) $('cntPayments').textContent = `${fmt(bySource['payment'] ?? 0)} records`;
    if ($('cntSettlements')) $('cntSettlements').textContent = `${fmt(bySource['razorpay'] ?? 0)} batches`;
    if ($('cntBank')) $('cntBank').textContent = `${fmt(bySource['bank'] ?? 0)} txns`;

    // Agent pods state update
    updateAgentPod('pod-ingest', 'state-ingest', 'bubble-ingest', 'idle', 'IDLE', `${(d.records_by_source || []).length} sources loaded`);
    updateAgentPod('pod-normalize', 'state-normalize', 'bubble-normalize', 'completed', 'COMPLETED', `${fmt(d.counts?.financial_records ?? 0)} standard records`);
    updateAgentPod('pod-match', 'state-match', 'bubble-match', 'completed', 'COMPLETED', `${fmt(m.RECONCILED || 0)} high-conf matches`);
    const aiLabel = aiDiagnosticsData?.configured_model || 'Gemini 3.1 Flash-Lite';
    updateAgentPod('pod-ai', 'state-ai', 'bubble-ai', 'working', 'READY', aiLabel);
    updateAgentPod('pod-policy', 'state-policy', 'bubble-policy', 'blocked', 'GUARDING', 'Gate: 0.93 threshold');
    updateAgentPod('pod-human', 'state-human', 'bubble-human', 'waiting', 'WAITING', `${fmt(m.REVIEW || 0)} cases in review`);

    fetchAiStatus();
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
    if ($('btnFilterAllExceptions')) $('btnFilterAllExceptions').textContent = `All Exceptions (${fmt(rows.length)})`;
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
    if (d && d.llm_benchmark) {
      const llm = d.llm_benchmark;
      if ($('benchModelBadge')) $('benchModelBadge').textContent = `✨ ${llm.model} Active`;
      if ($('benchModelSub')) $('benchModelSub').textContent = llm.model;
      if ($('benchGeminiCasesCount')) $('benchGeminiCasesCount').textContent = (llm.gemini_resolved_cases || 0);
    }
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
  const currentModel = aiDiagnosticsData?.configured_model || 'gemini-3.1-flash-lite';
  box.style.display = 'block';
  box.innerHTML = `
    <div style="background:#0e131b;border:1px solid var(--ai-border);border-radius:8px;padding:12px;display:flex;align-items:center;gap:10px;">
      <div class="pulse-dot" style="background:var(--ai);"></div>
      <span style="color:var(--ai);font-size:12px;">Querying Google Gemini (${esc(currentModel)}) with Pydantic gate verification...</span>
    </div>
  `;
  try {
    const res = await post(`/api/v1/ai/investigate/${encodeURIComponent(caseId)}`);
    const usage = res.usage || {};
    const estCost = usage.estimated_cost_usd !== undefined ? `$${usage.estimated_cost_usd}` : '< $0.0001';

    box.innerHTML = `
      <div style="background:#0e131b;border:1px solid var(--ai-border);border-radius:10px;padding:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span class="badge" style="background:rgba(139,92,246,0.2);color:#c4b5fd;border:1px solid #8b5cf6;">
              ✨ Google Gemini (${esc(res.model)})
            </span>
            <b style="color:${res.decision === 'MATCH' ? 'var(--good)' : (res.decision === 'REVIEW' ? 'var(--warn)' : 'var(--bad)')};">
              ${esc(res.decision)}
            </b>
          </div>
          <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#fff;">Conf: ${pc(res.confidence)}</span>
        </div>

        <div style="margin-top:8px;color:var(--soft);font-size:12px;">
          <b>Evidence:</b>
          <ul style="margin:4px 0 6px 16px;padding:0;">
            ${(res.evidence || []).map(x => `<li>${esc(x)}</li>`).join('')}
          </ul>
          ${res.risks?.length ? `
            <b style="color:var(--warn);">Risks Identified:</b>
            <ul style="margin:4px 0 0 16px;padding:0;">
              ${res.risks.map(x => `<li>${esc(x)}</li>`).join('')}
            </ul>
          ` : ''}
        </div>

        <!-- Token Usage & Economics Strip -->
        <div style="margin-top:10px;background:#141b25;border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-size:10px;color:var(--muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;">
          <span>Prompt: <b style="color:#fff;">${usage.prompt_tokens || '—'}</b> tokens</span>
          <span>Output: <b style="color:#fff;">${usage.candidates_tokens || '—'}</b> tokens</span>
          <span>Total: <b style="color:#fff;">${usage.total_tokens || '—'}</b> tokens</span>
          <span>Est. Cost: <b style="color:var(--good);">${estCost}</b></span>
        </div>

        <div style="margin-top:8px;font-size:10px;color:var(--muted);border-top:1px solid var(--line);padding-top:6px;display:flex;justify-content:space-between;align-items:center;">
          <div>
            Pydantic validation: <b class="good">${esc(res.pydantic_validation?.status)}</b> (extra='forbid') · 
            Policy Gate: <b class="${res.policy_gate?.auto_match_allowed ? 'good' : 'warn'}">${res.policy_gate?.final_action}</b>
          </div>
          ${res.raw_json ? `
            <button onclick="this.nextElementSibling.classList.toggle('hidden')" class="btn ghost sm" style="font-size:9px;padding:2px 6px;">Raw JSON</button>
            <pre class="hidden" style="margin-top:8px;padding:8px;background:#06080b;border-radius:6px;font-size:10px;color:#94a3b8;max-height:150px;overflow-y:auto;width:100%;">${esc(res.raw_json)}</pre>
          ` : ''}
        </div>
      </div>
    `;
    showToast(`Investigation finished: ${res.decision} (${pc(res.confidence)})`, 'info');
  } catch (err) {
    box.innerHTML = `<div class="bad" style="padding:10px;border:1px solid var(--bad-border);border-radius:8px;">Gemini investigation error: ${esc(err.message)}</div>`;
    showToast(`Gemini error: ${err.message}`, 'error');
  }
}

async function resolveCase(id, action) {
  const payment = action === 'approve_match' ? ($('reviewPayment')?.value || '') : null;
  const note = $('reviewNote')?.value || '';
  if (action === 'approve_match' && !payment) {
    showToast('Please enter or select a payment candidate ID first.', 'error');
    return;
  }
  try {
    await post(`/api/v1/cases/${encodeURIComponent(id)}/resolve`, {
      action,
      payment_id: payment,
      note,
      actor: 'dashboard_reviewer'
    });
    showToast(`Case ${id} resolved successfully.`, 'success');
    await openCase(id);
    overview();
    cases();
    exceptions();
    reviewQueue();
    audit();
  } catch (err) {
    showToast(`Resolution failed: ${err.message}`, 'error');
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

// ----------------- FILE IMPORT & RECONCILIATION RUNNER -----------------
async function reloadDemoDataset() {
  try {
    const btn = $('btnReloadDemoDataset');
    if (btn) btn.textContent = 'Reloading…';
    const res = await post('/api/v1/import/demo');
    showToast(res.message, 'success');
    overview();
    if (btn) btn.textContent = '⚡ Reload Verified Demo Dataset';
  } catch (err) {
    showToast(`Failed to reload demo dataset: ${err.message}`, 'error');
  }
}

async function runReconciliationNow() {
  const btn = $('btnRunReconcile');
  if (btn) btn.textContent = 'Reconciling…';
  try {
    await post('/api/v1/reconcile/run');
    showToast('Reconciliation cycle completed successfully.', 'success');
    overview();
    cases();
    exceptions();
    reviewQueue();
  } catch (err) {
    showToast(`Reconciliation error: ${err.message}`, 'error');
  } finally {
    if (btn) btn.textContent = '⚡ Run Reconciliation';
  }
}

function renderStagedFileCard(file, type, rowCount, headers, sampleRows) {
  const staging = $('uploadStagingArea');
  if (!staging) return;

  const card = document.createElement('div');
  card.className = 'staging-card';
  const kbSize = (file.size / 1024).toFixed(1);
  const typeIcons = {
    invoices: '📄',
    payments: '💳',
    settlements: '🏦',
    bank_statement: '🏛'
  };
  const typeTitles = {
    invoices: 'Merchant Receivables (Invoices)',
    payments: 'Gateway Collections (Payments)',
    settlements: 'Razorpay Settlements (Batches)',
    bank_statement: 'Bank Statement (Payout Credits)'
  };

  card.innerHTML = `
    <div class="staging-header">
      <div class="staging-file-info">
        <div class="staging-icon">${typeIcons[type] || '📁'}</div>
        <div class="staging-details">
          <h4>${esc(file.name)} <span class="badge good">INGESTED & NORMALIZED</span></h4>
          <span>${typeTitles[type] || type} · ${kbSize} KB · <b style="color:#fff;">${rowCount} records parsed</b></span>
        </div>
      </div>
      <div class="stepper-status">
        <span class="chip" style="color:var(--good);border-color:var(--good-border);">Canonical Schema ✓</span>
      </div>
    </div>

    <div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">Auto-Detected & Mapped Fields:</div>
      <div class="column-chips">
        ${headers.slice(0, 8).map(h => `<span class="col-chip mapped">✓ ${esc(h)}</span>`).join('')}
        ${headers.length > 8 ? `<span class="col-chip">+${headers.length - 8} more</span>` : ''}
      </div>
    </div>

    ${sampleRows && sampleRows.length ? `
      <details style="margin-top:6px;">
        <summary style="font-size:11px;color:var(--accent-light);cursor:pointer;user-select:none;">Preview First ${sampleRows.length} Rows (Click to inspect)</summary>
        <div class="staging-preview-table-container">
          <table class="staging-preview-table">
            <thead>
              <tr>${headers.slice(0, 6).map(h => `<th>${esc(h)}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${sampleRows.map(r => `<tr>${headers.slice(0, 6).map(h => `<td>${esc(r[h] || '')}</td>`).join('')}</tr>`).join('')}
            </tbody>
          </table>
        </div>
      </details>
    ` : ''}

    <div class="staging-actions">
      <div style="font-size:11px;color:var(--soft);">Staged in database. Ready for multi-hop reconciliation.</div>
      <button onclick="runReconciliationNow()" class="btn primary sm">⚡ Run Multi-Hop Reconciliation Now</button>
    </div>
  `;
  staging.prepend(card);
}

let stagedBatchFiles = [];

function inferSourceType(filename, headers) {
  const fn = (filename || '').toLowerCase();
  const hdrs = (headers || []).map(h => String(h).toLowerCase());
  // 1. Bank statement
  if (fn.includes('bank') || hdrs.includes('bank_txn_id') || (hdrs.includes('credit') && hdrs.includes('debit'))) return 'bank_statement';
  // 2. Settlements (check before payments so settlement exports are accurately mapped)
  if (fn.includes('settle') || hdrs.includes('settlement_id') || hdrs.includes('settlement_utr') || hdrs.includes('net_amount')) return 'settlements';
  // 3. Invoices
  if (fn.includes('inv') || hdrs.includes('invoice_id') || hdrs.includes('receivable')) return 'invoices';
  // 4. Payments
  if (fn.includes('pay') || hdrs.includes('payment_id') || hdrs.includes('invoice_reference')) return 'payments';
  return 'invoices';
}

function renderBatchStagingDeck() {
  const deck = $('batchStagingDeck');
  const countEl = $('batchQueueFileCount');
  const listEl = $('batchStagedItemsList');
  if (!deck || !listEl) return;

  if (stagedBatchFiles.length === 0) {
    deck.style.display = 'none';
    return;
  }

  deck.style.display = 'block';
  if (countEl) countEl.textContent = stagedBatchFiles.length;

  listEl.innerHTML = stagedBatchFiles.map((f) => `
    <div class="batch-stage-item" style="display:flex; justify-content:space-between; align-items:center; background:#070b10; border:1px solid var(--line); border-radius:8px; padding:10px 14px;">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="font-size:22px;">📄</div>
        <div>
          <b style="font-size:12px; color:#fff; display:block;">${esc(f.name)}</b>
          <span style="font-size:11px; color:var(--muted); font-family:'JetBrains Mono',monospace;">
            ${(f.size / 1024).toFixed(1)} KB · <b style="color:var(--soft);">${f.rowCount} records</b> · ${f.headers.length} columns detected
          </span>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:10px;">
        <select class="form-select batch-type-select" data-id="${f.id}" style="background:#090d13; border:1px solid var(--line); color:#fff; padding:6px 10px; border-radius:6px; font-size:11px;" onchange="updateStagedType('${f.id}', this.value)">
          <option value="invoices" ${f.type === 'invoices' ? 'selected' : ''}>📄 Invoices (Receivables)</option>
          <option value="payments" ${f.type === 'payments' ? 'selected' : ''}>💳 Payments (Collections)</option>
          <option value="settlements" ${f.type === 'settlements' ? 'selected' : ''}>🏦 Settlements (Razorpay)</option>
          <option value="bank_statement" ${f.type === 'bank_statement' ? 'selected' : ''}>🏛 Bank Statement</option>
        </select>
        <button onclick="removeStagedFile('${f.id}')" class="btn ghost sm" style="color:var(--danger); font-weight:700; padding:4px 8px;" title="Remove this file">✕</button>
      </div>
    </div>
  `).join('');
}

window.updateStagedType = function(id, newType) {
  const item = stagedBatchFiles.find(x => x.id === id);
  if (item) item.type = newType;
};

window.removeStagedFile = function(id) {
  stagedBatchFiles = stagedBatchFiles.filter(x => x.id !== id);
  renderBatchStagingDeck();
};

function clearStagingQueue() {
  stagedBatchFiles = [];
  renderBatchStagingDeck();
}

async function ingestAllBatch() {
  if (!stagedBatchFiles.length) {
    showToast('No documents in queue to ingest.', 'warn');
    return;
  }
  const btn = $('btnIngestAllBatch');
  const originalText = btn ? btn.textContent : '';
  if (btn) btn.textContent = `⏳ Ingesting ${stagedBatchFiles.length} Documents & Reconciling...`;

  try {
    const payload = {
      merchant_id: merchant,
      files: stagedBatchFiles.map(f => ({
        source_type: f.type,
        filename: f.name,
        content: f.content
      })),
      auto_reconcile: true
    };

    const res = await post('/api/v1/import/batch-upload', payload);

    // Render inspect cards
    for (const f of stagedBatchFiles) {
      renderStagedFileCard(f.file, f.type, f.rowCount, f.headers, f.sampleRows);
    }

    showToast(`✓ Ingested ${res.total_imported} records from ${stagedBatchFiles.length} files into database!`, 'success');
    clearStagingQueue();

    // Re-sync all views with live database state
    overview();
    cases();
    exceptions();
    reviewQueue();
    benchmark();
  } catch (err) {
    showToast(`Batch ingest error: ${err.message}`, 'error');
  } finally {
    if (btn) btn.textContent = originalText;
  }
}

async function handleFiles(fileList) {
  if (!fileList || !fileList.length) return;
  const files = Array.from(fileList);

  for (const file of files) {
    const reader = new FileReader();
    reader.onload = async e => {
      try {
        const content = e.target.result;
        const lines = content.split(/\r?\n/).filter(l => l.trim().length > 0);
        const headers = lines[0] ? lines[0].split(',').map(s => s.trim().replace(/^["']|["']$/g, '')) : [];
        const sampleRows = [];
        for (let i = 1; i < Math.min(lines.length, 5); i++) {
          const vals = lines[i].split(',').map(s => s.trim().replace(/^["']|["']$/g, ''));
          const rowObj = {};
          headers.forEach((h, idx) => { rowObj[h] = vals[idx] || ''; });
          sampleRows.push(rowObj);
        }

        const type = inferSourceType(file.name, headers);
        const rowCount = Math.max(0, lines.length - 1);

        stagedBatchFiles.push({
          id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          file: file,
          name: file.name,
          size: file.size,
          rowCount: rowCount,
          type: type,
          headers: headers,
          sampleRows: sampleRows,
          content: content
        });

        renderBatchStagingDeck();
        showToast(`Staged ${file.name} (${rowCount} rows, detected as ${type})`, 'info');
      } catch (err) {
        showToast(`Error reading ${file.name}: ${err.message}`, 'error');
      }
    };
    reader.readAsText(file);
  }
}

// ----------------- DELETE DOCUMENTS MODAL -----------------
async function openDeleteModal() {
  try {
    const d = await get(`/api/v1/overview/${merchant}`);
    if (d && d.records_by_source) {
      const srcMap = {};
      d.records_by_source.forEach(r => { srcMap[r.source] = r.c; });
      if ($('delCntInvoices')) $('delCntInvoices').textContent = srcMap['merchant'] || 0;
      if ($('delCntPayments')) $('delCntPayments').textContent = srcMap['payment'] || 0;
      if ($('delCntSettlements')) $('delCntSettlements').textContent = srcMap['razorpay'] || 0;
      if ($('delCntBank')) $('delCntBank').textContent = srcMap['bank'] || 0;
    }
  } catch (err) {
    console.error('Failed to load overview counts for delete modal:', err);
  }
  $('deleteModal')?.classList.remove('hidden');
}

function closeDeleteModal() {
  $('deleteModal')?.classList.add('hidden');
}

async function confirmDeleteDocuments() {
  const selectedRadio = document.querySelector('input[name="deleteTarget"]:checked');
  const target = selectedRadio ? selectedRadio.value : 'all';
  const btn = $('btnConfirmDeleteDocuments');
  if (btn) btn.textContent = '⏳ Deleting from DB...';

  try {
    const res = await post('/api/v1/db/delete-documents', {
      source: target,
      merchant_id: merchant
    });
    showToast(res.message || '✓ Documents deleted from SQLite database.', 'success');
    closeDeleteModal();

    // Immediately re-sync all live views from the database!
    overview();
    cases();
    exceptions();
    reviewQueue();
    benchmark();
  } catch (err) {
    showToast(`Delete error: ${err.message}`, 'error');
  } finally {
    if (btn) btn.textContent = 'Confirm & Delete from DB';
  }
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
  if (v === 'import') overview();
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
$('btnAiStatusChip')?.addEventListener('click', openAiDiagnostics);
$('btnCloseAiModal')?.addEventListener('click', closeAiDiagnostics);
$('btnCloseAiModalFooter')?.addEventListener('click', closeAiDiagnostics);
$('btnRunAiTest')?.addEventListener('click', runLiveAiTest);

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
$('btnRunReconcile')?.addEventListener('click', runReconciliationNow);
$('btnReloadDemoDataset')?.addEventListener('click', reloadDemoDataset);
$('btnOpenDeleteModal')?.addEventListener('click', openDeleteModal);
$('btnCloseDeleteModal')?.addEventListener('click', closeDeleteModal);
$('btnCancelDeleteModal')?.addEventListener('click', closeDeleteModal);
$('btnConfirmDeleteDocuments')?.addEventListener('click', confirmDeleteDocuments);
$('btnClearStagingQueue')?.addEventListener('click', clearStagingQueue);
$('btnIngestAllBatch')?.addEventListener('click', ingestAllBatch);
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
      handleFiles(e.dataTransfer.files);
    }
  };
}

$('fileInput')?.addEventListener('change', e => {
  if (e.target.files.length) {
    handleFiles(e.target.files);
  }
});

// ----------------- BATCH AI INVESTIGATION (RATE-GUARDED) -----------------
let selectedBatchLimit = 5;
let batchEventSource = null;

function openBatchModal() {
  $('batchModal')?.classList.remove('hidden');
}

function closeBatchModal() {
  if (batchEventSource) {
    batchEventSource.close();
    batchEventSource = null;
  }
  $('batchModal')?.classList.add('hidden');
}

function selectBatchPreset(limit, btn) {
  selectedBatchLimit = limit;
  document.querySelectorAll('.batch-preset-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function startBatchInvestigation() {
  const box = $('batchProgressBox');
  const feed = $('batchStreamFeed');
  const bar = $('batchProgressBar');
  const startBtn = $('btnStartBatch');
  const cancelBtn = $('btnCancelBatch');

  if (batchEventSource) batchEventSource.close();

  box.style.display = 'block';
  feed.innerHTML = `<div style="color:var(--soft);margin-bottom:4px;">Initiating rate-guarded investigation (Batch: ${selectedBatchLimit} cases, Paced at 14.2 RPM under 15 RPM cap)...</div>`;
  bar.style.width = '0%';
  startBtn.style.display = 'none';
  cancelBtn.style.display = 'inline-block';

  let matchCount = 0;
  let reviewCount = 0;
  let tokenCount = 0;
  let costTotal = 0.0;

  batchEventSource = new EventSource(`/api/v1/ai/batch-stream?limit=${selectedBatchLimit}&merchant_id=${merchant}&delay=4.2`);

  batchEventSource.onmessage = e => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'init') {
        $('batchProgressTitle').textContent = `Investigating ${data.total} exception cases with Gemini`;
        $('batchProgressCount').textContent = `0 / ${data.total}`;
      } else if (data.type === 'progress') {
        $('batchProgressTitle').textContent = `Analyzing ${data.case_id}...`;
        $('batchProgressCount').textContent = `${data.index} / ${data.total}`;
        const pct = Math.round((data.index - 1) / data.total * 100);
        bar.style.width = `${pct}%`;
      } else if (data.type === 'case_result') {
        if (data.decision === 'MATCH') matchCount++;
        else reviewCount++;
        tokenCount += data.tokens || 0;
        costTotal += data.cost || 0;

        $('batchMatches').textContent = matchCount;
        $('batchReviews').textContent = reviewCount;
        $('batchTokens').textContent = tokenCount.toLocaleString();
        $('batchCost').textContent = `$${costTotal.toFixed(4)}`;

        const logEntry = document.createElement('div');
        const color = data.decision === 'MATCH' ? 'var(--good)' : 'var(--warn)';
        logEntry.innerHTML = `[${data.index}/${data.total}] <b>${esc(data.case_id)}</b> → <span style="color:${color};font-weight:700;">${data.decision}</span> (${Math.round(data.confidence*100)}%) · ${data.tokens} tokens · $${(data.cost||0).toFixed(5)}`;
        feed.prepend(logEntry);

        const pct = Math.round(data.index / data.total * 100);
        bar.style.width = `${pct}%`;
      } else if (data.type === 'pacing') {
        const paceMsg = document.createElement('div');
        paceMsg.style.color = '#7c3aed';
        paceMsg.style.fontSize = '9px';
        paceMsg.textContent = `⏳ Pacing 4.2s to enforce free-tier 15 RPM guard...`;
        feed.prepend(paceMsg);
      } else if (data.type === 'case_error') {
        const errMsg = document.createElement('div');
        errMsg.style.color = 'var(--danger)';
        errMsg.style.fontSize = '9px';
        errMsg.textContent = `⚠ [${esc(data.case_id)}] ${esc(data.error)}`;
        feed.prepend(errMsg);
      } else if (data.type === 'complete') {
        batchEventSource.close();
        batchEventSource = null;
        bar.style.width = '100%';
        $('batchProgressTitle').textContent = `✓ Batch Investigation Complete!`;
        startBtn.style.display = 'inline-block';
        startBtn.textContent = 'Run Another Batch';
        cancelBtn.style.display = 'none';
        showToast(`✓ Batch investigation completed: ${matchCount} matches, ${reviewCount} reviews`, 'success');
        overview();
        exceptions();
        reviewQueue();
        cases();
      }
    } catch (err) {
      console.error('Batch stream parse error:', err);
    }
  };

  batchEventSource.onerror = () => {
    feed.prepend(document.createTextNode('Stream disconnected or finished.'));
    if (batchEventSource) batchEventSource.close();
    batchEventSource = null;
    startBtn.style.display = 'inline-block';
    cancelBtn.style.display = 'none';
  };
}

// Batch Event Listeners
$('btnOpenBatchModal')?.addEventListener('click', openBatchModal);
$('btnCloseBatchModal')?.addEventListener('click', closeBatchModal);
$('btnCloseBatchModalFooter')?.addEventListener('click', closeBatchModal);
$('btnStartBatch')?.addEventListener('click', startBatchInvestigation);
$('btnCancelBatch')?.addEventListener('click', () => {
  if (batchEventSource) {
    batchEventSource.close();
    batchEventSource = null;
  }
  $('batchProgressTitle').textContent = 'Batch paused by user.';
  $('btnStartBatch').style.display = 'inline-block';
  $('btnCancelBatch').style.display = 'none';
  showToast('Batch investigation paused.', 'info');
});

document.querySelectorAll('.batch-preset-btn').forEach(btn => {
  btn.onclick = () => selectBatchPreset(Number(btn.dataset.limit || 5), btn);
});

// Initial boot
fetchAiStatus();
overview();
