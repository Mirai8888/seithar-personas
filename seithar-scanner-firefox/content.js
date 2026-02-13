// Seithar Cognitive Threat Scanner — Content Script
(function() {
  if (window.__seitharScanned) {
    // Re-scan: remove old highlights
    document.querySelectorAll('.sct-highlight').forEach(el => {
      el.replaceWith(document.createTextNode(el.textContent));
    });
  }
  window.__seitharScanned = true;

  const SCT_PATTERNS = {
    'SCT-001': { name: 'Narrative Capture', severity: 'medium',
      keywords: ['narrative','framing','reframe','story','believe','truth claim','manufactured consent','echo chamber'] },
    'SCT-002': { name: 'Frequency Lock', severity: 'medium',
      keywords: ['repetition','always','never','every time','constant','drumbeat','saturate','flood'] },
    'SCT-003': { name: 'Substrate Priming', severity: 'high',
      keywords: ['prime','prepare','condition','normalize','desensitize','gradual','incremental','seed'] },
    'SCT-004': { name: 'Binding Protocol', severity: 'high',
      keywords: ['loyalty','pledge','oath','commitment','sacrifice','devotion','belong','identity'] },
    'SCT-005': { name: 'Identity Capture', severity: 'critical',
      keywords: ['us vs them','tribe','in-group','out-group','traitor','real identity','true believer'] },
    'SCT-006': { name: 'Consensus Manufacturing', severity: 'high',
      keywords: ['everyone knows','most people','studies show','experts agree','the science','overwhelming'] },
    'SCT-007': { name: 'Recursive Infection', severity: 'critical',
      keywords: ['share this','spread the word','viral','tell everyone','wake up','red pill','open your eyes'] },
    'SCT-008': { name: 'Temporal Distortion', severity: 'high',
      keywords: ['urgent','running out of time','now or never','before it\'s too late','ticking clock','deadline'] },
    'SCT-009': { name: 'Perception Management', severity: 'critical',
      keywords: ['look here not there','distract','deflect','whatabout','pivot','reframe','nothing to see'] },
    'SCT-010': { name: 'Adversarial Ontology', severity: 'critical',
      keywords: ['reality','what\'s really happening','hidden truth','they don\'t want you to know','cover up','false flag'] },
    'SCT-011': { name: 'Cognitive Sovereignty Erosion', severity: 'critical',
      keywords: ['can\'t think','overwhelm','confusion','contradiction','gaslight','doubt yourself'] },
    'SCT-012': { name: 'Existential Capture', severity: 'critical',
      keywords: ['survival','extinction','end times','apocalypse','civilization','future of humanity','no choice'] }
  };

  const severityColor = { low: '#3b82f6', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' };

  // Build one big regex per pattern for efficiency
  const compiledPatterns = {};
  for (const [code, pat] of Object.entries(SCT_PATTERNS)) {
    const escaped = pat.keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    compiledPatterns[code] = {
      ...pat,
      regex: new RegExp('\\b(' + escaped.join('|') + ')\\b', 'gi')
    };
  }

  const results = {};
  let totalMatches = 0;

  function walkTextNodes(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        const tag = node.parentElement?.tagName;
        if (!tag || ['SCRIPT','STYLE','NOSCRIPT','SVG','TEXTAREA','INPUT'].includes(tag)) return NodeFilter.FILTER_REJECT;
        if (node.parentElement.classList?.contains('sct-highlight')) return NodeFilter.FILTER_REJECT;
        return node.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });

    const textNodes = [];
    let n;
    while (n = walker.nextNode()) textNodes.push(n);
    return textNodes;
  }

  const textNodes = walkTextNodes(document.body);

  for (const node of textNodes) {
    const text = node.textContent;
    const matchesInNode = [];

    for (const [code, pat] of Object.entries(compiledPatterns)) {
      pat.regex.lastIndex = 0;
      let m;
      while ((m = pat.regex.exec(text)) !== null) {
        matchesInNode.push({ code, start: m.index, end: m.index + m[0].length, keyword: m[0], severity: pat.severity, name: pat.name });
        if (!results[code]) results[code] = { name: pat.name, severity: pat.severity, count: 0, examples: [] };
        results[code].count++;
        totalMatches++;
        if (results[code].examples.length < 3) {
          const ctx = text.substring(Math.max(0, m.index - 30), Math.min(text.length, m.index + m[0].length + 30)).trim();
          results[code].examples.push(ctx);
        }
      }
    }

    if (matchesInNode.length === 0) continue;

    // Sort by position descending to replace from end
    matchesInNode.sort((a, b) => b.start - a.start);

    // Deduplicate overlapping (keep highest severity)
    const sevOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    const filtered = [];
    for (const m of matchesInNode) {
      if (!filtered.some(f => m.start < f.end && m.end > f.start)) {
        filtered.push(m);
      }
    }

    let frag = document.createDocumentFragment();
    let remaining = text;

    // Sort ascending for building fragment
    filtered.sort((a, b) => a.start - b.start);

    let lastIdx = 0;
    for (const m of filtered) {
      if (m.start > lastIdx) frag.appendChild(document.createTextNode(remaining.substring(lastIdx, m.start)));
      const span = document.createElement('span');
      span.className = 'sct-highlight sct-' + m.severity;
      span.dataset.sctCode = m.code;
      span.dataset.sctName = m.name;
      span.title = `${m.code}: ${m.name}`;
      span.textContent = remaining.substring(m.start, m.end);
      frag.appendChild(span);
      lastIdx = m.end;
    }
    if (lastIdx < remaining.length) frag.appendChild(document.createTextNode(remaining.substring(lastIdx)));
    node.parentNode.replaceChild(frag, node);
  }

  // Calculate threat score (0-100)
  const wordCount = document.body.innerText.split(/\s+/).length || 1;
  const density = totalMatches / wordCount;
  const vectorCount = Object.keys(results).length;
  const hasCritical = Object.values(results).some(r => r.severity === 'critical' && r.count > 0);

  let score = Math.min(100, Math.round(
    (density * 2000) +
    (vectorCount * 5) +
    (hasCritical ? 15 : 0)
  ));

  const scanData = { score, totalMatches, vectorCount, results, url: location.href, title: document.title, timestamp: new Date().toISOString() };

  // Store results for popup
  browser.runtime.sendMessage({ type: 'scanResults', data: scanData });
})();
