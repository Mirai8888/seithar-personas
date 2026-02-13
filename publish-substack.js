
const https = require('https');
const fs = require('fs');

// Build cookie string
const cookies = JSON.parse(fs.readFileSync('/home/angel/.config/substack/cookies.json', 'utf8'));
const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');

// Convert markdown to ProseMirror JSON
function mdToProseMirror(md) {
  const lines = md.split('\n');
  const content = [];
  let i = 0;
  
  while (i < lines.length) {
    const line = lines[i];
    
    // Skip empty lines
    if (line.trim() === '') { i++; continue; }
    
    // Horizontal rule
    if (/^---+\s*$/.test(line.trim())) {
      content.push({ type: "horizontal_rule" });
      i++; continue;
    }
    
    // Headings
    const hMatch = line.match(/^(#{1,6})\s+(.*)/);
    if (hMatch) {
      const level = hMatch[1].length;
      content.push({
        type: "heading",
        attrs: { level },
        content: parseInline(hMatch[2])
      });
      i++; continue;
    }
    
    // Bullet list items
    if (/^[-*]\s/.test(line.trim())) {
      const items = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i].trim())) {
        const text = lines[i].trim().replace(/^[-*]\s+/, '');
        items.push({
          type: "list_item",
          content: [{ type: "paragraph", content: parseInline(text) }]
        });
        i++;
      }
      content.push({ type: "bullet_list", content: items });
      continue;
    }
    
    // Numbered list
    if (/^\d+\.\s/.test(line.trim())) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        const text = lines[i].trim().replace(/^\d+\.\s+/, '');
        items.push({
          type: "list_item",
          content: [{ type: "paragraph", content: parseInline(text) }]
        });
        i++;
      }
      content.push({ type: "ordered_list", attrs: { start: 1 }, content: items });
      continue;
    }
    
    // Regular paragraph
    content.push({
      type: "paragraph",
      content: parseInline(line)
    });
    i++;
  }
  
  // Add footer
  content.push({ type: "horizontal_rule" });
  content.push({
    type: "paragraph",
    content: parseInline("Full taxonomy and scanner: seithar.com | Research archive: github.com/Mirai8888/seithar-research | Discord: discord.gg/MktZyb2bvx")
  });
  
  return { type: "doc", content };
}

function parseInline(text) {
  const nodes = [];
  // Simple regex-based inline parsing
  const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let lastIndex = 0;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Text before match
    if (match.index > lastIndex) {
      nodes.push({ type: "text", text: text.slice(lastIndex, match.index) });
    }
    
    if (match[2]) { // bold+italic
      nodes.push({ type: "text", marks: [{ type: "bold" }, { type: "italic" }], text: match[2] });
    } else if (match[3]) { // bold
      nodes.push({ type: "text", marks: [{ type: "bold" }], text: match[3] });
    } else if (match[4]) { // italic
      nodes.push({ type: "text", marks: [{ type: "italic" }], text: match[4] });
    } else if (match[5]) { // code
      nodes.push({ type: "text", marks: [{ type: "code" }], text: match[5] });
    }
    
    lastIndex = match.index + match[0].length;
  }
  
  if (lastIndex < text.length) {
    nodes.push({ type: "text", text: text.slice(lastIndex) });
  }
  
  if (nodes.length === 0) {
    nodes.push({ type: "text", text: text || " " });
  }
  
  return nodes;
}

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const opts = {
      hostname: 'substack.com',
      path,
      method,
      headers: {
        'Cookie': cookieStr,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
      }
    };
    if (data) opts.headers['Content-Length'] = Buffer.byteLength(data);
    
    const req = https.request(opts, res => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => {
        console.log(`${method} ${path} -> ${res.statusCode}`);
        try { resolve(JSON.parse(body)); } catch(e) { resolve(body); }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function main() {
  const md = fs.readFileSync('/home/angel/seithar-research/output/CEA-2026-02-12-003-jsou-cognitive-warfare.md', 'utf8');
  const bodyJson = mdToProseMirror(md);
  
  console.log('Creating draft...');
  const draft = await request('POST', '/api/v1/drafts', {
    draft_title: "The State Discovers the Substrate — When Military Doctrine Meets Cognitive Defense",
    draft_subtitle: "JSOU, NATO, and Frontiers converge on the same attack surface. We mapped it first.",
    draft_bylines: [{ id: 83103230, is_guest: false }],
    type: "newsletter",
    audience: "everyone"
  });
  
  console.log('Draft response:', JSON.stringify(draft).slice(0, 500));
  
  const draftId = draft.id;
  if (!draftId) { console.error('No draft ID!', draft); return; }
  console.log('Draft ID:', draftId);
  
  console.log('Updating body...');
  const updated = await request('PUT', `/api/v1/drafts/${draftId}`, {
    body_json: bodyJson
  });
  console.log('Update response:', JSON.stringify(updated).slice(0, 300));
  
  console.log('Publishing...');
  const pub = await request('POST', `/api/v1/drafts/${draftId}/publish`, {
    draft_bylines: [{ id: 83103230, is_guest: false }]
  });
  console.log('Publish response:', JSON.stringify(pub).slice(0, 500));
}

main().catch(console.error);
