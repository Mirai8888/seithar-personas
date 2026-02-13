let lastScanData = null;

document.getElementById('scan-btn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  const resultsEl = document.getElementById('results');
  statusEl.textContent = 'SCANNING…';
  statusEl.classList.remove('hidden');
  resultsEl.classList.add('hidden');

  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) { statusEl.textContent = 'NO ACTIVE TAB'; return; }

  try {
    await browser.tabs.insertCSS(tab.id, { file: 'styles.css' });
    await browser.tabs.executeScript(tab.id, { file: 'content.js' });
  } catch (e) {
    statusEl.textContent = 'CANNOT SCAN THIS PAGE';
    return;
  }

  // Listen for results
  const handler = (msg) => {
    if (msg.type === 'scanResults') {
      browser.runtime.onMessage.removeListener(handler);
      lastScanData = msg.data;
      renderResults(msg.data);
    }
  };
  browser.runtime.onMessage.addListener(handler);

  // Timeout
  setTimeout(() => {
    browser.runtime.onMessage.removeListener(handler);
    if (!lastScanData) {
      statusEl.textContent = 'NO RESULTS — PAGE MAY BE RESTRICTED';
    }
  }, 5000);
});

function renderResults(data) {
  document.getElementById('status').classList.add('hidden');
  const resultsEl = document.getElementById('results');
  resultsEl.classList.remove('hidden');

  const scoreEl = document.getElementById('score');
  scoreEl.textContent = data.score;
  scoreEl.className = 'score-value ' + (
    data.score < 20 ? 'low' : data.score < 45 ? 'medium' : data.score < 70 ? 'high' : 'critical'
  );

  document.getElementById('vector-count').textContent = data.vectorCount;
  document.getElementById('match-count').textContent = data.totalMatches;

  const vectorsEl = document.getElementById('vectors');
  vectorsEl.innerHTML = '';

  const sorted = Object.entries(data.results).sort((a, b) => b[1].count - a[1].count);

  for (const [code, info] of sorted) {
    const div = document.createElement('div');
    div.className = 'vector sev-' + info.severity;
    div.innerHTML = `
      <div class="vector-header">
        <div>
          <span class="vector-code">${code}</span>
          <span class="vector-name">${info.name}</span>
        </div>
        <span class="vector-count">×${info.count}</span>
      </div>
      ${info.examples[0] ? `<div class="vector-example">…${info.examples[0]}…</div>` : ''}
    `;
    vectorsEl.appendChild(div);
  }

  if (sorted.length === 0) {
    vectorsEl.innerHTML = '<div style="padding:20px;text-align:center;color:#999;font-size:11px;letter-spacing:2px;text-transform:uppercase">No threat patterns detected</div>';
  }
}

document.getElementById('share-btn').addEventListener('click', () => {
  if (!lastScanData) {
    copyToClipboard('No scan data yet. Click "Scan Page" first.');
    return;
  }
  const d = lastScanData;
  const level = d.score < 20 ? '🟢' : d.score < 45 ? '🟡' : d.score < 70 ? '🟠' : '🔴';
  const vectors = Object.entries(d.results)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 5)
    .map(([code, info]) => `${code} ${info.name} (×${info.count})`)
    .join('\n');

  const text = `${level} Seithar Cognitive Threat Score: ${d.score}/100

${d.vectorCount} vectors detected, ${d.totalMatches} matches

${vectors}

Scanned: ${d.title}
${d.url}

🛡️ seithar.com | github.com/Mirai8888/seithar-cogdef`;

  copyToClipboard(text);
});

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('share-btn');
    btn.textContent = 'COPIED';
    setTimeout(() => { btn.textContent = 'SHARE ANALYSIS'; }, 1500);
  });
}
