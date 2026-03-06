const IMM_COLORS = {
  Bleed:      '#ef4444',
  Poison:     '#22c55e',
  Incinerate: '#f97316',
  Shock:      '#eab308',
  Coldsnap:   '#38bdf8',
  Frostbite:  '#a5f3fc',
  Nullify:    '#a855f7',
  Stagger:    '#c084fc',
  'Armor Break': '#9ca3af',
  'Fate Seal':   '#f472b6',
};

// Circle layout positions (center of SVG = 500, 400)
const CIRCLE_DEFS = {
  Bleed:       { cx: 340, cy: 300, r: 200 },
  Poison:      { cx: 620, cy: 280, r: 210 },
  Incinerate:  { cx: 480, cy: 460, r: 190 },
  Shock:       { cx: 280, cy: 530, r: 170 },
  Coldsnap:    { cx: 680, cy: 500, r: 150 },
  Frostbite:   { cx: 750, cy: 370, r: 130 },
  Nullify:     { cx: 150, cy: 380, r: 100 },
  Stagger:     { cx: 130, cy: 510, r: 90 },
  'Armor Break':{ cx: 170, cy: 260, r: 100 },
  'Fate Seal':  { cx: 100, cy: 430, r: 80 },
};

let data = null;
let activeFilter = null;
let champNodes = [];
const PORTRAIT_R = 14;

async function init() {
  const res = await fetch('/api/tierlist');
  data = await res.json();
  buildLegend();
  buildDiagram();
}

function buildLegend() {
  const legend = document.getElementById('legend');
  legend.innerHTML = Object.entries(IMM_COLORS).map(([type, color]) => {
    const count = (data.immunity_map[type] || []).length;
    return `<div class="legend-item" data-imm="${type}">
      <span class="legend-dot" style="background:${color}"></span>
      ${type} (${count})
    </div>`;
  }).join('');

  legend.querySelectorAll('.legend-item').forEach(item => {
    item.addEventListener('click', () => {
      const imm = item.dataset.imm;
      if (activeFilter === imm) {
        activeFilter = null;
        legend.querySelectorAll('.legend-item').forEach(i => i.classList.remove('active'));
      } else {
        activeFilter = imm;
        legend.querySelectorAll('.legend-item').forEach(i =>
          i.classList.toggle('active', i.dataset.imm === imm));
      }
      updateVisibility();
    });
  });
}

function getChampImmunities(name) {
  const c = data.champions.find(ch => ch.name === name);
  return c ? (c.immunities || []) : [];
}

function getChampPortrait(name) {
  const c = data.champions.find(ch => ch.name === name);
  return c ? c.portrait : null;
}

function computePosition(immunities) {
  // Place champion at the centroid of the circles they belong to
  if (immunities.length === 0) return null;

  let cx = 0, cy = 0;
  for (const imm of immunities) {
    const circle = CIRCLE_DEFS[imm];
    if (circle) {
      cx += circle.cx;
      cy += circle.cy;
    }
  }
  cx /= immunities.length;
  cy /= immunities.length;
  return { cx, cy };
}

function resolveCollisions(nodes) {
  // Simple iterative collision resolution
  for (let iter = 0; iter < 50; iter++) {
    let moved = false;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const minDist = PORTRAIT_R * 2 + 2;
        if (dist < minDist && dist > 0) {
          const push = (minDist - dist) / 2;
          const nx = dx / dist, ny = dy / dist;
          a.x -= nx * push;
          a.y -= ny * push;
          b.x += nx * push;
          b.y += ny * push;
          moved = true;
        }
      }
    }
    if (!moved) break;
  }
}

function buildDiagram() {
  const svg = document.getElementById('svg');
  const W = 900, H = 750;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  // Draw immunity circles
  let circlesHtml = '';
  for (const [type, def] of Object.entries(CIRCLE_DEFS)) {
    const color = IMM_COLORS[type];
    circlesHtml += `<ellipse class="imm-circle" data-imm="${type}"
      cx="${def.cx}" cy="${def.cy}" rx="${def.r}" ry="${def.r * 0.85}"
      fill="${color}" stroke="${color}" />`;
    circlesHtml += `<text class="imm-label" x="${def.cx}" y="${def.cy - def.r * 0.85 + 18}"
      fill="${color}">${type}</text>`;
  }

  // Collect champions with immunities
  const immuneChamps = new Set();
  for (const champs of Object.values(data.immunity_map)) {
    champs.forEach(n => immuneChamps.add(n));
  }

  // Compute positions
  champNodes = [];
  for (const name of immuneChamps) {
    const immunities = getChampImmunities(name);
    const pos = computePosition(immunities);
    if (pos) {
      // Add some jitter to avoid exact overlaps
      champNodes.push({
        name,
        immunities,
        portrait: getChampPortrait(name),
        x: pos.cx + (Math.random() - 0.5) * 30,
        y: pos.cy + (Math.random() - 0.5) * 30,
      });
    }
  }

  // Resolve overlaps
  resolveCollisions(champNodes);

  // Draw champions
  let champsHtml = '';
  for (const node of champNodes) {
    const imgHtml = node.portrait
      ? `<image href="${node.portrait}" x="${node.x - PORTRAIT_R}" y="${node.y - PORTRAIT_R}"
          width="${PORTRAIT_R * 2}" height="${PORTRAIT_R * 2}" clip-path="inset(0 round ${PORTRAIT_R}px)"
          class="champ-img" preserveAspectRatio="xMidYMid slice" />`
      : `<circle cx="${node.x}" cy="${node.y}" r="${PORTRAIT_R}" fill="#222" class="champ-img" />`;

    // Use clipPath for round images
    const clipId = `clip-${node.name.replace(/[^a-zA-Z0-9]/g, '')}`;
    champsHtml += `<g class="champ-group" data-name="${node.name}" data-imm="${node.immunities.join(',')}">
      <defs><clipPath id="${clipId}"><circle cx="${node.x}" cy="${node.y}" r="${PORTRAIT_R}" /></clipPath></defs>
      <image href="${node.portrait || ''}" x="${node.x - PORTRAIT_R}" y="${node.y - PORTRAIT_R}"
        width="${PORTRAIT_R * 2}" height="${PORTRAIT_R * 2}"
        clip-path="url(#${clipId})" preserveAspectRatio="xMidYMid slice" />
      <circle cx="${node.x}" cy="${node.y}" r="${PORTRAIT_R}" fill="none" class="champ-img" />
      <text class="champ-label" x="${node.x}" y="${node.y + PORTRAIT_R + 10}">${node.name}</text>
    </g>`;
  }

  svg.innerHTML = circlesHtml + champsHtml;

  // Tooltip
  const tooltip = document.getElementById('tooltip');
  svg.querySelectorAll('.champ-group').forEach(g => {
    g.addEventListener('mouseenter', (e) => {
      const name = g.dataset.name;
      const imms = g.dataset.imm.split(',').filter(Boolean);
      tooltip.innerHTML = `<div class="tt-name">${name}</div>
        <div class="tt-imm">${imms.map(i =>
          `<span class="tt-tag" style="border-left:2px solid ${IMM_COLORS[i] || '#666'}">${i}</span>`
        ).join('')}</div>`;
      tooltip.style.display = 'block';
    });
    g.addEventListener('mousemove', (e) => {
      tooltip.style.left = (e.clientX + 12) + 'px';
      tooltip.style.top = (e.clientY - 10) + 'px';
    });
    g.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none';
    });
  });
}

function updateVisibility() {
  document.querySelectorAll('.champ-group').forEach(g => {
    if (!activeFilter) {
      g.style.opacity = '1';
      return;
    }
    const imms = g.dataset.imm.split(',');
    g.style.opacity = imms.includes(activeFilter) ? '1' : '0.1';
  });
  document.querySelectorAll('.imm-circle').forEach(c => {
    if (!activeFilter) {
      c.style.fillOpacity = '0.08';
      c.style.strokeOpacity = '0.4';
      return;
    }
    const match = c.dataset.imm === activeFilter;
    c.style.fillOpacity = match ? '0.15' : '0.03';
    c.style.strokeOpacity = match ? '0.7' : '0.15';
  });
}

init();
