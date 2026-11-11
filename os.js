"use strict";
/* ICS-OS 0.1.
   Theme: Microsoft Dynamics AX 2012 / Enterprise ERP / Aero Glass / Luna / Skeuomorphic Retro UI with Web Audio API.
   Generated page: edit os.js, os.css and os_template.html, then run build_os.py. [PROPOSAL] */
const D = /*__DATA__*/null;
const $ = (s, r) => (r || document).querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const plain = h => h.replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/\s+/g, " ").trim();
const OSN = D.os;
const ROLE = Object.fromEntries(D.roles.map(r => [r.id, r]));
const PERSON = D.people || {};
const DOC = Object.fromEntries(D.docs.map(d => [d.no, d]));
const byCode = Object.fromEntries(D.msgs.map(m => [m.code, m]));
const S = Object.assign({role: "", box: "", ar: false, muted: false, theme: "auto", skin: "classic"}, JSON.parse(localStorage.getItem("icsos") || sessionStorage.getItem("icsos") || "{}"));
if (!ROLE[S.role]) S.role = "";
if (S.theme && S.theme !== "auto") document.documentElement.dataset.theme = S.theme;
if (S.skin === "aero") document.documentElement.dataset.skin = "aero";
const save = () => {
  try {
    sessionStorage.setItem("icsos", JSON.stringify(S));
    localStorage.setItem("icsos", JSON.stringify(S));
  } catch (_) {}
};
function applyTheme(themeId) {
  S.theme = themeId || "auto";
  save();
  if (S.theme && S.theme !== "auto") {
    document.documentElement.dataset.theme = S.theme;
  } else {
    delete document.documentElement.dataset.theme;
  }
}
function applySkin(skin) {
  S.skin = skin === "aero" ? "aero" : "classic";
  save();
  if (S.skin === "aero") document.documentElement.dataset.skin = "aero";
  else delete document.documentElement.dataset.skin;
}
const author = () => S.role === "all";
const level = () => ROLE[S.role].level;
const canDoc = (d, role) => d.roles.includes(role || S.role);
const docsFor = role => D.docs.filter(d => canDoc(d, role));
const seenBy = role => D.msgs.filter(m => m.roles.includes(role));
const TIERLBL = d => d.outside ? "No tier" : ["All staff", "PTKW", "Branch Director", "Board"][d.tier];
document.title = OSN.name + " " + OSN.version;

/* ----------------------------------------------------------- Web Audio API ---- */
const Sound = {
  ctx: null,
  muted: !!S.muted,
  init() {
    if (!this.ctx && typeof window !== "undefined") {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
  },
  play(fn) {
    if (this.muted) return;
    try {
      this.init();
      if (this.ctx) fn(this.ctx);
    } catch (_) {}
  },
  click() {
    this.play(c => {
      const now = c.currentTime;
      const osc = c.createOscillator();
      const gain = c.createGain();
      const filter = c.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(1400, now);
      filter.Q.setValueAtTime(2.5, now);
      osc.type = "sine";
      osc.frequency.setValueAtTime(1500, now);
      osc.frequency.exponentialRampToValueAtTime(160, now + 0.02);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.02);
      osc.connect(filter);
      filter.connect(gain);
      gain.connect(c.destination);
      osc.start(now);
      osc.stop(now + 0.022);
    });
  },
  open() {
    this.play(c => {
      const now = c.currentTime;
      // Retro enterprise rising chime chord (C5 -> G5 -> C6)
      [[523.25, 0, 0.16, 0.14], [783.99, 0.04, 0.22, 0.15], [1046.5, 0.08, 0.26, 0.12]].forEach(([freq, start, dur, vol]) => {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, now + start);
        gain.gain.setValueAtTime(0.001, now + start);
        gain.gain.linearRampToValueAtTime(vol, now + start + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(now + start);
        osc.stop(now + start + dur);
      });
    });
  },
  close() {
    this.play(c => {
      const now = c.currentTime;
      [[659.25, 0, 0.12, 0.12], [440.0, 0.03, 0.16, 0.10]].forEach(([freq, start, dur, vol]) => {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, now + start);
        gain.gain.setValueAtTime(vol, now + start);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(now + start);
        osc.stop(now + start + dur);
      });
    });
  },
  min() {
    this.play(c => {
      const now = c.currentTime;
      const osc = c.createOscillator();
      const gain = c.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(320, now + 0.04);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(c.destination);
      osc.start(now);
      osc.stop(now + 0.045);
    });
  },
  max() {
    this.play(c => {
      const now = c.currentTime;
      const osc = c.createOscillator();
      const gain = c.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(980, now + 0.04);
      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(c.destination);
      osc.start(now);
      osc.stop(now + 0.045);
    });
  },
  ding() {
    this.play(c => {
      const now = c.currentTime;
      // Classic retro alert bell chord (E5 + A5 + B5)
      [[587.33, 0, 0.6, 0.18], [880.0, 0, 0.5, 0.14], [1174.66, 0, 0.45, 0.10]].forEach(([freq, start, dur, vol]) => {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, now + start);
        gain.gain.setValueAtTime(vol, now + start);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(now + start);
        osc.stop(now + start + dur);
      });
    });
  },
  boot() {
    this.play(c => {
      const now = c.currentTime;
      // Nostalgic corporate 4-tone boot chord (F4 -> Bb4 -> C5 -> F5)
      const notes = [
        [349.23, 0.00, 1.2, 0.12],
        [466.16, 0.18, 1.1, 0.14],
        [523.25, 0.36, 1.0, 0.15],
        [698.46, 0.54, 1.4, 0.18]
      ];
      notes.forEach(([freq, start, dur, vol]) => {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, now + start);
        gain.gain.setValueAtTime(0.001, now + start);
        gain.gain.linearRampToValueAtTime(vol, now + start + 0.08);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(now + start);
        osc.stop(now + start + dur);
      });
    });
  },
  toggle() {
    this.muted = !this.muted;
    S.muted = this.muted;
    save();
    if (!this.muted) this.click();
    return this.muted;
  }
};

/* ------------------------------------------------------------------ icons ---- */
const MARK = '<svg viewBox="0 0 48 48" aria-hidden="true"><image href="data:image/png;base64,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" width="48" height="48"/></svg>';

const AVATAR = {
  staff: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-staff)" stroke="#C9A84C" stroke-width="2.5"/><circle cx="32" cy="23" r="10" fill="#F4EEE1"/><path d="M16 51c0-8.8 7.2-16 16-16s16 7.2 16 16" fill="#F4EEE1"/><defs><linearGradient id="g-staff" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2a4577"/><stop offset="100%" stop-color="#142442"/></linearGradient></defs></svg>',
  ptkw: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-ptkw)" stroke="#6FA3B5" stroke-width="2.5"/><path d="M32 14l16 6v13c0 10-6.8 19-16 22-9.2-3-16-12-16-22V20l16-6z" fill="#E6EBEF" opacity="0.9"/><circle cx="32" cy="31" r="5" fill="#183247"/><defs><linearGradient id="g-ptkw" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2a5875"/><stop offset="100%" stop-color="#142c3d"/></linearGradient></defs></svg>',
  director: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-dir)" stroke="#B8923A" stroke-width="3"/><circle cx="32" cy="32" r="18" fill="none" stroke="#C9A84C" stroke-width="2.5"/><path d="M17 50 C8 32 20 12 36 18 C46 22 45 36 36 46" fill="none" stroke="#C9A84C" stroke-width="3.5" stroke-linecap="round"/><circle cx="32" cy="32" r="6" fill="#C9A84C"/><defs><linearGradient id="g-dir" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1e345c"/><stop offset="100%" stop-color="#0b172d"/></linearGradient></defs></svg>',
  research: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-res)" stroke="#8FBF9F" stroke-width="2.5"/><path d="M28 17h8v10l8 14c1 1.8-.2 4-2.3 4H22.3c-2.1 0-3.3-2.2-2.3-4l8-14V17z" fill="#E7EDE9" opacity="0.9"/><path d="M23 41l4-7h10l4 7H23z" fill="#8FBF9F"/><defs><linearGradient id="g-res" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2c5c54"/><stop offset="100%" stop-color="#14302c"/></linearGradient></defs></svg>',
  design: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-des)" stroke="#E39B6B" stroke-width="2.5"/><circle cx="32" cy="32" r="16" fill="none" stroke="#F6F0EA" stroke-width="2.5"/><circle cx="26" cy="26" r="3.5" fill="#E39B6B"/><circle cx="38" cy="26" r="3.5" fill="#C9A84C"/><circle cx="35" cy="38" r="3.5" fill="#6FA3B5"/><circle cx="23" cy="36" r="2.5" fill="#F6F0EA"/><defs><linearGradient id="g-des" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#55427d"/><stop offset="100%" stop-color="#2a2044"/></linearGradient></defs></svg>',
  access: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-acc)" stroke="#C9A84C" stroke-width="2.5"/><polygon points="32,16 45,26 45,42 32,50 19,42 19,26" fill="none" stroke="#C9A84C" stroke-width="2.5"/><circle cx="32" cy="33" r="5" fill="#C9A84C"/><defs><linearGradient id="g-acc" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1e2238"/><stop offset="100%" stop-color="#080a14"/></linearGradient></defs></svg>',
  all: '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="url(#g-all)" stroke="#dcd8cc" stroke-width="2.5"/><path d="M22 28h20v18H22z" fill="#EFEDE8"/><path d="M26 28v-6a6 6 0 0 1 12 0v6" fill="none" stroke="#EFEDE8" stroke-width="3" stroke-linecap="round"/><circle cx="32" cy="37" r="2.5" fill="#23262e"/><defs><linearGradient id="g-all" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b3f4c"/><stop offset="100%" stop-color="#181a20"/></linearGradient></defs></svg>'
};

const ICON = {
  mail: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="5" y="11" width="38" height="27" rx="3" fill="#F4EEE1" stroke="#1A2E52" stroke-width="2.5"/>' +
    '<path d="M7 14l17 13L41 14" fill="none" stroke="#1A2E52" stroke-width="2.5" stroke-linejoin="round"/><circle cx="37" cy="14" r="6.5" fill="#C9A84C" stroke="#1A2E52" stroke-width="2"/></svg>',
  drive: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M14 38a9.5 9.5 0 0 1-1.5-18.9A12 12 0 0 1 35.5 17 10.5 10.5 0 0 1 35 38z" fill="#F4EEE1" stroke="#1A2E52" stroke-width="2.5" stroke-linejoin="round"/>' +
    '<path d="M17 26h6l2 2.5h8V35H17z" fill="#C9A84C" stroke="#1A2E52" stroke-width="2" stroke-linejoin="round"/></svg>',
  doc: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M11 5h20l9 9v29H11z" fill="#F4EEE1" stroke="#1A2E52" stroke-width="2.5" stroke-linejoin="round"/>' +
    '<path d="M31 5v9h9" fill="#C9A84C" stroke="#1A2E52" stroke-width="2.5" stroke-linejoin="round"/><path d="M17 22h18M17 28h18M17 34h11" stroke="#1A2E52" stroke-width="2.5" stroke-linecap="round"/></svg>',
  timeline: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 24h32" stroke="#1A2E52" stroke-width="2.5" stroke-linecap="round"/>' +
    '<circle cx="12" cy="24" r="5" fill="#F4EEE1" stroke="#1A2E52" stroke-width="2.5"/><circle cx="24" cy="24" r="5" fill="#C9A84C" stroke="#1A2E52" stroke-width="2.5"/><circle cx="36" cy="24" r="5" fill="#F4EEE1" stroke="#1A2E52" stroke-width="2.5"/>' +
    '<path d="M12 14v5M24 29v5M36 14v5" stroke="#1A2E52" stroke-width="2.5" stroke-linecap="round"/></svg>',
  file: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l5 5v15H6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 2v5h5M9 13h7M9 17h7" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
  folder: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5h7l2 2.5h11V20H2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
  cloud: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 19a4.5 4.5 0 0 1-.7-8.9A6 6 0 0 1 17.8 9 5 5 0 0 1 18 19z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 14l2.2 2.2L15 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  out: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4H4v16h5M15 8l5 4-5 4M20 12H9" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v6M12 7.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  sound: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5L6 9H2v6h4l5 4V5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  mute: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5L6 9H2v6h4l5 4V5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><line x1="16" y1="9" x2="22" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="22" y1="9" x2="16" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  power: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v10M18.36 5.64a9 9 0 1 1-12.73 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><line x1="16.5" y1="16.5" x2="22" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  fullscreen: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  compress: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3v6H3M15 3v6h6M9 21v-6H3M15 21v-6h6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  palette: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-9 9c0 4.97 4.03 9 9 9 .83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-4.97-4.03-9-10-9zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9s1.5.67 1.5 1.5S7.33 12 6.5 12zm3-4c-.83 0-1.5-.67-1.5-1.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5S18.33 12 17.5 12z" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>'
};

/* ------------------------------------------------------------------ themes ---- */
const THEMES = [
  {id: "auto", name: "Automatic (Role Clearance)", category: "System", preview: ["#1A2E52", "#C9A84C", "#F4EEE1"], desc: "Follows the active badge clearance role palette automatically."},
  {id: "staff", name: "ICS Classic (Earth Branch)", category: "Corporate", preview: ["#1A2E52", "#C9A84C", "#F4EEE1"], desc: "Document 2.32 standard Deep Blue & Warm Gold on Transit beige."},
  {id: "ptkw", name: "PTKW Operations", category: "Corporate", preview: ["#183247", "#6FA3B5", "#E6EBEF"], desc: "Cool slate and ice cyan for Level 5, 8 & 9 operations."},
  {id: "director", name: "Executive Office", category: "Corporate", preview: ["#10203f", "#B8923A", "#EEE9DD"], desc: "Formal midnight navy and ivory for the Branch Director."},
  {id: "research", name: "Research Division", category: "Corporate", preview: ["#1d3a36", "#8FBF9F", "#E7EDE9"], desc: "Laboratory pine and sage for EOD assessment suites."},
  {id: "design", name: "Brand & Interface", category: "Corporate", preview: ["#3a2f5c", "#E39B6B", "#F6F0EA"], desc: "Plum and warm copper of the internal communications team."},
  {id: "access", name: "Board Eclipse", category: "Corporate", preview: ["#0b1022", "#C9A84C", "#121830"], desc: "Pitch midnight and sovereign gold for Board clearance."},
  {id: "all", name: "Master Archive", category: "Corporate", preview: ["#23262e", "#C9A84C", "#EFEDE8"], desc: "Heavy graphite and titanium master author archive view."},
  {id: "win95", name: "Windows 95/98 Classic", category: "Retro Computing", preview: ["#000080", "#008080", "#c0c0c0"], desc: "Authentic 1995 desktop teal with 3D beveled silver-gray chrome."},
  {id: "luna", name: "Luna Blue (Early 2000s)", category: "Retro Computing", preview: ["#0055ea", "#f39c12", "#ece9d8"], desc: "Bright royal blue titlebars and warm silver-sand panels."},
  {id: "amber", name: "Amber CRT Phosphor", category: "Retro Terminals", preview: ["#ffb000", "#ff9900", "#120a00"], desc: "Monochrome glowing amber CRT workstation from 1989."},
  {id: "matrix", name: "Green Matrix CRT", category: "Retro Terminals", preview: ["#00ff66", "#33ff33", "#031203"], desc: "High-phosphor green mainframe terminal console."},
  {id: "solar", name: "Solarized Workstation", category: "Specialty", preview: ["#002b36", "#b58900", "#fdf6e3"], desc: "Low-contrast precision palette for extended night shifts."},
  {id: "forest", name: "Evergreen Grove", category: "Nature", preview: ["#1e3a2a", "#c9a24c", "#eaf0e6"], desc: "Deep conifer green with brass trim on pale moss."},
  {id: "ocean", name: "Deep Ocean", category: "Nature", preview: ["#0b3a53", "#2fb3c4", "#e4eff3"], desc: "Abyssal blue with a bright kelp-teal accent."},
  {id: "sand", name: "Desert Sand", category: "Nature", preview: ["#6b3f1f", "#d08a3c", "#f4ead8"], desc: "Warm terracotta and amber on sun-bleached sand."},
  {id: "rose", name: "Rosewood", category: "Corporate", preview: ["#5a1f2e", "#d3a35a", "#f5ebe8"], desc: "Oxblood and antique gold on blush paper."},
  {id: "nord", name: "Nordic Frost", category: "Specialty", preview: ["#2e3b52", "#88c0d0", "#eceff4"], desc: "Cool polar blues with a pale ice accent."},
  {id: "mint", name: "Clinic Mint", category: "Specialty", preview: ["#1f4f4a", "#4fbfa8", "#eaf5f2"], desc: "Clean sterile teal and mint, as in the Level 3 wellness suites."},
  {id: "dusk", name: "Dusk Violet", category: "Dark", preview: ["#1a1330", "#b794f6", "#221a3d"], desc: "Dark indigo and violet for the night shift."},
  {id: "slate", name: "Graphite Night", category: "Dark", preview: ["#14181f", "#5cc8ff", "#1c222c"], desc: "Near-black graphite with an electric blue accent."},
  {id: "contrast", name: "High Contrast", category: "Accessibility", preview: ["#000000", "#ffd400", "#ffffff"], desc: "Black on white with yellow highlights for maximum legibility."}
];

function openThemeDialog() {
  Sound.click();
  const m = $("#modal");
  let curPick = S.theme || "auto";
  let curSkin = S.skin === "aero" ? "aero" : "classic";

  const renderSwatches = th => {
    return '<span class="os-theme-swatches">' +
      th.preview.map(c => '<span class="os-theme-swatch" style="background:' + c + '"></span>').join("") +
      '</span>';
  };

  const getThemeItem = th => {
    const isSel = th.id === curPick;
    return '<div class="os-theme-row' + (isSel ? ' active' : '') + '" data-tid="' + th.id + '">' +
      renderSwatches(th) +
      '<div class="os-theme-meta">' +
        '<b>' + esc(th.name) + '</b>' +
        '<small>' + esc(th.desc) + '</small>' +
      '</div>' +
      '</div>';
  };

  const updatePreview = () => {
    const th = THEMES.find(t => t.id === curPick) || THEMES[0];
    const previewEl = $("#theme-preview-box");
    if (!previewEl) return;
    const c1 = th.preview[0], c2 = th.preview[1], c3 = th.preview[2];
    previewEl.style.background = c3;
    previewEl.innerHTML =
      '<div class="os-prev-win" style="background:' + c3 + '; border-color:' + c1 + ';">' +
        '<div class="os-prev-titlebar" style="background:' + c1 + '; color:#fff;">' +
          '<span>Sample Workstation Window</span>' +
          '<span class="os-prev-close" style="border-color:' + c2 + ';">\u00d7</span>' +
        '</div>' +
        '<div class="os-prev-content" style="color:' + (th.id === 'amber' ? '#ffb000' : th.id === 'matrix' ? '#55ff55' : th.id === 'access' ? '#ebe6d6' : '#1f2433') + ';">' +
          '<span><b>' + esc(th.name) + '</b> &middot; <i>' + esc(th.category) + '</i></span>' +
          '<div class="os-prev-bar" style="background:' + c2 + '; color:' + (th.id === 'access' || th.id === 'staff' || th.id === 'director' ? '#10203f' : '#fff') + ';">Accent Badge</div>' +
        '</div>' +
      '</div>';
  };

  const h = '<div class="mbx os-theme-dialog" role="dialog">' +
    '<div class="mt"><span style="display:flex;align-items:center;gap:6px;">' + ICON.palette + 'Display Properties &middot; Workstation Themes</span></div>' +
    '<div class="mb" style="padding:12px 16px;">' +
      '<div class="os-theme-preview-container">' +
        '<div class="os-sidebar-label" style="margin-bottom:4px;">Live Appearance Preview:</div>' +
        '<div id="theme-preview-box" class="os-theme-preview-box"></div>' +
      '</div>' +
      '<div class="os-sidebar-label" style="margin:8px 0 4px;">Available Theme Schemes:</div>' +
      '<div class="os-theme-listbox" id="theme-listbox">' +
        THEMES.map(getThemeItem).join("") +
      '</div>' +
      '<div class="os-sidebar-label" style="margin:10px 0 4px;">Window Style:</div>' +
      '<div class="os-skin-group" id="skin-group">' +
        '<label class="os-skin-opt"><input type="radio" name="skin" value="classic"' + (curSkin === "classic" ? ' checked' : '') + '><span><b>Classic Workstation</b><small>Bevelled faces and sunken wells, as on the Log On screen.</small></span></label>' +
        '<label class="os-skin-opt"><input type="radio" name="skin" value="aero"' + (curSkin === "aero" ? ' checked' : '') + '><span><b>Aero Glass</b><small>The earlier look: glossy title bars and ERP ribbon toolbars.</small></span></label>' +
      '</div>' +
    '</div>' +
    '<div class="mf" style="display:flex;justify-content:space-between;align-items:center;padding:8px 16px 12px;">' +
      '<button class="os-90s-btn" type="button" id="th-reset">Auto (Role)</button>' +
      '<div style="display:flex;gap:8px;">' +
        '<button class="os-90s-btn primary" type="button" id="th-ok">Apply &amp; Save</button>' +
        '<button class="os-90s-btn" type="button" id="th-cancel">Cancel</button>' +
      '</div>' +
    '</div>' +
  '</div>';

  m.innerHTML = h;
  m.hidden = false;
  updatePreview();

  const bindRows = () => {
    m.querySelectorAll(".os-theme-row").forEach(row => {
      row.onclick = () => {
        Sound.click();
        curPick = row.dataset.tid;
        m.querySelectorAll(".os-theme-row").forEach(r => r.classList.toggle("active", r.dataset.tid === curPick));
        updatePreview();
      };
    });
  };
  bindRows();

  $("#th-reset").onclick = () => {
    Sound.click();
    curPick = "auto";
    m.querySelectorAll(".os-theme-row").forEach(r => r.classList.toggle("active", r.dataset.tid === "auto"));
    updatePreview();
  };

  m.querySelectorAll('input[name="skin"]').forEach(r => {
    r.onchange = () => { Sound.click(); curSkin = r.value; };
  });

  $("#th-ok").onclick = () => {
    Sound.boot();
    applyTheme(curPick);
    applySkin(curSkin);
    m.hidden = true;
    if (document.body.dataset.phase === "desk") {
      drawTask();
      drawStart();
    } else if (document.body.dataset.phase === "login") {
      drawLogin($("#lbox") ? $("#lbox").value : "");
    }
  };

  $("#th-cancel").onclick = () => {
    Sound.click();
    m.hidden = true;
  };
}

/* ----------------------------------------------------------------- dialogs ---- */
function modal(title, html, ok) {
  Sound.ding();
  const m = $("#modal");
  m.innerHTML = '<div class="mbx" role="dialog"><div class="mt">' + esc(title) + '</div><div class="mb">' + html + '</div><div class="mf"><button class="btn" type="button" id="mok">' + esc(ok || "OK") + '</button></div></div>';
  m.hidden = false;
  $("#mok").onclick = () => { Sound.click(); m.hidden = true; };
  $("#mok").focus();
}
const POLICY = () => modal("ICS Cloud policy",
  "<p>Files in ICS Cloud are kept in ICS Cloud only. They cannot be saved, downloaded, copied or printed to this device.</p>" +
  "<p>This is so that every employee reads the current version.</p>", "Understood");

function menu(x, y, items) {
  closeMenu();
  const c = document.createElement("div");
  c.id = "ctx";
  c.innerHTML = items.map((it, i) => it === "-" ? "<hr>" :
    '<button type="button" data-i="' + i + '"' + (it.off ? ' disabled title="Disabled by ICS Cloud policy"' : "") + ">" + esc(it.t) + "</button>").join("");
  document.body.appendChild(c);
  c.style.left = Math.min(x, innerWidth - c.offsetWidth - 6) + "px";
  c.style.top = Math.min(y, innerHeight - c.offsetHeight - 6) + "px";
  c.onclick = e => { const b = e.target.closest("button[data-i]"); if (b && !b.disabled) { const f = items[+b.dataset.i].f; closeMenu(); f(); } };
}
function closeMenu() { const c = $("#ctx"); if (c) c.remove(); }

/* ------------------------------------------------------------------- boot ---- */
let bootTimer = 0;
function boot() {
  document.body.dataset.phase = "boot";
  $("#boot").innerHTML = MARK + "<h1>ICS</h1><div class='ver'>" + esc(OSN.name) + " &middot; version " + esc(OSN.version) + "</div>" +
    "<div class='bar'><i id='bbar'></i></div><div class='st' id='bst'></div><div class='tag'>Because You're Worth the Investment</div>";
  const steps = [[6, "Starting " + OSN.name + " " + OSN.version], [24, "Reading badge"], [46, "Connecting to ICS Cloud"],
    [68, "Starting the CCN relay"], [88, "Preparing your desktop"], [100, "Ready"]];
  let i = 0;
  const tick = () => {
    const s = steps[i++];
    $("#bbar").style.width = s[0] + "%"; $("#bst").textContent = s[1];
    bootTimer = setTimeout(i < steps.length ? tick : toLogin, i < steps.length ? 650 : 800);
  };
  tick();
  const skip = () => { if (document.body.dataset.phase === "boot") toLogin(); };
  setTimeout(() => { $("#boot").onclick = skip; document.addEventListener("keydown", skip, {once: true}); }, 900);
}
function toLogin() {
  clearTimeout(bootTimer);
  Sound.boot();
  if (S.role) { startDesk(); return; }
  document.body.dataset.phase = "login"; drawLogin(S.box);
}

/* ---------------------------------------------------------------- sign-in ---- */
let pick = S.role || "staff";
function mailSelect(role, current, id) {
  const c = {};
  seenBy(role).forEach(m => m.box.forEach(b => { c[b] = (c[b] || 0) + 1; }));
  const ids = Object.keys(c).filter(b => PERSON[b]).sort((a, b) => PERSON[a].label.localeCompare(PERSON[b].label));
  const opt = b => '<option value="' + esc(b) + '"' + (b === current ? " selected" : "") + ">" + esc(PERSON[b].label) + " (" + c[b] + ")</option>";
  const offices = ids.filter(b => b.indexOf("grp:") === 0), people = ids.filter(b => b.indexOf("grp:") !== 0);
  return '<select id="' + id + '"><option value="">Whole role: every mailbox</option>' +
    (offices.length ? '<optgroup label="Offices">' + offices.map(opt).join("") + "</optgroup>" : "") +
    (people.length ? '<optgroup label="People and desks">' + people.map(opt).join("") + "</optgroup>" : "") + "</select>";
}

function drawLogin(keepBox) {
  document.documentElement.dataset.role = pick;
  const L = $("#login");
  const r = ROLE[pick];
  const now = new Date();
  const timeStr = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
  const dateStr = now.toLocaleDateString("en-US", {weekday: "long", year: "numeric", month: "long", day: "numeric"});

  const roleOptions = D.roles.map(x =>
    '<option value="' + x.id + '"' + (x.id === pick ? " selected" : "") + ">" + esc(x.label) + "</option>"
  ).join("");

  const userCards = D.roles.map(x => {
    const isSel = x.id === pick;
    const tierName = x.level === 0 ? "Tier 3 · Global Staff" : x.level === 1 ? "Tier 2 · PTKW Clearance" : x.level === 2 ? "Tier 1 · Director Office" : (x.id === "all" ? "Master Archive View" : "Board Clearance");
    return '<button type="button" class="os-role-item' + (isSel ? ' active' : '') + '" data-id="' + x.id + '">' +
      '<span class="os-role-item-icon">' + (AVATAR[x.id] || AVATAR.staff) + '</span>' +
      '<div class="os-role-item-meta">' +
        '<span class="os-role-item-title">' + esc(x.label) + '</span>' +
        '<span class="os-role-item-tier">' + esc(tierName) + '</span>' +
      '</div>' +
      '</button>';
  }).join("");

  const tierBadge = r.level === 0 ? "Global Access" : r.level === 1 ? "PTKW Clearance" : r.level === 2 ? "Director Clearance" : (pick === "all" ? "Master Archive" : "Board Access");

  let h = '<div class="os-login-container">' +
    '<div class="os-login-dialog">' +
      '<div class="os-login-titlebar">' +
        '<div class="os-tb-title">' +
          MARK + '<span>Log On to ICS Earth Branch Workstation</span>' +
        '</div>' +
        '<div class="os-tb-controls">' +
          '<button type="button" class="os-tb-btn" id="ltheme" title="Change workstation theme">' + ICON.palette + ' Theme</button>' +
          '<button type="button" class="os-tb-btn" id="lsound" title="Toggle audio">' + (Sound.muted ? ICON.mute : ICON.sound) + ' Sound: ' + (Sound.muted ? 'Off' : 'On') + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="os-login-body">' +
        '<div class="os-brand-banner">' +
          '<div class="os-brand-left">' +
            '<div class="os-corp-logo">' + MARK + '<span>ICS</span></div>' +
            '<div class="os-corp-title">Interplanetary Corporate Solutions &middot; Earth Branch</div>' +
            '<div class="os-corp-motto">"Because You\'re Worth the Investment"</div>' +
          '</div>' +
          '<div class="os-brand-right">' +
            '<div class="os-time-badge">' + timeStr + '</div>' +
            '<div class="os-date-badge">' + dateStr + '</div>' +
            '<div class="os-node-badge">Terminal 349-B &middot; Cycle 300</div>' +
          '</div>' +
        '</div>' +
        '<div class="os-form-columns">' +
          '<div class="os-roles-sidebar">' +
            '<div class="os-sidebar-label">Select Account Clearance:</div>' +
            '<div class="os-roles-listbox">' + userCards + '</div>' +
          '</div>' +
          '<div class="os-form-main">' +
            '<fieldset class="os-retro-group">' +
              '<legend class="os-retro-legend">Active User Profile</legend>' +
              '<div class="os-user-hero">' +
                '<div class="os-hero-avatar">' + (AVATAR[pick] || AVATAR.staff) + '</div>' +
                '<div class="os-hero-info">' +
                  '<div class="os-hero-header">' +
                    '<h3 class="os-hero-name">' + esc(r.label) + '</h3>' +
                    '<span class="os-hero-badge">' + esc(tierBadge) + '</span>' +
                  '</div>' +
                  '<p class="os-hero-blurb">' + esc(r.blurb) + '</p>' +
                '</div>' +
              '</div>' +
            '</fieldset>' +
            '<fieldset class="os-retro-group">' +
              '<legend class="os-retro-legend">Credentials &amp; Routing</legend>' +
              '<div class="os-fields-group">' +
                '<div class="os-field-row">' +
                  '<label for="lrole-sel">Account Role:</label>' +
                  '<div class="os-input-wrap">' +
                    '<select id="lrole-sel" class="os-retro-select">' + roleOptions + '</select>' +
                  '</div>' +
                '</div>' +
                '<div class="os-field-row">' +
                  '<label for="lpass">Badge Token:</label>' +
                  '<div class="os-input-wrap os-pass-wrap">' +
                    '<input type="password" id="lpass" value="••••••••" readonly class="os-retro-input">' +
                    '<span class="os-badge-verified-tag">&#x2714; Verified Token</span>' +
                  '</div>' +
                '</div>' +
                '<div class="os-field-row">' +
                  '<label for="lbox">Mailbox Filter:</label>' +
                  '<div class="os-input-wrap">' +
                    '<span id="lboxw" class="os-field-val"></span>' +
                  '</div>' +
                '</div>' +
              '</div>' +
            '</fieldset>' +
            '<div class="os-clearance-status">' +
              '<span class="os-status-led"></span> ' +
              '<span class="os-status-text">Security Check: <b>PASSED</b> &middot; <b>' + docsFor(pick).length + '</b> Documents Cleared &middot; <b>' + seenBy(pick).length + '</b> Comms Channels</span>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="os-login-actions">' +
        '<div class="os-actions-left"><span class="os-sys-info">' + esc(OSN.name) + ' ' + esc(OSN.version) + ' &middot; Earth Branch Node #349 &middot; CCN Relay: ACTIVE</span></div>' +
        '<div class="os-actions-right">' +
          '<button type="button" class="os-90s-btn primary" id="gobtn">Log On &rarr;</button>' +
          '<button type="button" class="os-90s-btn" id="lpower">Restart</button>' +
        '</div>' +
      '</div>' +
    '</div>' +
  '</div>';

  L.innerHTML = h;
  $("#lboxw").innerHTML = mailSelect(pick, keepBox || "", "lbox");
  const sel = $("#lbox");
  if (sel) sel.className = "os-retro-select";

  L.querySelectorAll(".os-role-item").forEach(b => {
    b.onclick = () => {
      Sound.click();
      pick = b.dataset.id;
      drawLogin($("#lbox") ? $("#lbox").value : "");
    };
  });
  $("#lrole-sel").onchange = e => {
    Sound.click();
    pick = e.target.value;
    drawLogin($("#lbox") ? $("#lbox").value : "");
  };
  $("#gobtn").onclick = () => { Sound.click(); signIn(pick, $("#lbox").value); };
  $("#lpass").onkeydown = e => { if (e.key === "Enter") { Sound.click(); signIn(pick, $("#lbox").value); } };
  $("#ltheme").onclick = () => { openThemeDialog(); };
  $("#lsound").onclick = () => { Sound.toggle(); drawLogin($("#lbox") ? $("#lbox").value : ""); };
  $("#lpower").onclick = () => { Sound.boot(); boot(); };
}

function signIn(role, box) {
  S.role = role; S.box = box || ""; M.box = S.box; M.folder = "all"; M.series = ""; M.tier = ""; M.cyc = ""; M.q = ""; M.wn = false; M.sel = "";
  save(); Sound.boot(); startDesk();
}
function signOut() {
  Sound.close();
  WINS.slice().forEach(closeWin);
  S.role = ""; save();
  $("#start").hidden = true;
  document.body.dataset.phase = "login"; drawLogin(S.box);
}

/* --------------------------------------------------------------- desktop ---- */
const APPS = {
  mail: {title: OSN.mail, icon: ICON.mail, w: 1120, h: 700, single: true, mount: mailMount},
  drive: {title: OSN.cloud, icon: ICON.drive, w: 900, h: 560, single: true, mount: driveMount},
  folio: {title: OSN.docs, icon: ICON.doc, w: 900, h: 700, single: false, mount: folioMount},
  timeline: {title: "Timeline", icon: ICON.timeline, w: 980, h: 620, single: true, mount: timelineMount}
};
function startDesk() {
  document.body.dataset.phase = "desk";
  document.documentElement.dataset.role = S.role;
  $("#wall").innerHTML = MARK + '<div class="tg">Because You\'re Worth the Investment</div><div class="dev">ICS Earth Branch &middot; Personal device &middot; ' + esc(OSN.name) + " " + esc(OSN.version) + "</div>";
  $("#icons").innerHTML = ["mail", "drive", "folio", "timeline"].map(k =>
    '<button type="button" class="ic" data-app="' + k + '">' + APPS[k].icon + esc(APPS[k].title) + "</button>").join("");
  $("#icons").querySelectorAll(".ic").forEach(b => {
    b.onclick = () => {
      Sound.click();
      $("#icons").querySelectorAll(".ic").forEach(x => x.classList.remove("sel"));
      b.classList.add("sel");
      openApp(b.dataset.app);
    };
    b.ondblclick = () => openApp(b.dataset.app);
    b.onkeydown = e => { if (e.key === "Enter") openApp(b.dataset.app); };
  });
  drawTask(); drawStart();
}
function drawTask() {
  const r = ROLE[S.role];
  const dir = S.role === "director";
  const now = new Date();
  const timeStr = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
  const isFs = !!document.fullscreenElement;
  $("#task").innerHTML = '<button type="button" class="sbtn" id="sbtn">' + MARK + 'ICS</button>' +
    '<div class="task-search" id="tsearchbox">' + ICON.search + '<input type="text" id="tsearchinput" placeholder="Search (Ctrl+Space)" autocomplete="off"></div>' +
    '<div id="tbwins"></div>' +
    '<div class="tray">' + (dir ? '<span class="sync" id="ccnset" title="Copying to Office of the Branch Director. Set by: no record." style="cursor:default">CCN copy: on</span>' : "") +
    '<span class="sync tray-btn" id="themetoggle" title="Change Theme / Appearance">' + ICON.palette + ' Theme</span>' +
    '<span class="sync tray-btn" id="soundtoggle" title="Toggle audio sound effects">' + (Sound.muted ? ICON.mute : ICON.sound) + ' Sound: ' + (Sound.muted ? 'off' : 'on') + '</span>' +
    '<span class="sync tray-btn" id="fstoggle" title="Toggle Fullscreen / Kiosk Mode (F11)">' + (isFs ? ICON.compress : ICON.fullscreen) + (isFs ? ' Restore' : ' Fullscreen') + '</span>' +
    '<span class="sync" id="syncset" title="Everything on this device is in ICS Cloud">' + ICON.cloud + ' ICS Cloud: synced</span>' +
    '<span class="acct">' + esc(r.label) + '</span><span class="clock" id="trayclock">' + timeStr + '</span></div>';
  $("#sbtn").onclick = e => { e.stopPropagation(); Sound.click(); const s = $("#start"); s.hidden = !s.hidden; $("#sbtn").classList.toggle("on", !s.hidden); };
  $("#themetoggle").onclick = () => { openThemeDialog(); };
  $("#soundtoggle").onclick = () => {
    Sound.toggle();
    drawTask();
  };
  $("#fstoggle").onclick = () => {
    Sound.click();
    toggleFullscreen();
  };
  const tsin = $("#tsearchinput");
  if (tsin) {
    tsin.onfocus = () => { openSearch(tsin.value); tsin.value = ""; };
    tsin.onclick = () => { openSearch(tsin.value); tsin.value = ""; };
  }
  $("#syncset").onclick = () => { Sound.click(); about(); };
  if (dir) $("#ccnset").onclick = () => modal("CCN copy", "<p>Copy of staff and PTKW mail to the Office of the Branch Director: <b>on</b>.</p><p>Set by: no record.</p><p>This setting is not managed from this account.</p>");
  tbRefresh();
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}
document.addEventListener("fullscreenchange", () => {
  const el = $("#fstoggle");
  if (el) {
    const isFs = !!document.fullscreenElement;
    el.innerHTML = (isFs ? ICON.compress : ICON.fullscreen) + (isFs ? ' Restore' : ' Fullscreen');
  }
});

function openSearch(q) {
  const gs = $("#gsearch");
  if (!gs) return;
  gs.hidden = false;
  gs.innerHTML = '<div class="gs-hd">' + ICON.search + '<input type="text" id="gsin" placeholder="Search messages, documents, people\u2026" autofocus></div><div class="gs-res" id="gsres"></div>';
  const inp = $("#gsin", gs), res = $("#gsres", gs);
  inp.value = q || "";
  inp.focus();

  const query = () => {
    const val = inp.value.trim().toLowerCase();
    if (!val) {
      res.innerHTML = '<div class="gs-empty">Type to search messages and documents across ICS-OS.</div>';
      return;
    }
    const ms = seenBy(S.role).filter(m =>
      m.code.toLowerCase().includes(val) ||
      m.subject.toLowerCase().includes(val) ||
      m.from.toLowerCase().includes(val) ||
      (m.body && plain(m.body).toLowerCase().includes(val))
    ).slice(0, 8);
    const ds = docsFor(S.role).filter(d =>
      d.no.toLowerCase().includes(val) ||
      d.title.toLowerCase().includes(val) ||
      d.folder.toLowerCase().includes(val) ||
      (d._t && d._t.includes(val))
    ).slice(0, 8);

    if (!ms.length && !ds.length) {
      res.innerHTML = '<div class="gs-empty">No results found for "' + esc(val) + '".</div>';
      return;
    }

    let h = "";
    ms.forEach(m => {
      h += '<div class="gs-item" data-type="mail" data-code="' + esc(m.code) + '">' +
        '<span class="gs-tag">Mail</span><span class="gs-title">' + esc(m.code + ' \u2014 ' + m.subject) + '</span>' +
        '<span class="gs-snip">' + esc(m.from) + '</span></div>';
    });
    ds.forEach(d => {
      h += '<div class="gs-item" data-type="doc" data-no="' + esc(d.no) + '">' +
        '<span class="gs-tag doc">Doc ' + esc(d.no) + '</span><span class="gs-title">' + esc(d.title) + '</span>' +
        '<span class="gs-snip">' + esc(d.folder) + '</span></div>';
    });
    res.innerHTML = h;

    res.querySelectorAll(".gs-item").forEach(it => {
      it.onclick = () => {
        Sound.click();
        gs.hidden = true;
        if (it.dataset.type === "mail") openApp("mail", it.dataset.code);
        else if (it.dataset.type === "doc") openDoc(it.dataset.no);
      };
    });
  };

  inp.oninput = query;
  inp.onkeydown = e => {
    if (e.key === "Escape") { gs.hidden = true; }
    else if (e.key === "Enter") {
      const first = res.querySelector(".gs-item");
      if (first) first.click();
    }
  };
  query();
}
setInterval(() => {
  const el = $("#trayclock");
  if (el) {
    const now = new Date();
    el.textContent = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
  }
}, 10000);

function drawStart() {
  const r = ROLE[S.role];
  $("#start").innerHTML = '<div class="hd">' + MARK + "<div><b>" + esc(r.label) + "</b><span>" + esc(OSN.name) + " " + esc(OSN.version) + "</span></div></div>" +
    ["mail", "drive", "folio", "timeline"].map(k => '<button type="button" data-app="' + k + '">' + APPS[k].icon + esc(APPS[k].title) + "</button>").join("") +
    '<hr><button type="button" id="st-theme">' + ICON.palette + 'Themes &amp; Appearance\u2026</button>' +
    '<button type="button" id="st-search">' + ICON.search + 'Global Search\u2026</button>' +
    '<button type="button" id="st-about">' + ICON.info + "About " + esc(OSN.name) + '</button><button type="button" id="st-out">' + ICON.out + "Sign out</button>";
  $("#start").querySelectorAll("button[data-app]").forEach(b => b.onclick = () => { $("#start").hidden = true; $("#sbtn").classList.remove("on"); openApp(b.dataset.app); });
  $("#st-theme").onclick = () => { Sound.click(); $("#start").hidden = true; $("#sbtn").classList.remove("on"); openThemeDialog(); };
  $("#st-search").onclick = () => { Sound.click(); $("#start").hidden = true; $("#sbtn").classList.remove("on"); openSearch(); };
  $("#st-about").onclick = () => { Sound.click(); $("#start").hidden = true; $("#sbtn").classList.remove("on"); about(); };
  $("#st-out").onclick = signOut;
}
function about() {
  modal("About " + OSN.name,
    "<table><tr><td>System</td><td>" + esc(OSN.name) + " version " + esc(OSN.version) + "</td></tr>" +
    "<tr><td>Signed in as</td><td>" + esc(ROLE[S.role].label) + "</td></tr>" +
    "<tr><td>Storage</td><td>ICS Cloud only. This device holds no files.</td></tr>" +
    "<tr><td>Last synced</td><td>" + esc(D.generated.replace("T", " ").slice(0, 16)) + "</td></tr>" +
    (author() ? "<tr><td>Scan</td><td>" + D.scan + "</td></tr>" : "") + "</table>");
}
document.addEventListener("pointerdown", e => {
  if (!e.target.closest("#start,#sbtn")) { const s = $("#start"); if (s && !s.hidden) { s.hidden = true; const b = $("#sbtn"); if (b) b.classList.remove("on"); } }
  if (!e.target.closest("#ctx")) closeMenu();
});

/* Delegated click sound for buttons, tabs, links */
document.addEventListener("click", e => {
  const target = e.target.closest("button, a.mref, a.dref, .rc, .ic, .item, th, tr.f, select, .os-user-tile");
  if (target && !target.closest("#soundtoggle, #lsound")) {
    Sound.click();
  }
});

/* -------------------------------------------------------- window manager ---- */
const WINS = [];
let zTop = 10, actWin = null, nextId = 1, cascade = 0;
const wsRect = () => $("#wins").getBoundingClientRect();

function openApp(app, arg) {
  Sound.open();
  const A = APPS[app];
  if (A.single) {
    const ex = WINS.find(w => w.app === app);
    if (ex) { restoreWin(ex); if (ex.api && ex.api.open) ex.api.open(arg); return ex; }
  }
  const ws = wsRect();
  const el = document.createElement("div");
  el.className = "win";
  const W = Math.min(A.w, ws.width - 24), H = Math.min(A.h, ws.height - 24);
  const x = Math.max(0, Math.min(ws.width - W, 30 + (cascade % 8) * 28)), y = Math.max(0, Math.min(ws.height - H, 14 + (cascade % 8) * 28));
  cascade++;
  Object.assign(el.style, {left: x + "px", top: y + "px", width: W + "px", height: H + "px"});
  el.innerHTML = '<div class="tb">' + A.icon + '<span class="tt"></span><button type="button" class="wb mn" title="Minimise">&#8211;</button>' +
    '<button type="button" class="wb mx" title="Maximise">&#9633;</button><button type="button" class="wb x" title="Close">&#10005;</button></div>' +
    '<div class="wbody"></div><div class="rs"></div>';
  $("#wins").appendChild(el);
  const w = {id: nextId++, app, el, body: $(".wbody", el), api: null,
    setTitle: t => { $(".tt", el).textContent = t; w.title = t; tbRefresh(); }};
  w.title = A.title; $(".tt", el).textContent = A.title;
  WINS.push(w);
  $(".mn", el).onclick = () => minWin(w);
  $(".mx", el).onclick = () => maxWin(w);
  $(".x", el).onclick = () => closeWin(w);
  el.addEventListener("pointerdown", () => focusWin(w), true);
  $(".tb", el).addEventListener("pointerdown", e => dragStart(w, e));
  $(".tb", el).addEventListener("dblclick", e => { if (!e.target.closest(".wb")) maxWin(w); });
  $(".rs", el).addEventListener("pointerdown", e => resizeStart(w, e));
  w.api = A.mount(w, arg) || {};
  focusWin(w);
  return w;
}
function focusWin(w) {
  if (w.el.classList.contains("min")) w.el.classList.remove("min");
  actWin = w; w.el.style.zIndex = ++zTop;
  WINS.forEach(x => x.el.classList.toggle("act", x === w));
  tbRefresh();
}
function restoreWin(w) { Sound.max(); w.el.classList.remove("min"); focusWin(w); }
function nextWin() { return WINS.filter(x => !x.el.classList.contains("min")).sort((a, b) => b.el.style.zIndex - a.el.style.zIndex)[0]; }
function minWin(w) {
  Sound.min();
  w.el.classList.add("min");
  if (actWin === w) { actWin = null; const nx = nextWin(); if (nx) focusWin(nx); }
  WINS.forEach(x => x.el.classList.toggle("act", x === actWin));
  tbRefresh();
}
function maxWin(w) { Sound.max(); w.el.classList.toggle("max"); focusWin(w); }
function closeWin(w) {
  Sound.close();
  const i = WINS.indexOf(w); if (i >= 0) WINS.splice(i, 1);
  w.el.remove();
  if (w.app === "mail") mailW = null;
  if (actWin === w) { actWin = null; const nx = nextWin(); if (nx) focusWin(nx); }
  tbRefresh();
}
function tbRefresh() {
  const t = $("#tbwins"); if (!t) return;
  t.innerHTML = "";
  WINS.forEach(w => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "tbb" + (w === actWin && !w.el.classList.contains("min") ? " on" : "") + (w.el.classList.contains("min") ? " min" : "");
    b.textContent = w.title; b.title = w.title;
    b.onclick = () => { if (w.el.classList.contains("min")) restoreWin(w); else if (w === actWin) minWin(w); else focusWin(w); };
    t.appendChild(b);
  });
}
function dragStart(w, e) {
  if (e.button !== 0 || e.target.closest(".wb") || w.el.classList.contains("max")) return;
  const r = w.el.getBoundingClientRect(), ws = wsRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
  const guide = $("#snap-guide");
  let snapMode = null;
  const mv = ev => {
    w.el.style.left = Math.max(-r.width + 90, Math.min(ws.width - 90, ev.clientX - dx - ws.left)) + "px";
    w.el.style.top = Math.max(0, Math.min(ws.height - 32, ev.clientY - dy - ws.top)) + "px";

    if (ev.clientY <= 8) {
      snapMode = "top";
      if (guide) { guide.className = "snap-top"; guide.hidden = false; }
    } else if (ev.clientX <= 8) {
      snapMode = "left";
      if (guide) { guide.className = "snap-left"; guide.hidden = false; }
    } else if (ev.clientX >= ws.width - 8) {
      snapMode = "right";
      if (guide) { guide.className = "snap-right"; guide.hidden = false; }
    } else {
      snapMode = null;
      if (guide) guide.hidden = true;
    }
  };
  const up = () => {
    removeEventListener("pointermove", mv);
    removeEventListener("pointerup", up);
    if (guide) guide.hidden = true;

    if (snapMode === "top") {
      maxWin(w);
    } else if (snapMode === "left") {
      w.el.classList.remove("max");
      w.el.style.left = "4px";
      w.el.style.top = "4px";
      w.el.style.width = Math.round(ws.width / 2 - 6) + "px";
      w.el.style.height = (ws.height - 8) + "px";
      focusWin(w);
      Sound.max();
    } else if (snapMode === "right") {
      w.el.classList.remove("max");
      w.el.style.left = Math.round(ws.width / 2 + 2) + "px";
      w.el.style.top = "4px";
      w.el.style.width = Math.round(ws.width / 2 - 6) + "px";
      w.el.style.height = (ws.height - 8) + "px";
      focusWin(w);
      Sound.max();
    }
  };
  addEventListener("pointermove", mv); addEventListener("pointerup", up);
  e.preventDefault();
}
function resizeStart(w, e) {
  if (e.button !== 0) return;
  const r = w.el.getBoundingClientRect(), ws = wsRect(), sx = e.clientX, sy = e.clientY;
  const mv = ev => {
    w.el.style.width = Math.max(340, Math.min(ws.right - r.left, r.width + ev.clientX - sx)) + "px";
    w.el.style.height = Math.max(240, Math.min(ws.bottom - r.top, r.height + ev.clientY - sy)) + "px";
  };
  const up = () => { removeEventListener("pointermove", mv); removeEventListener("pointerup", up); };
  addEventListener("pointermove", mv); addEventListener("pointerup", up);
  e.preventDefault();
}
addEventListener("resize", () => {
  const ws = wsRect();
  WINS.forEach(w => {
    if (w.el.classList.contains("max")) return;
    const r = w.el.getBoundingClientRect();
    w.el.style.width = Math.min(r.width, ws.width) + "px"; w.el.style.height = Math.min(r.height, ws.height) + "px";
    w.el.style.left = Math.max(0, Math.min(ws.width - Math.min(r.width, ws.width), r.left - ws.left)) + "px";
    w.el.style.top = Math.max(0, Math.min(ws.height - Math.min(r.height, ws.height), r.top - ws.top)) + "px";
  });
});

/* Cloud-only: no save, no print, no copying out of a file. The author's view (All files) is exempt from copy. */
document.addEventListener("keydown", e => {
  if (document.body.dataset.phase !== "desk") return;
  if (e.key === "Escape") { closeMenu(); $("#modal").hidden = true; }
  if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S" || e.key === "p" || e.key === "P")) { e.preventDefault(); POLICY(); }
});
const inPage = n => { const el = n && (n.nodeType === 3 ? n.parentElement : n); return !!(el && el.closest && el.closest(".pg")); };
["copy", "cut", "dragstart"].forEach(t => document.addEventListener(t, e => { if (!author() && inPage(e.target)) e.preventDefault(); }));
document.addEventListener("contextmenu", e => {
  if (e.target.closest("input,select,textarea")) return;
  e.preventDefault();
  if (e.target.closest(".pg") && !author()) {
    menu(e.clientX, e.clientY, [{t: "Copy", off: true, f() {}}, {t: "Save as\u2026", off: true, f() {}}, {t: "Print\u2026", off: true, f() {}}]);
    return;
  }
  if (document.body.dataset.phase === "desk" && e.target.closest("#wall,#desk,#icons") && !e.target.closest(".win,#task,#start,#modal,#gsearch")) {
    menu(e.clientX, e.clientY, [
      {t: "Themes & Appearance\u2026", f() { openThemeDialog(); }},
      {t: "Global Search\u2026 (Ctrl+Space)", f() { openSearch(); }},
      "-",
      {t: "About " + OSN.name + "\u2026", f() { about(); }},
      {t: "Sign Out", f() { signOut(); }}
    ]);
  }
});

/* ------------------------------------------------------------------ Hearth ---- */
const FOLDERS = [["all", "All messages", "#C9A84C"], ["retained", "Retained copies", "#8a8a8a"], ["delivered", "Delivered", "#3f6b4f"],
  ["drafts", "Drafts and unsent", "#2f4f9a"], ["held", "Held by CCN", "#9a4a2b"], ["sealed", "Sealed", "#1A2E52"], ["notes", "Found notes", "#7a7468"]];
const TIERS = ["Open", "Design Team", "PTKW", "Branch Director", "Above Branch Director", "Sealed", "Board"];
const M = {box: S.box, folder: "all", series: "", tier: "", cyc: "", q: "", sort: "story", wn: false, sel: ""};
let mailW = null;
const who = raw => String(raw || "").replace(/\s*\(.*$/, "").replace(/^\[|\]$/g, "").trim() || "Unknown";
const retained = m => S.role === "director" && !!m.mirror;
const mCan = m => m.roles.includes(S.role);
const mBase = () => seenBy(S.role).filter(m => !M.box || m.box.includes(M.box));
function mPasses(m) {
  return mCan(m) && (!M.box || m.box.includes(M.box)) &&
    (M.folder === "all" || (M.folder === "retained" ? retained(m) : m.folder === M.folder)) &&
    (!M.series || m.series === M.series) && (!M.tier || m.tier === M.tier) && (!M.cyc || String(m.sort[0]) === M.cyc);
}
function mVisible() {
  const q = M.q.trim().toLowerCase();
  const r = mBase().filter(m => mPasses(m) && (!q || (m.code + " " + m.subject + " " + m.from + " " + m.to + " " + m.txt).toLowerCase().includes(q)));
  r.sort((a, b) => {
    if (M.sort === "code") return a.code < b.code ? -1 : 1;
    for (let i = 0; i < 4; i++) { if (a.sort[i] !== b.sort[i]) return a.sort[i] < b.sort[i] ? -1 : 1; }
    return 0;
  });
  return r;
}
function mailMount(w) {
  mailW = w; w.setTitle(OSN.mail);
  w.body.innerHTML = '<div class="hm" id="hm"><div class="hm-bar">' + MARK + "<b>" + esc(OSN.mail) + '</b><span class="tgl">ICS Earth Branch &middot; Internal Messaging</span><span class="sp"></span>' +
    '<input id="hq" type="search" placeholder="Search your mail" autocomplete="off">' +
    '<label id="hwn" style="display:none"><input type="checkbox" id="hwnc"> Writer\'s notes</label>' +
    '<label id="har" style="display:none"><input type="checkbox" id="harc"> Auto-reload</label></div>' +
    '<div class="hm-main"><nav id="hnav"></nav><section class="list" id="hlist"></section><article id="hread"></article></div><div class="hm-stat" id="hstat"></div></div>';
  $("#hwn").style.display = $("#har").style.display = author() ? "" : "none";
  $("#hwnc").checked = M.wn; $("#harc").checked = !!S.ar;
  $("#hq").value = M.q;
  $("#hq").oninput = e => { M.q = e.target.value; drawList(); };
  $("#hwnc").onchange = e => { M.wn = e.target.checked; drawRead(); };
  $("#harc").onchange = e => { S.ar = e.target.checked; save(); };
  w.el.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") { if (e.key === "Escape") e.target.blur(); return; }
    if (e.key === "/") { e.preventDefault(); $("#hq").focus(); return; }
    if (e.key !== "j" && e.key !== "k") return;
    const r = mVisible(); if (!r.length) return;
    let i = r.findIndex(m => m.code === M.sel);
    i = e.key === "j" ? Math.min(r.length - 1, i + 1) : Math.max(0, i - 1);
    mSelect(r[i].code);
  });
  drawNav(); drawList(); drawRead();
  return {open: code => { if (code) mSelect(code); }};
}
function drawNav() {
  const n = $("#hnav"), b0 = mBase();
  n.innerHTML = "<h3>Mailbox</h3>" + mailSelect(S.role, M.box, "nbox") + "<h3>Folders</h3>";
  $("#nbox").onchange = e => { M.box = e.target.value; S.box = M.box; save(); M.folder = "all"; M.series = ""; M.tier = ""; M.cyc = ""; drawNav(); drawList(); drawRead(); };
  FOLDERS.forEach(([k, label, col]) => {
    if (k === "retained" && S.role !== "director") return;
    const c = k === "all" ? b0.length : k === "retained" ? b0.filter(retained).length : b0.filter(m => m.folder === k).length;
    if (!c && k !== "all") return;
    const b = document.createElement("button");
    b.className = M.folder === k ? "on" : "";
    b.innerHTML = '<span class="dot" style="background:' + col + '"></span>' + esc(label) + '<span class="n">' + c + "</span>";
    b.onclick = () => { M.folder = k; drawNav(); drawList(); };
    n.appendChild(b);
  });
  n.insertAdjacentHTML("beforeend", "<h3>Channels</h3>");
  [["", "Every channel"]].concat(Object.entries(D.series)).forEach(([k, label]) => {
    const c = k ? b0.filter(m => m.series === k).length : b0.length;
    if (k && !c) return;
    const b = document.createElement("button");
    b.className = M.series === k ? "on" : "";
    b.innerHTML = esc(label) + '<span class="n">' + c + "</span>";
    b.onclick = () => { M.series = k; drawNav(); drawList(); };
    n.appendChild(b);
  });
  if (author()) n.insertAdjacentHTML("beforeend", '<div class="foot">Built from the files in the writing folder.<br>Scan ' + D.scan + "<br>" + esc(D.generated.replace("T", " ").slice(0, 16)) + "</div>");
}
function chips(m) {
  let h = '<span class="chip c-code">' + esc(m.code) + "</span>";
  if (m.folder === "drafts") h += '<span class="chip c-draft">Draft</span>';
  if (m.folder === "held") h += '<span class="chip c-held">CCN held</span>';
  if (m.folder === "sealed") h += '<span class="chip c-sealed">Sealed</span>';
  if (m.folder === "notes") h += '<span class="chip c-note">Found note</span>';
  if (m.tier !== "Open" && m.folder !== "sealed") h += '<span class="chip c-tier">' + esc(m.tier) + "</span>";
  if (retained(m)) h += '<span class="chip c-ret"><s>&#9680;</s>Retained copy</span>';
  if (m.proposal && author()) h += '<span class="chip c-prop">Proposal</span>';
  return h;
}
function drawList() {
  const r = mVisible(), b0 = mBase(), L = $("#hlist");
  if (!L) return;
  const tiers = TIERS.filter(t => b0.some(m => m.tier === t));
  const cycs = Array.from(new Set(b0.map(m => m.sort[0]))).sort((a, b) => a - b);
  L.innerHTML = '<div class="listbar"><span>' + r.length + " of " + b0.length + '</span><span class="sp"></span>Sort ' +
    '<select id="so"><option value="story">Story time</option><option value="code">Message code</option></select>' +
    '<span style="flex-basis:100%;height:0"></span>Clearance <select id="ft"><option value="">Any</option>' + tiers.map(t => "<option>" + esc(t) + "</option>").join("") + "</select>" +
    'Cycle <select id="fc"><option value="">Any</option>' + cycs.map(c => '<option value="' + c + '">' + (c === 99999 ? "Undated" : c) + "</option>").join("") + "</select></div>";
  $("#so").value = M.sort; $("#ft").value = M.tier; $("#fc").value = M.cyc;
  $("#so").onchange = e => { M.sort = e.target.value; drawList(); };
  $("#ft").onchange = e => { M.tier = e.target.value; drawList(); };
  $("#fc").onchange = e => { M.cyc = e.target.value; drawList(); };
  $("#hstat").innerHTML = S.role === "director"
    ? "<span>" + b0.filter(retained).length + " retained copies</span><span>Requested: 0</span><span>Acknowledged: 0</span>"
    : "<span>" + b0.length + " messages</span>" + (author() ? "<span>Scan " + D.scan + "</span>" : "");
  if (!r.length) { L.insertAdjacentHTML("beforeend", '<div class="empty">Nothing here.</div>'); return; }
  let undated = false;
  r.forEach(m => {
    if (M.sort === "story" && m.sort[0] === 99999 && !undated) { undated = true; L.insertAdjacentHTML("beforeend", '<div class="listbar" style="top:auto;position:static">Undated</div>'); }
    const d = document.createElement("div");
    d.className = "item" + (m.code === M.sel ? " on" : "") + (retained(m) ? " ret" : ""); d.dataset.code = m.code;
    d.innerHTML = '<div class="top"><span class="who">' + esc(who(m.from)) + '</span><span class="when">' + esc(m.ds + (m.clock ? " " + m.clock : "")) + "</span></div>" +
      '<div class="subj">' + esc(m.subject) + '</div><div class="pre">' + esc(m.preview) + '</div><div style="margin-top:5px">' + chips(m) + "</div>";
    d.onclick = () => mSelect(m.code);
    L.appendChild(d);
  });
}
function strip(m) {
  if (!m.status) return "";
  const cls = m.folder === "held" ? "held" : m.folder === "sealed" ? "sealed" : m.folder === "drafts" ? "draft" : "";
  return '<div class="strip ' + cls + '">' + esc(m.status.replace(/\*/g, "")) + "</div>";
}
function readHtml(m, back) {
  const mir = retained(m);
  let h = '<div class="wrap">' + (back ? '<button type="button" class="back" id="hback">&larr; Back to list</button>' : "") + '<div>' + chips(m) + '<span class="chip c-code" style="background:transparent">' + esc(D.series[m.series] || "") + "</span></div>" +
    "<h2>" + esc(m.subject) + "</h2>" +
    (mir ? '<div class="mirror"><div class="mtag">COPY</div><div><b>Retained copy. You were not an addressee.</b>The sender and the recipients were not told that this copy exists. It reached the Office of the Branch Director by CCN relay and was not requested.</div></div>' : "") +
    '<div class="hdr"><div><b>From</b><span>' + esc(m.from || "\u2014") + "</span></div>" +
    "<div><b>To</b><span>" + esc(m.to || "\u2014") + "</span></div>" +
    (m.cc ? "<div><b>Cc</b><span>" + esc(m.cc) + "</span></div>" : "") +
    "<div><b>Date</b><span>" + esc(m.date || "(undated)") + "</span></div>" +
    (mir ? '<div class="ret"><b>Route</b><span>Sender &rarr; CCN relay &rarr; addressees. Copy &rarr; Office of the Branch Director.</span></div>' +
      '<div class="ret"><b>This copy</b><span>Opened ' + m.mirror.views + (m.mirror.views === 1 ? " time" : " times") + " before today. Opened by: no record.</span></div>" : "") +
    m.details.map(d => "<div><b>" + esc(d[0]) + "</b><span>" + d[1] + "</span></div>").join("") + "</div>" +
    (mir ? '<span class="late">Your open was recorded.</span>' : "") +
    strip(m) + (m.banner.length ? '<p style="color:var(--muted);font-size:13px">' + m.banner.join("<br>") + "</p>" : "") +
    '<div class="mbody rich">' + m.body + "</div>";
  if (author() && M.wn) h += '<div class="writer"><h5>Writer\'s notes</h5>' + (m.meta || "<p>No notes.</p>") + "</div>";
  const rel = Array.from(new Set(m.out.concat(m.in))).filter(c => byCode[c] && mCan(byCode[c]));
  if (rel.length) h += '<div class="rel"><h5>Connected messages</h5>' + rel.map(c => '<a href="#" class="mref" title="' + esc(byCode[c].subject) + '">' + c + "</a>").join("") + "</div>";
  if (author()) h += '<div class="path">' + esc(m.path) + "</div>";
  return h + "</div>";
}
function drawRead() {
  const m = byCode[M.sel], A = $("#hread"), hm = $("#hm");
  if (!A) return;
  hm.classList.toggle("reading", !!m);
  if (!m) {
    A.innerHTML = '<div class="hello">' + MARK + "<h2>" + esc(OSN.mail) + "</h2><div>Because you're worth the investment.</div>" +
      '<p style="margin-top:22px;font-size:13px">Choose a message to read it. Use <b>j</b> and <b>k</b> to move, <b>/</b> to search.</p></div>';
    return;
  }
  if (!mCan(m)) {
    A.innerHTML = '<div class="denied"><div class="lock">' + esc(m.code) + "</div><h2>Outside your clearance</h2><div>This message is held at <b>" + esc(m.tier) +
      "</b> level. Your account is signed in as " + esc(ROLE[S.role].label) + ".</div></div>";
    return;
  }
  A.innerHTML = readHtml(m, true); A.scrollTop = 0;
  $("#hback").onclick = () => { M.sel = ""; drawList(); drawRead(); };
}
function mSelect(code) {
  const m = byCode[code]; if (!m) return;
  M.sel = code;
  if (mCan(m) && !mPasses(m)) { M.folder = "all"; M.series = ""; M.tier = ""; M.cyc = ""; M.box = ""; drawNav(); }
  drawList(); drawRead();
  const on = $(".item.on"); if (on) on.scrollIntoView({block: "nearest"});
}
setInterval(() => { if (S.ar && author() && document.body.dataset.phase === "desk") location.reload(); }, 8000);

/* ------------------------------------------------------------ cross links ---- */
document.addEventListener("click", e => {
  const a = e.target.closest("a.mref, a.dref");
  if (!a) return;
  e.preventDefault();
  if (a.classList.contains("dref")) { openDoc(a.dataset.doc); return; }
  const code = a.textContent.trim();
  if (!byCode[code] || !mCan(byCode[code])) { modal("Outside your clearance", "<p>Message " + esc(code) + " is not available to " + esc(ROLE[S.role].label) + ".</p>"); return; }
  const w = openApp("mail", code); if (w && w.api && w.api.open) w.api.open(code);
});
function openDoc(no) {
  const d = DOC[no];
  if (!d || !canDoc(d)) {
    modal("Outside your clearance", "<p>Document " + esc(no) + (d ? " is held at <b>" + esc(TIERLBL(d)) + "</b> level." : " is not in ICS Cloud.") +
      " Your account is signed in as " + esc(ROLE[S.role].label) + ".</p>");
    return;
  }
  const ex = WINS.find(w => w.app === "folio" && w.api && w.api.no === no);
  if (ex) { restoreWin(ex); return; }
  const blank = WINS.find(w => w.app === "folio" && w.api && !w.api.no);
  if (blank) { blank.api.open(no); restoreWin(blank); return; }
  openApp("folio", no);
}

/* ---------------------------------------------------------------- Timeline ---- */
/* [PROPOSAL] Story tracks from ICS-Writing/tools/timeline.json. Each entry is checked against
   the account's clearance: an entry the account cannot open at all shows as a withheld row.
   Mail opens in this window with Previous / Next along the track; the tree opens to the entries of a track. */
function timelineMount(w, id) {
  const T = D.timeline.tracks, B = w.body;
  const st = {id: (T.find(t => t.id === id) || T[0] || {}).id, open: {}, mode: "track", i: -1, code: "", q: ""};
  if (st.id) st.open[st.id] = true;
  w.setTitle("Timeline");
  const can = r => r.t === "m" ? !!byCode[r.id] && mCan(byCode[r.id]) : r.t === "d" ? !!DOC[r.id] && canDoc(DOC[r.id]) : author();
  const name = r => r.t === "m" ? byCode[r.id].subject : r.t === "d" ? DOC[r.id].title : r.title;
  const lab = r => r.t === "m" ? r.id : r.t === "d" ? "Doc " + r.id : "Scene " + r.id;
  const trk = () => T.find(t => t.id === st.id) || T[0];
  /* Every entry of a track, in order, with what this account may open. */
  const cache = {};
  const flat = tr => {
    if (cache[tr.id]) return cache[tr.id];
    const out = [];
    tr.groups.forEach(g => g.items.forEach(it => {
      const ok = it.refs.filter(can);
      if (!it.refs.length || it.refs.every(r => r.t === "s")) { if (!author()) return; out.push({h: g.h, it, ok, live: true}); }
      else out.push({h: g.h, it, ok, live: ok.length > 0});
    }));
    out.forEach((x, i) => { x.i = i; x.mail = x.ok.find(r => r.t === "m"); });
    return (cache[tr.id] = out);
  };
  const short = x => {
    if (!x.live) return "Access restricted";
    const r = x.ok.find(r => r.t !== "s") || x.ok[0];
    return r ? lab(r) + " \u00b7 " + name(r) : x.it.text;
  };
  const hay = x => x._h || (x._h = (x.h + " " + x.it.text + " " + x.ok.map(r => r.t === "m"
    ? r.id + " " + byCode[r.id].subject + " " + byCode[r.id].from + " " + byCode[r.id].txt
    : r.t === "d" ? "doc " + r.id + " " + DOC[r.id].title : "scene " + r.id + " " + r.title).join(" ")).toLowerCase());
  const seq = () => flat(trk()).filter(x => x.mail);
  const pos = () => seq().findIndex(x => x.i === st.i);
  const reading = () => st.mode === "read" && !st.q.trim();
  const terms = () => st.q.trim().toLowerCase().split(/\s+/).filter(Boolean);

  B.innerHTML = '<div class="dr tl"><div class="dr-bar"><b class="nm" id="tlname"></b><span class="tl-bl" id="tlbl"></span><span class="sp"></span>' +
    '<button type="button" id="tlback" hidden>\u2190 List</button><button type="button" id="tlprev" hidden>\u25C0 Previous</button><span class="tl-pos" id="tlpos" hidden></span><button type="button" id="tlnext" hidden>Next \u25B6</button>' +
    '<button type="button" id="tlall" title="Show every track with its entries">All tracks</button>' +
    '<input type="search" id="tlq" placeholder="Search the timeline" autocomplete="off"></div>' +
    '<div class="dr-main"><div class="dr-tree" id="tltree"></div><div class="tl-split" id="tlsplit" role="separator" aria-orientation="vertical" tabindex="0" title="Drag to resize the tracks menu. Double-click to reset."></div><div class="dr-files tl-list" id="tlpane"></div></div>' +
    '<div class="dr-stat" id="tlstat"></div></div>';
  const tree = $("#tltree", B), pane = $("#tlpane", B), qi = $("#tlq", B);
  /* Width of the tracks menu: drag the divider, use the arrow keys on it, or double-click to reset. Kept between sessions. */
  const main = $(".dr-main", B), split = $("#tlsplit", B), TLW = 250, TLMIN = 130;
  const tlMax = () => Math.max(TLMIN, Math.min(640, main.clientWidth - 260));
  const setW = (px, keep) => {
    const v = Math.round(Math.max(TLMIN, Math.min(tlMax(), px)));
    main.style.setProperty("--tlw", v + "px");
    split.setAttribute("aria-valuenow", v);
    if (keep) { S.tlw = v; save(); }
    return v;
  };
  setW(S.tlw || TLW);
  split.onpointerdown = e => {
    e.preventDefault(); split.setPointerCapture(e.pointerId); split.classList.add("drag");
    const x0 = e.clientX, w0 = tree.getBoundingClientRect().width;
    split.onpointermove = m => setW(w0 + m.clientX - x0);
    split.onpointerup = split.onpointercancel = u => {
      split.onpointermove = split.onpointerup = split.onpointercancel = null;
      split.classList.remove("drag"); try { split.releasePointerCapture(u.pointerId); } catch (_) {}
      setW(tree.getBoundingClientRect().width, true);
    };
  };
  split.ondblclick = () => setW(TLW, true);
  split.onkeydown = e => {
    const cur = tree.getBoundingClientRect().width, d = e.shiftKey ? 60 : 20;
    if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); setW(cur - d, true); }
    else if (e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); setW(cur + d, true); }
    else if (e.key === "Home") { e.preventDefault(); e.stopPropagation(); setW(TLMIN, true); }
    else if (e.key === "End") { e.preventDefault(); e.stopPropagation(); setW(tlMax(), true); }
  };
  if (window.ResizeObserver) new ResizeObserver(() => { const cur = parseInt(main.style.getPropertyValue("--tlw"), 10); if (cur > tlMax()) setW(tlMax()); }).observe(main);

  const row = (x, tid, showDay) => {
    if (!x.live) return '<div class="tl-it dim" data-tid="' + esc(tid) + '" data-i="' + x.i + '"><div class="tl-t"></div><div class="tl-b"><div class="tl-x"><b>Access restricted</b> \u00b7 withheld at ' + esc(ROLE[S.role].label) + " clearance</div></div></div>";
    return '<div class="tl-it" data-tid="' + esc(tid) + '" data-i="' + x.i + '"><div class="tl-t">' + esc(x.it.time || "") + '</div><div class="tl-b">' +
      (showDay ? '<div class="tl-sent">' + esc(x.h) + "</div>" : "") +
      (x.it.text ? '<div class="tl-x">' + esc(x.it.text) + (x.it.sent ? ' <span class="tl-sent">(' + esc(x.it.sent) + ")</span>" : "") + "</div>" : "") +
      x.it.refs.map(r => can(r)
        ? (r.t === "s" ? '<div class="tl-ref sc"><b>' + esc(lab(r)) + "</b> " + esc(name(r)) + "</div>"
          : '<a href="#" class="tl-ref" data-t="' + r.t + '" data-id="' + esc(r.id) + '"><b>' + esc(lab(r)) + "</b> " + esc(name(r)) + (!x.it.text && x.it.sent ? ' <span class="tl-sent">(' + esc(x.it.sent) + ")</span>" : "") + "</a>")
        : r.t === "s" ? "" : '<div class="tl-ref lock"><b>' + esc(lab(r)) + "</b> restricted</div>").join("") +
      "</div></div>";
  };

  const drawBar = () => {
    const tr = trk(), rd = reading(), q = !!st.q.trim(), p = rd ? pos() : -1, s = rd ? seq() : [];
    $("#tlname", B).textContent = q ? "Search" : st.mode === "all" ? "All tracks" : tr ? tr.label : "Timeline";
    $("#tlbl", B).textContent = q ? "" : st.mode === "all" ? "Every track and its entries" : tr ? tr.blurb : "";
    $("#tlback", B).hidden = !rd;
    $("#tlprev", B).hidden = $("#tlnext", B).hidden = $("#tlpos", B).hidden = !rd;
    $("#tlprev", B).disabled = p <= 0;
    $("#tlnext", B).disabled = p < 0 || p >= s.length - 1;
    $("#tlpos", B).textContent = p >= 0 ? "Message " + (p + 1) + " of " + s.length : "Not in this track";
    $("#tlall", B).classList.toggle("on", st.mode === "all" && !q);
  };
  const drawTree = () => {
    const top = tree.scrollTop;
    tree.innerHTML = "<h3>Tracks</h3>" + T.map(t => {
      const f = flat(t), op = !!st.open[t.id];
      let h = '<button type="button" class="tk' + (t.id === st.id && st.mode !== "all" ? " on" : "") + '" data-t="' + esc(t.id) + '" aria-expanded="' + op + '"><span class="car">' + (op ? "\u25BE" : "\u25B8") + "</span>" + esc(t.label) + "<span class='n'>" + f.length + "</span></button>";
      if (op) {
        let last = null;
        h += '<div class="tk-sub">' + f.map(x => {
          const g = x.h !== last ? '<div class="tk-g">' + esc(x.h) + "</div>" : ""; last = x.h;
          const cur = st.mode === "read" && t.id === st.id && x.i === st.i;
          return g + '<button type="button" class="ent' + (cur ? " on" : "") + (x.live ? "" : " dim") + '" data-tid="' + esc(t.id) + '" data-i="' + x.i + '" title="' + esc(short(x)) + '"><span class="t">' + esc(x.live ? x.it.time || "" : "") + '</span><span class="l">' + esc(short(x)) + "</span></button>";
        }).join("") + "</div>";
      }
      return h;
    }).join("");
    tree.scrollTop = top;
  };
  const drawPane = () => {
    const tr = trk(), ts = terms();
    pane.classList.toggle("tl-read", reading());
    if (ts.length) {
      const res = T.map(t => ({t, hits: flat(t).filter(x => x.live && ts.every(k => hay(x).includes(k)))})).filter(r => r.hits.length);
      pane.innerHTML = res.length ? res.map(r => '<h4 class="tl-h">' + esc(r.t.label) + " \u00b7 " + r.hits.length + "</h4>" + r.hits.map(x => row(x, r.t.id, true)).join("")).join("")
        : '<div class="empty">No entry matches \u201c' + esc(st.q.trim()) + "\u201d.</div>";
      pane.scrollTop = 0; return;
    }
    if (st.mode === "read") {
      const m = byCode[st.code];
      pane.innerHTML = m && mCan(m) ? readHtml(m, false) : '<div class="empty">Outside your clearance.</div>';
      pane.scrollTop = 0; return;
    }
    if (st.mode === "all") {
      pane.innerHTML = T.map(t => {
        const f = flat(t); let last = null;
        return '<h4 class="tl-h tl-trk">' + esc(t.label) + " <span>" + f.length + ' entries</span></h4><div class="tl-blq">' + esc(t.blurb) + "</div>" +
          f.map(x => {
            const g = x.h !== last ? '<div class="tl-ag">' + esc(x.h) + "</div>" : ""; last = x.h;
            return g + '<button type="button" class="tl-go' + (x.live ? "" : " dim") + '" data-tid="' + esc(t.id) + '" data-i="' + x.i + '"><span class="t">' + esc(x.live ? x.it.time || "" : "") + '</span><span class="l">' + esc(short(x)) + "</span></button>";
          }).join("");
      }).join("");
      return;
    }
    let last = null;
    const f = tr ? flat(tr) : [];
    pane.innerHTML = f.length ? f.map(x => {
      const hd = x.h !== last ? '<h4 class="tl-h">' + esc(x.h) + "</h4>" : ""; last = x.h;
      return hd + row(x, tr.id, false);
    }).join("") : '<div class="empty">Nothing on this track is open to this account.</div>';
  };
  const drawStat = () => {
    const tr = trk(), q = st.q.trim();
    $("#tlstat", B).innerHTML = "<span>" + (q ? pane.querySelectorAll(".tl-it").length + " matches" : st.mode === "all" ? T.reduce((n, t) => n + flat(t).length, 0) + " entries in " + T.length + " tracks" : (tr ? flat(tr).length : 0) + " entries") + '</span><span class="ok">Branch calendar: Day 0 is a Tuesday</span>';
  };
  const draw = () => { drawBar(); drawTree(); drawPane(); drawStat(); };
  const reveal = (tid, i) => {
    const el = pane.querySelector('.tl-it[data-tid="' + tid + '"][data-i="' + i + '"]');
    if (el) { el.scrollIntoView({block: "center"}); el.classList.add("hit"); }
  };
  const clearQ = () => { st.q = ""; qi.value = ""; };

  const readMail = (tid, i, code) => {
    clearQ(); st.id = tid; st.open[tid] = true; st.mode = "read"; st.code = code;
    const s = flat(T.find(t => t.id === tid)).filter(x => x.mail);
    const hit = i >= 0 ? s.find(x => x.i === i) : s.find(x => x.mail.id === code);
    st.i = hit ? hit.i : -1;
    draw();
    const on = tree.querySelector("button.ent.on"); if (on) on.scrollIntoView({block: "nearest"});
  };
  const openEntry = (tid, i) => {
    const x = flat(T.find(t => t.id === tid))[i]; if (!x) return;
    if (x.mail) { readMail(tid, i, x.mail.id); return; }
    clearQ(); st.id = tid; st.open[tid] = true; st.mode = "track"; st.i = i;
    draw(); reveal(tid, i);
    const d = x.ok.find(r => r.t === "d"); if (d) openDoc(d.id);
  };
  const step = d => {
    const s = seq(), p = pos(), n = p < 0 ? null : s[p + d];
    if (n) readMail(st.id, n.i, n.mail.id);
  };
  const back = () => { const i = st.i, tid = st.id; st.mode = "track"; draw(); if (i >= 0) reveal(tid, i); };

  tree.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.classList.contains("ent")) { openEntry(b.dataset.tid, +b.dataset.i); return; }
    const t = b.dataset.t, was = st.open[t] && st.id === t && st.mode !== "all";
    st.open[t] = !was; clearQ();
    if (!was) { st.id = t; st.mode = "track"; st.i = -1; }
    draw();
  };
  pane.onclick = e => {
    const go = e.target.closest("button.tl-go");
    if (go) { openEntry(go.dataset.tid, +go.dataset.i); return; }
    const a = e.target.closest("a.tl-ref");
    if (!a) return;
    e.preventDefault();
    if (a.dataset.t === "d") { openDoc(a.dataset.id); return; }
    const it = a.closest(".tl-it");
    readMail(it.dataset.tid, +it.dataset.i, a.dataset.id);
  };
  /* Connected messages inside the reader open in this window too. */
  B.addEventListener("click", e => {
    const a = e.target.closest("a.mref");
    if (!a || !pane.contains(a)) return;
    e.preventDefault(); e.stopPropagation(); Sound.click();
    const c = a.textContent.trim();
    if (!byCode[c] || !mCan(byCode[c])) { modal("Outside your clearance", "<p>Message " + esc(c) + " is not available to " + esc(ROLE[S.role].label) + ".</p>"); return; }
    readMail(st.id, -1, c);
  });
  $("#tlback", B).onclick = back;
  $("#tlprev", B).onclick = () => step(-1);
  $("#tlnext", B).onclick = () => step(1);
  $("#tlall", B).onclick = () => { clearQ(); st.mode = st.mode === "all" ? "track" : "all"; draw(); };
  qi.oninput = e => { st.q = e.target.value; drawBar(); drawPane(); drawStat(); };
  w.el.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") { if (e.key === "Escape") { clearQ(); drawBar(); drawPane(); drawStat(); e.target.blur(); } return; }
    if (e.key === "/") { e.preventDefault(); qi.focus(); return; }
    if (!reading()) return;
    if (e.key === "ArrowRight" || e.key === "j") step(1);
    else if (e.key === "ArrowLeft" || e.key === "k") step(-1);
    else if (e.key === "Escape") back();
  });
  draw();
  return {open: i => { if (T.some(t => t.id === i)) { clearQ(); st.id = i; st.open[i] = true; st.mode = "track"; draw(); } }};
}

/* ------------------------------------------------------- ICS Cloud Drive ---- */
function driveMount(w) {
  const st = {folder: "*", q: "", sort: "no", dir: 1, sel: ""};
  w.setTitle(OSN.cloud);
  const rows = () => {
    const q = st.q.trim().toLowerCase();
    let r = docsFor(S.role).filter(d => (st.folder === "*" || d.folder === st.folder));
    if (q) {
      r = docsFor(S.role).filter(d => {
        if (d._t === undefined) d._t = d.segs.filter(s => s.t <= level()).map(s => plain(s.h)).join(" ").toLowerCase();
        return (d.no + " " + d.title).toLowerCase().includes(q) || d._t.includes(q);
      });
    }
    const key = {no: d => d.no, tier: d => d.outside ? 9 : d.tier, mtime: d => d.mtime, size: d => d.size}[st.sort];
    r.sort((a, b) => (key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : a.no < b.no ? -1 : 1) * st.dir);
    return r;
  };
  const folders = () => D.folders.map(f => [f, docsFor(S.role).filter(d => d.folder === f).length]).filter(x => x[1]);
  const open = no => openDoc(no);
  const props = d => modal("Properties", "<table><tr><td>Name</td><td>" + esc(d.no + " \u2014 " + d.title) + "</td></tr>" +
    "<tr><td>Location</td><td>ICS Cloud \u203a " + esc(d.folder) + "</td></tr>" +
    "<tr><td>Clearance</td><td>" + esc(TIERLBL(d)) + "</td></tr>" +
    "<tr><td>Stored</td><td>ICS Cloud only. No copy on this device.</td></tr>" +
    "<tr><td>Last synced</td><td>" + esc(d.mtime) + "</td></tr>" +
    "<tr><td>Size</td><td>" + Math.max(1, Math.round(d.size / 1024)) + " KB</td></tr>" +
    (author() ? "<tr><td>Source file</td><td>" + esc(d.path) + "</td></tr>" : "") + "</table>");
  const fileMenu = (x, y, d) => menu(x, y, [{t: "Open", f: () => open(d.no)}, {t: "Properties", f: () => props(d)}, "-",
    {t: "Save a copy\u2026", off: true, f() {}}, {t: "Download", off: true, f() {}}, {t: "Copy to this device", off: true, f() {}}, {t: "Print\u2026", off: true, f() {}}]);
  const draw = () => {
    const r = rows(), fs = folders(), all = docsFor(S.role).length;
    const col = (k, label) => '<th data-k="' + k + '">' + label + (st.sort === k ? (st.dir > 0 ? " \u25B2" : " \u25BC") : "") + "</th>";
    w.body.innerHTML = '<div class="dr"><div class="dr-bar"><button type="button" id="dopen" ' + (st.sel ? "" : "disabled") + '>Open</button>' +
      '<div class="dr-path">ICS Cloud \u203a ' + esc(st.q ? "Search results" : st.folder === "*" ? "All documents" : st.folder) + '</div><input type="search" id="dq" placeholder="Search ICS Cloud" value="' + esc(st.q) + '">' +
      '<button type="button" id="dref" title="Reload from ICS Cloud">Refresh</button></div>' +
      '<div class="dr-main"><div class="dr-tree"><h3>ICS Cloud</h3><button type="button" data-f="*" class="' + (st.folder === "*" && !st.q ? "on" : "") + '">' + ICON.cloud + "All documents<span class='n'>" + all + "</span></button>" +
      fs.map(f => '<button type="button" class="sub ' + (st.folder === f[0] && !st.q ? "on" : "") + '" data-f="' + esc(f[0]) + '">' + ICON.folder + esc(f[0]) + "<span class='n'>" + f[1] + "</span></button>").join("") + "</div>" +
      '<div class="dr-files"><table><thead><tr>' + col("no", "Name") + col("tier", "Clearance") + col("mtime", "Last synced") + col("size", "Size") + "</tr></thead><tbody>" +
      r.map(d => '<tr class="f' + (d.no === st.sel ? " sel" : "") + '" data-no="' + d.no + '"><td class="nm">' + ICON.file + esc(d.no + " \u2014 " + d.title) + "</td><td>" + esc(TIERLBL(d)) + "</td><td>" + esc(d.mtime) + "</td><td>" + Math.max(1, Math.round(d.size / 1024)) + " KB</td></tr>").join("") +
      "</tbody></table>" + (r.length ? "" : '<div class="empty">Nothing here.</div>') + "</div></div>" +
      '<div class="dr-stat"><span>' + r.length + ' items</span><span class="ok">Stored in ICS Cloud only</span><span>Last synced ' + esc(D.generated.replace("T", " ").slice(0, 16)) + "</span></div></div>";
    const T = w.body;
    $("#dq", T).oninput = e => { st.q = e.target.value; const p = e.target.selectionStart; draw(); const q = $("#dq", T); q.focus(); q.setSelectionRange(p, p); };
    $("#dref", T).onclick = draw;
    $("#dopen", T).onclick = () => st.sel && open(st.sel);
    T.querySelectorAll(".dr-tree button").forEach(b => b.onclick = () => { st.folder = b.dataset.f; st.q = ""; st.sel = ""; draw(); });
    T.querySelectorAll("th").forEach(h => h.onclick = () => { if (st.sort === h.dataset.k) st.dir = -st.dir; else { st.sort = h.dataset.k; st.dir = 1; } draw(); });
    T.querySelectorAll("tr.f").forEach(tr => {
      tr.onclick = () => { st.sel = tr.dataset.no; T.querySelectorAll("tr.f").forEach(x => x.classList.toggle("sel", x === tr)); $("#dopen", T).disabled = false; };
      tr.ondblclick = () => open(tr.dataset.no);
      tr.oncontextmenu = e => { e.preventDefault(); e.stopPropagation(); tr.click(); fileMenu(e.clientX, e.clientY, DOC[tr.dataset.no]); };
    });
    $(".dr-files", T).oncontextmenu = e => {
      if (e.target.closest("tr.f")) return;
      e.preventDefault(); e.stopPropagation();
      menu(e.clientX, e.clientY, [{t: "Refresh from ICS Cloud", f: draw}, "-", {t: "Upload from this device\u2026", off: true, f() {}}]);
    };
  };
  w.el.addEventListener("keydown", e => { if (e.key === "Enter" && st.sel && e.target.tagName !== "INPUT") open(st.sel); });
  draw();
  return {};
}

/* ------------------------------------------------------------------- Folio ---- */
function folioMount(w, no) {
  const api = {no: ""};
  let hits = [], hi = -1, zoom = 1.0;
  const pick = () => {
    w.setTitle(OSN.docs);
    api.no = "";
    w.body.innerHTML = '<div class="fo"><div class="fo-bar"><b class="nm">' + esc(OSN.docs) + '</b><span class="cl">' + ICON.cloud + ' Connected to ICS Cloud</span></div>' +
      '<div class="fo-canvas"><div class="pg free" style="user-select:none"><h4 class="h2" style="margin-top:0">Open from ICS Cloud</h4><p>' + esc(OSN.docs) + ' opens files from ICS Cloud only. It cannot open or save files on this device.</p><ul>' +
      docsFor(S.role).map(d => '<li><a href="#" class="dref" data-doc="' + d.no + '">' + esc(d.no + " \u2014 " + d.title) + "</a></li>").join("") + "</ul></div></div></div>";
  };
  const show = n => {
    const d = DOC[n];
    api.no = n;
    w.setTitle(d.no + " \u2014 " + d.title + " \u2014 " + OSN.docs);
    const lv = level();
    const body = d.segs.map((sg, k) => {
      if (sg.t > lv) {
        const bars = Math.max(1, Math.min(9, Math.round(sg.n / 260)));
        let b = ""; for (let i = 0; i < bars; i++) b += '<i style="width:' + (52 + ((i * 37 + k * 11) % 46)) + '%"></i>';
        return '<div class="red"><div class="rh"><b>Access restricted</b> &middot; ' + esc(D.tiers[sg.t]) + " clearance required &middot; section withheld</div>" + b + "</div>";
      }
      return sg.t > 0 ? '<div class="layer l' + sg.t + '"><i>' + esc(D.tiers[sg.t]) + " layer</i>" + sg.h + "</div>" : sg.h;
    }).join("");
    w.body.innerHTML = '<div class="fo"><div class="fo-bar"><b class="nm">' + esc(d.no + " \u2014 " + d.title) + '</b><span class="sp"></span>' +
      '<span class="cl">' + ICON.cloud + " Synced to ICS Cloud " + esc(d.mtime) + "</span>" +
      '<div class="fo-zoom">' +
      '<button type="button" id="fzoomout" title="Zoom out">\u2212</button>' +
      '<button type="button" id="fzoomreset" title="Reset zoom (100%)">' + Math.round(zoom * 100) + '%</button>' +
      '<button type="button" id="fzoomin" title="Zoom in">+</button>' +
      '</div>' +
      '<button type="button" class="dis" id="fsave" title="Disabled by ICS Cloud policy">Save</button>' +
      '<button type="button" class="dis" id="fprn" title="Disabled by ICS Cloud policy">Print</button>' +
      '<input type="search" id="ffind" placeholder="Find in file"><span class="fc" id="fcnt"></span>' +
      '<button type="button" id="fprev" title="Previous">&uarr;</button><button type="button" id="fnext" title="Next">&darr;</button>' +
      '<button type="button" id="fopen">Open\u2026</button></div>' +
      '<div class="fo-main"><div class="fo-out" id="fout"></div><div class="fo-canvas" id="fcan"><div class="pg' + (author() ? " free" : "") + '" id="fpg"><div class="meta">' +
      '<span class="chip c-code">' + esc(d.no) + '</span><span class="chip c-tier">' + esc(TIERLBL(d)) + '</span><span class="chip c-tier">' + esc(d.folder) + "</span>" +
      '<span class="chip c-tier">Read only &middot; ICS Cloud</span></div><div class="rich">' + body + "</div>" +
      (author() && d.notes ? '<div class="writer"><h5>Writer\'s notes</h5>' + d.notes + "</div>" : "") +
      (author() ? '<div class="path">' + esc(d.path) + "</div>" : "") + "</div></div></div></div>";
    const T = w.body, pg = $("#fpg", T);
    const hs = Array.from(pg.querySelectorAll(".rich h4")).filter(h => !h.closest(".red"));
    $("#fout", T).innerHTML = "<h3>Outline</h3>" + (hs.length ? "" : '<div style="color:var(--muted);padding:3px 6px">No headings</div>');
    hs.forEach(h => {
      const a = document.createElement("a");
      a.textContent = h.textContent.replace(/^TERM:\s*/, "").slice(0, 70);
      a.className = h.classList.contains("h1") || h.classList.contains("h2") ? "" : h.classList.contains("h3") ? "l2" : "l3";
      a.onclick = () => h.scrollIntoView({block: "start"});
      $("#fout", T).appendChild(a);
    });
    const applyZoom = z => {
      zoom = Math.max(0.6, Math.min(2.5, Math.round(z * 100) / 100));
      if (pg) pg.style.zoom = zoom;
      const lbl = $("#fzoomreset", T);
      if (lbl) lbl.textContent = Math.round(zoom * 100) + "%";
    };
    if (zoom !== 1.0) applyZoom(zoom);
    $("#fzoomin", T).onclick = () => {
      Sound.click();
      const next = [0.75, 0.85, 1.0, 1.15, 1.25, 1.5, 1.75, 2.0].find(x => x > zoom + 0.01) || Math.min(2.5, zoom + 0.25);
      applyZoom(next);
    };
    $("#fzoomout", T).onclick = () => {
      Sound.click();
      const prev = [0.75, 0.85, 1.0, 1.15, 1.25, 1.5, 1.75, 2.0].reverse().find(x => x < zoom - 0.01) || Math.max(0.6, zoom - 0.25);
      applyZoom(prev);
    };
    $("#fzoomreset", T).onclick = () => {
      Sound.click();
      applyZoom(1.0);
    };
    $("#fcan", T).addEventListener("wheel", e => {
      if (e.ctrlKey) {
        e.preventDefault();
        applyZoom(zoom + (e.deltaY < 0 ? 0.1 : -0.1));
      }
    }, {passive: false});
    $("#fsave", T).onclick = POLICY; $("#fprn", T).onclick = POLICY;
    $("#fopen", T).onclick = pick;
    const find = () => {
      pg.querySelectorAll("mark").forEach(m => m.replaceWith(document.createTextNode(m.textContent))); pg.normalize();
      hits = []; hi = -1;
      const q = $("#ffind", T).value;
      if (q.length >= 2) {
        const tw = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT, {acceptNode: n => n.parentElement.closest(".red") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
        const nodes = []; while (tw.nextNode()) nodes.push(tw.currentNode);
        const ql = q.toLowerCase();
        for (const n of nodes) {
          const t = n.nodeValue, tl = t.toLowerCase(); let i = tl.indexOf(ql); if (i < 0 || hits.length >= 500) continue;
          const f = document.createDocumentFragment(); let last = 0;
          while (i >= 0 && hits.length < 500) {
            f.appendChild(document.createTextNode(t.slice(last, i)));
            const mk = document.createElement("mark"); mk.textContent = t.slice(i, i + q.length); f.appendChild(mk); hits.push(mk);
            last = i + q.length; i = tl.indexOf(ql, last);
          }
          f.appendChild(document.createTextNode(t.slice(last))); n.replaceWith(f);
        }
      }
      step(1);
    };
    const step = dir => {
      if (!hits.length) { $("#fcnt", T).textContent = $("#ffind", T).value.length >= 2 ? "0" : ""; return; }
      if (hi >= 0) hits[hi].classList.remove("cur");
      hi = (hi + dir + hits.length) % hits.length; if (hi < 0) hi = 0;
      hits[hi].classList.add("cur"); hits[hi].scrollIntoView({block: "center"});
      $("#fcnt", T).textContent = (hi + 1) + "/" + hits.length;
    };
    $("#ffind", T).oninput = find;
    $("#ffind", T).onkeydown = e => { if (e.key === "Enter") step(e.shiftKey ? -1 : 1); };
    $("#fnext", T).onclick = () => step(1); $("#fprev", T).onclick = () => step(-1);
  };
  api.open = n => { if (n && DOC[n] && canDoc(DOC[n])) show(n); };
  if (no) show(no); else pick();
  return api;
}

/* Global keyboard navigation & shortcuts */
document.addEventListener("keydown", e => {
  if ((e.ctrlKey && e.code === "Space") || (e.altKey && e.code === "Space") || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s")) {
    e.preventDefault();
    const gs = $("#gsearch");
    if (gs && !gs.hidden) { gs.hidden = true; } else { openSearch(); }
    return;
  }
  if (e.key === "Escape") {
    const gs = $("#gsearch"); if (gs && !gs.hidden) { gs.hidden = true; return; }
    const st = $("#start"); if (st && !st.hidden) { st.hidden = true; $("#sbtn").classList.remove("on"); return; }
    const mo = $("#modal"); if (mo && !mo.hidden) { mo.hidden = true; return; }
    closeMenu();
  }
});

/* PWA Service Worker Registration */
if (typeof window !== "undefined" && "serviceWorker" in navigator && location.protocol.startsWith("http")) {
  try {
    const swCode = "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());";
    const blob = new Blob([swCode], {type: "text/javascript"});
    navigator.serviceWorker.register(URL.createObjectURL(blob)).catch(() => {});
  } catch (_) {}
}

if (typeof window !== "undefined") {
  boot();
}
