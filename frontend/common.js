/* ===== PMS 3.0 — Shared Utilities ===== */
const API = 'https://placement-management-system-u48x.onrender.com';

const auth = {
  getToken: () => localStorage.getItem('pms_token'),
  getUser: () => JSON.parse(localStorage.getItem('pms_user') || 'null'),
  save(token, user) { localStorage.setItem('pms_token', token); localStorage.setItem('pms_user', JSON.stringify(user)); },
  clear() { localStorage.removeItem('pms_token'); localStorage.removeItem('pms_user'); },
  require() { if (!this.getToken()) { location.href = 'login.html'; return false; } return true; }
};

async function api(path, opts = {}) {
  const h = { 'Content-Type': 'application/json' };
  const t = auth.getToken();
  if (t) h['Authorization'] = 'Bearer ' + t;
  const r = await fetch(API + path, { ...opts, headers: { ...h, ...opts.headers } });
  if (r.status === 401) { auth.clear(); location.href = 'login.html'; throw new Error('Session expired'); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : JSON.stringify(d.detail || d));
  return d;
}

function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function openModal(html) {
  const o = document.getElementById('modal-overlay'), m = document.getElementById('modal-content');
  m.innerHTML = html; o.classList.add('active');
}
function closeModal() { document.getElementById('modal-overlay').classList.remove('active'); }
document.addEventListener('click', e => { if (e.target.id === 'modal-overlay') closeModal(); });

const IC = {
  dash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>',
  bldg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9l8-5 8 5v10"/><path d="M9 19v-6h6v6"/><line x1="2" y1="19" x2="22" y2="19"/></svg>',
  cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M9 16l2 2 4-4"/></svg>',
  doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
  brief: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  out: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
  menu: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
};

function buildSidebar(active) {
  const u = auth.getUser(); if (!u) return '';
  const r = u.role, ini = u.email[0].toUpperCase();
  let nav = `<a class="nav-item ${active==='dashboard'?'active':''}" href="dashboard.html">${IC.dash} Dashboard</a>`;
  if (r === 'student') nav += `<a class="nav-item ${active==='profile'?'active':''}" href="profile.html">${IC.user} My Profile</a>`;
  if (r === 'admin' || r === 'trainer') nav += `<div class="nav-label">Management</div><a class="nav-item ${active==='students'?'active':''}" href="students.html">${IC.users} Students</a>`;
  nav += `<a class="nav-item ${active==='colleges'?'active':''}" href="colleges.html">${IC.bldg} Colleges</a>`;
  nav += `<a class="nav-item ${active==='attendance'?'active':''}" href="attendance.html">${IC.cal} Attendance</a>`;
  nav += `<a class="nav-item ${active==='assessments'?'active':''}" href="assessments.html">${IC.doc} Assessments</a>`;
  nav += `<a class="nav-item ${active==='drives'?'active':''}" href="drives.html">${IC.brief} Placement Drives</a>`;
  if (r !== 'student') nav += `<div class="nav-label">Insights</div><a class="nav-item ${active==='analytics'?'active':''}" href="analytics.html">${IC.chart} Analytics</a>`;
  nav += `<div style="flex:1"></div><a class="nav-item" href="#" id="logout-btn">${IC.out} Logout</a>`;
  return `<button class="mobile-toggle" id="mob-toggle">${IC.menu}</button>
<div class="sidebar-backdrop" id="sb-backdrop"></div>
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand"><h2>🎓 PMS</h2><span>Placement Management</span></div>
  <nav class="sidebar-nav">${nav}</nav>
  <div class="sidebar-footer"><div class="user-chip"><div class="user-avatar">${ini}</div><div class="user-info"><div class="name">${u.email}</div><div class="role">${r}</div></div></div></div>
</aside>`;
}

function initPage(active, title, subtitle) {
  if (!auth.require()) return false;
  document.getElementById('app').innerHTML = `${buildSidebar(active)}
<main class="main-content">
  <div class="page-header"><h1>${title}</h1><p>${subtitle}</p></div>
  <div class="page-body page-enter" id="page-body"><div class="loading-overlay"><div class="spinner"></div><span>Loading...</span></div></div>
</main>`;
  document.getElementById('logout-btn').onclick = e => { e.preventDefault(); auth.clear(); location.href = 'login.html'; };
  const mt = document.getElementById('mob-toggle'), sb = document.getElementById('sidebar'), bd = document.getElementById('sb-backdrop');
  if (mt) { mt.onclick = () => { sb.classList.toggle('open'); bd.classList.toggle('active'); }; bd.onclick = () => { sb.classList.remove('open'); bd.classList.remove('active'); }; }
  return true;
}

function statusBadge(s) {
  const m = { placed:'green', unplaced:'orange', present:'green', absent:'red', late:'orange', upcoming:'blue', active:'green', completed:'purple', pending:'orange', selected:'green', rejected:'red', shortlisted:'cyan' };
  return `<span class="badge badge-${m[s]||'blue'}">${s}</span>`;
}

function pb() { return document.getElementById('page-body'); }
