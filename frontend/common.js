/* ── PMS 3.0 Common Utilities ── */
const API = 'https://placement-management-system-u48x.onrender.com';

const auth = {
  getToken: () => localStorage.getItem('pms_token'),
  getUser: () => JSON.parse(localStorage.getItem('pms_user') || 'null'),
  save(token, user) {
    localStorage.setItem('pms_token', token);
    localStorage.setItem('pms_user', JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem('pms_token');
    localStorage.removeItem('pms_user');
  },
  require() {
    if (!this.getToken()) { location.href = 'login.html'; return false; }
    return true;
  }
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

function openModal(html, large = false) {
  const o = document.getElementById('modal-overlay');
  const m = document.getElementById('modal-content');
  m.className = 'modal' + (large ? ' modal-lg' : '');
  m.innerHTML = html;
  o.classList.add('active');
}
function closeModal() { document.getElementById('modal-overlay').classList.remove('active'); }
document.addEventListener('click', e => { if (e.target.id === 'modal-overlay') closeModal(); });

function pb() { return document.getElementById('page-body'); }

function statusBadge(s) {
  const m = {
    placed: 'green', unplaced: 'orange',
    present: 'green', absent: 'red', late: 'orange',
    upcoming: 'blue', active: 'green', completed: 'gray',
    applied: 'blue', shortlisted: 'cyan', selected: 'green', rejected: 'red',
    admin: 'purple', trainer: 'blue', student: 'gray'
  };
  return `<span class="badge badge-${m[s] || 'gray'}">${s}</span>`;
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function timeAgo(d) {
  if (!d) return '';
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/* ── SVG Icons ── */
const IC = {
  dash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  user: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>`,
  batch: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/><line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/></svg>`,
  class_: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>`,
  cal: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M9 16l2 2 4-4"/></svg>`,
  doc: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  brief: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>`,
  out: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
  menu: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
  bldg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9l8-5 8 5v10"/><path d="M9 19v-6h6v6"/><line x1="2" y1="19" x2="22" y2="19"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
};

/* ── Sidebar Builder ── */
function buildSidebar(active) {
  const u = auth.getUser();
  if (!u) return '';
  const r = u.role;
  const ini = (u.full_name || u.email)[0].toUpperCase();
  const displayName = u.full_name || u.email;

  let nav = `<a class="nav-item ${active==='dashboard'?'active':''}" href="dashboard.html">${IC.dash} Dashboard</a>`;

  if (r === 'student') {
    nav += `<a class="nav-item ${active==='profile'?'active':''}" href="profile.html">${IC.user} My Profile</a>`;
    nav += `<a class="nav-item ${active==='notifications'?'active':''}" href="notifications.html">${IC.bell} Notifications</a>`;
    nav += `<a class="nav-item ${active==='classes'?'active':''}" href="classes.html">${IC.class_} My Classes</a>`;
    nav += `<div class="nav-section">Placement</div>`;
    nav += `<a class="nav-item ${active==='drives'?'active':''}" href="drives.html">${IC.brief} Placement Drives</a>`;
    nav += `<a class="nav-item ${active==='attendance'?'active':''}" href="attendance.html">${IC.cal} My Attendance</a>`;
    nav += `<a class="nav-item ${active==='assessments'?'active':''}" href="assessments.html">${IC.doc} Assessments</a>`;
  }

  if (r === 'trainer' || r === 'admin') {
    nav += `<div class="nav-section">Management</div>`;
    nav += `<a class="nav-item ${active==='students'?'active':''}" href="students.html">${IC.users} Students</a>`;
    nav += `<a class="nav-item ${active==='batches'?'active':''}" href="batches.html">${IC.batch} Batches</a>`;
    nav += `<a class="nav-item ${active==='classes'?'active':''}" href="classes.html">${IC.class_} Classes</a>`;
    nav += `<a class="nav-item ${active==='notifications'?'active':''}" href="notifications.html">${IC.bell} Notifications</a>`;
    nav += `<div class="nav-section">Academics</div>`;
    nav += `<a class="nav-item ${active==='attendance'?'active':''}" href="attendance.html">${IC.cal} Attendance</a>`;
    nav += `<a class="nav-item ${active==='assessments'?'active':''}" href="assessments.html">${IC.doc} Assessments</a>`;
    nav += `<div class="nav-section">Placement</div>`;
    nav += `<a class="nav-item ${active==='drives'?'active':''}" href="drives.html">${IC.brief} Drives</a>`;
    nav += `<a class="nav-item ${active==='analytics'?'active':''}" href="analytics.html">${IC.chart} Analytics</a>`;
  }

  if (r === 'admin') {
    nav += `<div class="nav-section">Admin</div>`;
    nav += `<a class="nav-item ${active==='colleges'?'active':''}" href="colleges.html">${IC.bldg} Colleges</a>`;
    nav += `<a class="nav-item ${active==='admin-users'?'active':''}" href="admin-users.html">${IC.settings} User Management</a>`;
  }

  return `
<button class="mobile-toggle" id="mob-toggle">${IC.menu}</button>
<div class="sidebar-backdrop" id="sb-backdrop"></div>
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <div class="brand-row">
      <div class="b-icon">P</div>
      <div><div class="b-name">PMS 3.0</div><div class="b-sub">MITADT University</div></div>
    </div>
  </div>
  <nav class="sidebar-nav">${nav}</nav>
  <div class="sidebar-footer">
    <div class="user-chip">
      <div class="user-avatar">${ini}</div>
      <div class="user-info">
        <div class="uname">${displayName}</div>
        <div class="urole">${r}</div>
      </div>
    </div>
    <a class="nav-item mt-1" href="#" id="logout-btn" style="color:#f87171">${IC.out} Logout</a>
  </div>
</aside>`;
}

function initPage(active, title, subtitle, headerActions = '') {
  if (!auth.require()) return false;

  // Check must_change_password
  const u = auth.getUser();
  if (u && u.must_change_password && active !== 'set-password') {
    location.href = 'set-password.html';
    return false;
  }

  document.getElementById('app').innerHTML = `
    ${buildSidebar(active)}
    <main class="main-content">
      <div class="page-header">
        <div class="page-header-left">
          <h1>${title}</h1>
          ${subtitle ? `<p>${subtitle}</p>` : ''}
        </div>
        ${headerActions ? `<div class="btn-group">${headerActions}</div>` : ''}
      </div>
      <div class="page-body page-enter" id="page-body">
        <div class="loading-overlay"><div class="spinner"></div><span>Loading...</span></div>
      </div>
    </main>`;

  document.getElementById('logout-btn').onclick = e => {
    e.preventDefault();
    auth.clear();
    location.href = 'login.html';
  };

  const mt = document.getElementById('mob-toggle');
  const sb = document.getElementById('sidebar');
  const bd = document.getElementById('sb-backdrop');
  if (mt) {
    mt.onclick = () => { sb.classList.toggle('open'); bd.classList.toggle('active'); };
    bd.onclick = () => { sb.classList.remove('open'); bd.classList.remove('active'); };
  }
  return true;
}
