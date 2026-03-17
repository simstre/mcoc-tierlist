let data = null;
let currentView = 'all';
let awClassView = 'all';
let sigClassView = 'all';
let selectedImms = new Set();
let immMode = 'immune'; // 'immune' or 'inflicts'
let prestigeKey = '';

const immColors = {
  // Immunities
  Bleed: '#ef4444', Poison: '#22c55e', Coldsnap: '#38bdf8', Shock: '#facc15',
  Incinerate: '#f97316', Nullify: '#a855f7', 'Armor Break': '#94a3b8',
  Stagger: '#a855f7', Frostbite: '#7dd3fc', 'Fate Seal': '#c084fc',
  // Extra debuff types
  'Heal Block': '#fb923c', 'Power Drain': '#60a5fa', 'Power Lock': '#818cf8',
  'Power Burn': '#c084fc', Stun: '#fbbf24', Degeneration: '#f472b6',
};

function buildImmToggles() {
  const container = document.getElementById('imm-toggles');
  const hint = document.getElementById('imm-hint');
  const types = immMode === 'immune' ? (data.immunity_types || []) : (data.debuff_types || []);

  hint.textContent = immMode === 'immune'
    ? 'Select immunities to find matching champions. Multiple = must have all.'
    : 'Select debuffs to find champions who inflict them. Multiple = must inflict all.';

  container.innerHTML = types.map(t => {
    const color = immColors[t] || '#888';
    const on = selectedImms.has(t) ? ' on' : '';
    return `<button class="imm-toggle${on}" style="--imm-color:${color}" data-imm="${t}">${t}</button>`;
  }).join('');

  container.querySelectorAll('.imm-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const imm = btn.dataset.imm;
      if (selectedImms.has(imm)) {
        selectedImms.delete(imm);
        btn.classList.remove('on');
      } else {
        selectedImms.add(imm);
        btn.classList.add('on');
      }
      renderImmunities();
    });
  });
}

async function init() {
  const res = await fetch('/data/tierlist.json');
  data = await res.json();

  const creators = data.sources.map(s => s.name).join(', ');
  document.getElementById('meta').innerHTML =
    `Based on ${creators}  \u00b7  Updated ${data.last_updated}`;

  // Source freshness
  const meta = data.source_meta || [];
  const sourceInfo = meta.map(s => {
    if (s.status === 'failed') return `<span style="color:#ef4444">${s.name}: failed</span>`;
    const edition = s.edition || 'unknown date';
    return `${s.name}: ${edition} (${s.champion_count})`;
  }).join('  \u00b7  ');

  document.getElementById('notes').innerHTML =
    `Scores 0\u2013100 from ${data.sources.length} YouTube creators. ${data.total_champions} champions.<br>` +
    `<span class="source-info">${sourceInfo}</span>`;

  // Build legends
  function legendItem(html, label) {
    return `<span class="legend-item">${html} ${label}</span>`;
  }
  function badgeLegend(key) {
    const b = TAG_BADGES[key];
    return legendItem(`<span class="tb" style="color:${b.color};background:${b.color}20">${b.label}</span>`, b.title);
  }

  const mainLegend =
    legendItem('<span class="aw"></span>', 'Awakening') +
    legendItem('<span class="no7">7</span>', 'No 7-Star') +
    Object.keys(TAG_BADGES).filter(k => k !== 'in_titan_crystal' && k !== 'meteor_tactic').map(badgeLegend).join('');
  document.getElementById('legend').innerHTML = mainLegend;

  const awLegendKeys = ['high_sig_needed', 'in_titan_crystal', 'defense'];
  document.getElementById('aw-legend').innerHTML = awLegendKeys.map(badgeLegend).join('');

  const sigLegendKeys = ['defense', 'high_sig_needed'];
  document.getElementById('sig-legend').innerHTML = sigLegendKeys.map(badgeLegend).join('');

  // Page tabs
  document.querySelectorAll('.ptab[data-page]').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.ptab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-' + tab.dataset.page).classList.add('active');
    });
  });

  // Class tabs
  document.querySelectorAll('#class-tabs .tab').forEach(tab => {
    tab.addEventListener('click', () => {
      currentView = tab.dataset.view;
      document.querySelectorAll('#class-tabs .tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      render();
    });
  });

  // Immunity/Debuff mode tabs
  document.querySelectorAll('.imm-mode').forEach(btn => {
    btn.addEventListener('click', () => {
      immMode = btn.dataset.mode;
      document.querySelectorAll('.imm-mode').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedImms.clear();
      buildImmToggles();
      renderImmunities();
    });
  });

  // Immunity/Debuff toggle buttons
  buildImmToggles();

  // Awakening gem class tabs
  const awClasses = ['all', 'Cosmic', 'Mutant', 'Tech', 'Skill', 'Science', 'Mystic'];
  const awTabs = document.getElementById('aw-class-tabs');
  awTabs.innerHTML = awClasses.map(c =>
    `<button class="tab${c === 'all' ? ' active' : ''}" data-view="${c}">${c === 'all' ? 'All' : c}</button>`
  ).join('');
  awTabs.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      awClassView = tab.dataset.view;
      awTabs.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderAwakening();
    });
  });

  // Sig stones class tabs
  const sigTabs = document.getElementById('sig-class-tabs');
  sigTabs.innerHTML = awClasses.map(c =>
    `<button class="tab${c === 'all' ? ' active' : ''}" data-view="${c}">${c === 'all' ? 'All' : c}</button>`
  ).join('');
  sigTabs.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      sigClassView = tab.dataset.view;
      sigTabs.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderSigStones();
    });
  });

  // Prestige controls
  const prestigeRankSel = document.getElementById('prestige-rank');
  prestigeRankSel.innerHTML = data.prestige_options.map(o =>
    `<option value="${o.key}">${o.label}</option>`
  ).join('');
  prestigeKey = data.prestige_options[0].key;
  prestigeRankSel.addEventListener('change', () => {
    prestigeKey = prestigeRankSel.value;
    renderPrestige();
  });

  document.getElementById('prestige-search').addEventListener('input', renderPrestige);

  document.getElementById('search').addEventListener('input', render);
  render();
  renderImmunities();
  renderAwakening();
  renderSigStones();
  renderPrestige();
}

function getFiltered() {
  const q = document.getElementById('search').value.toLowerCase();
  let list = data.champions;
  if (currentView !== 'all') {
    list = list.filter(c => c.class === currentView);
  }
  if (q) {
    list = list.filter(c => c.name.toLowerCase().includes(q));
  }
  return list;
}

function portraitHtml(c) {
  if (c.portrait) {
    return `<div class="champ-portrait"><img src="${c.portrait}" alt="" loading="lazy" onerror="this.parentElement.innerHTML='<span class=fb>${c.name[0]}</span>'"></div>`;
  }
  return `<div class="champ-portrait"><span class="fb">${c.name[0]}</span></div>`;
}

const TAG_BADGES = {
  defense: { label: 'D', color: '#22c55e', title: 'BGs Defense' },
  high_sig_needed: { label: '\u2B06', color: '#3b82f6', title: 'High Sig Needed' },
  relic: { label: 'R', color: '#f97316', title: 'Relic Important' },
  recoil: { label: '\u2620', color: '#a855f7', title: 'Recoil Friendly' },
  high_skill: { label: 'P', color: '#06b6d4', title: 'High Skill' },
  ascendable: { label: '\u2666', color: '#ec4899', title: 'Ascendable' },
  ramp_up: { label: '~', color: '#6b7280', title: 'Ramp Up' },
  synergy: { label: '+', color: '#14b8a6', title: 'Synergy Needed' },
  early_ranking: { label: '!', color: '#ef4444', title: 'Early Ranking' },
  meteor_tactic: { label: 'M', color: '#f97316', title: 'Meteor Tactic' },
  in_titan_crystal: { label: 'T', color: '#f59e0b', title: 'In Titan Crystal' },
};

function tagBadges(tags) {
  if (!tags || !tags.length) return '';
  return tags.map(t => {
    const b = TAG_BADGES[t];
    if (!b) return '';
    return `<span class="tb" style="color:${b.color};background:${b.color}20" title="${b.title}">${b.label}</span>`;
  }).join('');
}

function champHtml(c, rank) {
  const color = data.class_colors[c.class];
  const barColor = c.score >= 90 ? '#f59e0b' :
                   c.score >= 70 ? '#3b82f6' :
                   c.score >= 50 ? '#22c55e' :
                   c.score >= 30 ? '#555' : '#333';

  // Merge high_sig into tags so it uses the same blue arrow badge everywhere
  const tags = (c.tags ? [...c.tags] : []).filter(t => t !== 'high_sig_needed');
  const hasHighSig = c.high_sig || (c.tags && c.tags.includes('high_sig_needed'));

  let badges = '';
  if (c.awakened) badges += '<span class="aw" title="Benefits from Awakening"></span>';
  if (hasHighSig) badges += tagBadges(['high_sig_needed']);
  if (c.no7star) badges += '<span class="no7" title="Not available as 7-star">7</span>';
  badges += tagBadges(tags);

  const classTag = currentView === 'all'
    ? `<span class="champ-class" style="background:${color}15;color:${color}">${c.class}</span>`
    : '';
  const immLine = c.immunities && c.immunities.length
    ? `<div class="champ-imm-line">${c.immunities.map(i => `<span class="imm-tag">${i}</span>`).join('')}</div>`
    : '';

  return `<div class="champ">
    <span class="champ-rank">${rank}</span>
    ${portraitHtml(c)}
    <div class="champ-info">
      <span class="champ-name">${c.name}${badges}</span>
      ${immLine}
    </div>
    ${classTag}
    <span class="champ-bar-wrap"><div class="champ-bar"><div class="champ-bar-fill" style="width:${c.score}%;background:${barColor}"></div></div></span>
    <span class="champ-score">${c.score}</span>
  </div>`;
}

function render() {
  const champs = getFiltered();
  const tiers = [
    { key: 'God', label: 'God Tier' },
    { key: 'Great', label: 'Great' },
    { key: 'Good', label: 'Good' },
    { key: 'OK', label: 'OK' },
    { key: 'Low', label: 'Low' },
  ];

  let html = '';
  let rank = 1;
  for (const t of tiers) {
    const group = champs.filter(c => c.tier === t.key);
    if (!group.length) continue;
    html += `<div class="tier-section">
      <div class="tier-label" style="color:${data.tier_colors[t.key]}">
        ${t.label} <span class="tier-count">${group.length}</span>
      </div>
      ${group.map(c => champHtml(c, rank++)).join('')}
    </div>`;
  }
  document.getElementById('tierlist-content').innerHTML = html ||
    '<p class="empty">No champions found.</p>';
}

function renderImmunities() {
  const info = document.getElementById('imm-results-info');
  const field = immMode === 'immune' ? 'immunities' : 'inflicts';
  const verb = immMode === 'immune' ? 'immune to' : 'inflicting';

  let champs = data.champions.filter(c => c[field] && c[field].length > 0);

  if (selectedImms.size > 0) {
    champs = champs.filter(c =>
      [...selectedImms].every(imm => c[field].includes(imm))
    );
    const labels = [...selectedImms].join(' + ');
    info.textContent = `${champs.length} champion${champs.length !== 1 ? 's' : ''} ${verb} ${labels}`;
  } else {
    info.textContent = immMode === 'immune'
      ? `${champs.length} champions with at least one immunity`
      : `${champs.length} champions that inflict at least one debuff`;
  }

  champs.sort((a, b) => b.score - a.score);

  let html = champs.map(c => {
    const portrait = c.portrait
      ? `<img src="${c.portrait}" alt="" loading="lazy" onerror="this.outerHTML='<span class=fb>${c.name[0]}</span>'">`
      : `<span class="fb">${c.name[0]}</span>`;
    const color = data.class_colors[c.class];
    const tags = c[field].map(i => {
      const matched = selectedImms.has(i) ? ' matched' : '';
      return `<span class="imm-tag${matched}">${i}</span>`;
    }).join('');

    return `<div class="imm-champ-row">
      ${portrait}
      <span class="imm-champ-name">${c.name}</span>
      <span class="champ-class" style="background:${color}15;color:${color}">${c.class}</span>
      <span class="imm-champ-tags">${tags}</span>
      <span class="imm-champ-score">${c.score}</span>
    </div>`;
  }).join('');

  document.getElementById('imm-content').innerHTML = html ||
    '<p class="empty">No champions match.</p>';
}

function renderPriorityTab(sheetData, classView, contentId, infoId) {
  const tiers = [
    { key: 'Tier Above All', label: 'Tier Above All' },
    { key: 'Scorching', label: 'Scorching' },
    { key: 'Super Hot', label: 'Super Hot' },
    { key: 'Hot', label: 'Hot' },
    { key: 'Mild', label: 'Mild' },
  ];
  const tierColors = {
    'Tier Above All': '#f59e0b', 'Scorching': '#ef4444', 'Super Hot': '#f97316',
    'Hot': '#3b82f6', 'Mild': '#22c55e',
  };

  // Build list from sheet data, enrich with portraits and badges from main champion list
  let champs = Object.entries(sheetData).map(([name, info]) => {
    const main = data.champions.find(c => c.name === name);
    // Merge tags: sheet-specific tags + relevant main tierlist tags
    const tags = new Set(info.tags || []);
    if (main) {
      if (main.high_sig) tags.add('high_sig_needed');
      if (main.tags) main.tags.forEach(t => { if (t === 'defense') tags.add(t); });
    }
    return {
      name,
      class: info.class,
      tier: info.tier,
      score: info.score,
      tags: [...tags].sort(),
      portrait: main ? main.portrait : null,
    };
  });

  if (classView !== 'all') {
    champs = champs.filter(c => c.class === classView);
  }

  const info = document.getElementById(infoId);
  info.textContent = `${champs.length} champion${champs.length !== 1 ? 's' : ''}` +
    (classView !== 'all' ? ` in ${classView}` : '');

  let html = '';
  for (const t of tiers) {
    const group = champs.filter(c => c.tier === t.key);
    if (!group.length) continue;
    html += `<div class="tier-section">
      <div class="tier-label" style="color:${tierColors[t.key]}">
        ${t.label} <span class="tier-count">${group.length}</span>
      </div>
      ${group.map(c => {
        const portrait = c.portrait
          ? `<img src="${c.portrait}" alt="" loading="lazy" onerror="this.outerHTML='<span class=fb>${c.name[0]}</span>'">`
          : `<span class="fb">${c.name[0]}</span>`;
        const color = data.class_colors[c.class];
        const classTag = classView === 'all'
          ? `<span class="champ-class" style="background:${color}15;color:${color}">${c.class}</span>`
          : '';
        return `<div class="aw-champ-row">
          ${portrait}
          <span class="aw-champ-name">${c.name}${tagBadges(c.tags)}</span>
          ${classTag}
        </div>`;
      }).join('')}
    </div>`;
  }

  document.getElementById(contentId).innerHTML = html ||
    '<p class="empty">No champions found.</p>';
}

function renderAwakening() {
  renderPriorityTab(data.awakening_data || {}, awClassView, 'aw-content', 'aw-results-info');
}

function renderSigStones() {
  renderPriorityTab(data.sig_stones_data || {}, sigClassView, 'sig-content', 'sig-results-info');
}

function renderPrestige() {
  const champData = data.prestige[prestigeKey];
  if (!champData) {
    document.getElementById('prestige-content').innerHTML = '<p class="empty">No data available.</p>';
    return;
  }

  const sigLevels = data.prestige_sig_levels;
  const q = document.getElementById('prestige-search').value.toLowerCase();
  let entries = Object.entries(champData).map(([name, vals]) => ({ name, vals }));

  if (q) {
    entries = entries.filter(e => e.name.toLowerCase().includes(q));
  }

  // Sort by sig 200 (last value) descending
  entries.sort((a, b) => b.vals[b.vals.length - 1] - a.vals[a.vals.length - 1]);

  document.getElementById('prestige-info').textContent =
    `${entries.length} champions`;

  const thead = `<tr>
    <th>#</th><th></th><th>Champion</th>
    ${sigLevels.map(s => `<th>${s}</th>`).join('')}
  </tr>`;

  const rows = entries.map((e, i) => {
    const champ = data.champions.find(c => c.name === e.name);
    const imgUrl = (champ && champ.portrait) || data.prestige_portraits[e.name];
    const img = imgUrl
      ? `<img src="${imgUrl}" alt="" width="28" height="28" style="border-radius:5px" loading="lazy" onerror="this.outerHTML='<span class=fb>${e.name[0]}</span>'">`
      : `<span class="fb">${e.name[0]}</span>`;

    const maxVal = e.vals[e.vals.length - 1];
    const cells = e.vals.map(v =>
      `<td class="pv${v === maxVal ? ' pv-hi' : ''}">${v.toLocaleString()}</td>`
    ).join('');

    return `<tr>
      <td>${i + 1}</td>
      <td>${img}</td>
      <td>${e.name}</td>
      ${cells}
    </tr>`;
  }).join('');

  document.getElementById('prestige-content').innerHTML = entries.length
    ? `<table class="prestige-table"><thead>${thead}</thead><tbody>${rows}</tbody></table>`
    : '<p class="empty">No champions found.</p>';
}

init();
