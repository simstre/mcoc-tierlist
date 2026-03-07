let data = null;
let currentView = 'all';
let awClassView = 'all';
let sigClassView = 'all';
let selectedImms = new Set();
let prestigeKey = '';

async function init() {
  const res = await fetch('/api/tierlist');
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
    `<span class="source-info">${sourceInfo}</span><br>` +
    `<span class="aw"></span> benefits from awakening &nbsp; ` +
    `<span class="hs"></span> wants high sig &nbsp; ` +
    `<span class="no7">7</span> not available as 7-star`;

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

  // Immunity toggle buttons
  const immColors = {
    Bleed: '#ef4444', Poison: '#22c55e', Incinerate: '#f97316',
    Shock: '#eab308', Coldsnap: '#38bdf8', Frostbite: '#a5f3fc',
    Nullify: '#a855f7', Stagger: '#c084fc', 'Armor Break': '#9ca3af',
    'Fate Seal': '#f472b6',
  };
  const toggles = document.getElementById('imm-toggles');
  toggles.innerHTML = data.immunity_types.map(t =>
    `<button class="imm-toggle" data-imm="${t}" style="--imm-color:${immColors[t] || '#888'}">${t}</button>`
  ).join('');
  toggles.querySelectorAll('.imm-toggle').forEach(btn => {
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

function champHtml(c, rank) {
  const color = data.class_colors[c.class];
  const barColor = c.score >= 90 ? '#f59e0b' :
                   c.score >= 70 ? '#3b82f6' :
                   c.score >= 50 ? '#22c55e' :
                   c.score >= 30 ? '#555' : '#333';

  let badges = '';
  if (c.awakened) badges += '<span class="aw" title="Benefits from Awakening"></span>';
  if (c.high_sig) badges += '<span class="hs" title="Wants High Sig"></span>';
  if (c.no7star) badges += '<span class="no7" title="Not available as 7-star">7</span>';

  const classTag = currentView === 'all'
    ? `<span class="champ-class" style="background:${color}15;color:${color}">${c.class}</span>`
    : '';
  const immTags = c.immunities && c.immunities.length
    ? `<span class="champ-imm">${c.immunities.map(i => `<span class="imm-tag">${i}</span>`).join('')}</span>`
    : '';
  const tagLabels = data.tag_labels || {};
  const tagHtml = c.tags && c.tags.length
    ? `<span class="champ-tags">${c.tags.map(t => `<span class="tag" title="${tagLabels[t] || t}">${tagLabels[t] || t}</span>`).join('')}</span>`
    : '';

  return `<div class="champ">
    <span class="champ-rank">${rank}</span>
    ${portraitHtml(c)}
    <span class="champ-name">${c.name}${badges}</span>
    ${classTag}
    ${tagHtml}
    ${immTags}
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

  // Get champions with immunities
  let champs = data.champions.filter(c => c.immunities && c.immunities.length > 0);

  if (selectedImms.size > 0) {
    // Filter: champion must have ALL selected immunities
    champs = champs.filter(c =>
      [...selectedImms].every(imm => c.immunities.includes(imm))
    );
    const labels = [...selectedImms].join(' + ');
    info.textContent = `${champs.length} champion${champs.length !== 1 ? 's' : ''} immune to ${labels}`;
  } else {
    info.textContent = `${champs.length} champions with at least one immunity`;
  }

  // Sort by score descending
  champs.sort((a, b) => b.score - a.score);

  let html = champs.map(c => {
    const portrait = c.portrait
      ? `<img src="${c.portrait}" alt="" loading="lazy" onerror="this.outerHTML='<span class=fb>${c.name[0]}</span>'">`
      : `<span class="fb">${c.name[0]}</span>`;
    const color = data.class_colors[c.class];
    const tags = c.immunities.map(i => {
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

  // Build list from sheet data, enrich with portraits from main champion list
  let champs = Object.entries(sheetData).map(([name, info]) => {
    const main = data.champions.find(c => c.name === name);
    return {
      name,
      class: info.class,
      tier: info.tier,
      score: info.score,
      tags: info.tags || [],
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
        const prioTagLabels = {
          'high_sig_needed': 'High Sig', 'defense': 'BGs Defense', 'in_titan_crystal': 'Titan Crystal',
        };
        const tagHtml = c.tags.length
          ? `<span class="champ-tags">${c.tags.map(t => `<span class="tag">${prioTagLabels[t] || t}</span>`).join('')}</span>`
          : '';
        return `<div class="aw-champ-row">
          ${portrait}
          <span class="aw-champ-name">${c.name}</span>
          ${classTag}
          ${tagHtml}
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
