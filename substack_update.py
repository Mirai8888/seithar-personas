import json, requests, sys

# Load cookies
with open('/home/angel/.config/substack/cookies.json') as f:
    cookies_list = json.load(f)

cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies_list)
headers = {
    'Cookie': cookie_str,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}

FOOTER_NODES = [
    {"type":"horizontal_rule"},
    {"type":"paragraph","content":[
        {"type":"text","marks":[{"type":"bold"}],"text":"Seithar Group Intelligence & Research Division"},
        {"type":"hard_break"},
        {"type":"text","text":"Discord: "},
        {"type":"text","marks":[{"type":"link","attrs":{"href":"https://discord.gg/MktZyb2bvx"}}],"text":"discord.gg/MktZyb2bvx"},
        {"type":"text","text":" · Mirai Junsei: "},
        {"type":"text","marks":[{"type":"link","attrs":{"href":"https://x.com/gOPwbi7qqtWeD9o"}}],"text":"@未来純正"},
        {"type":"text","text":" · "},
        {"type":"text","marks":[{"type":"link","attrs":{"href":"https://x.com/SeitharGroup"}}],"text":"@SeitharGroup"},
        {"type":"text","text":" · "},
        {"type":"text","marks":[{"type":"link","attrs":{"href":"https://github.com/Mirai8888"}}],"text":"GitHub"},
        {"type":"text","text":" · 認知作戦"}
    ]}
]

# List all posts
all_posts = []
offset = 0
while True:
    r = requests.get(f'https://seithar.substack.com/api/v1/archive?sort=new&limit=50&offset={offset}', headers=headers)
    r.raise_for_status()
    posts = r.json()
    if not posts:
        break
    all_posts.extend(posts)
    if len(posts) < 50:
        break
    offset += 50

print(f"Found {len(all_posts)} posts total")

updated = 0
skipped = 0
errors = 0

for post in all_posts:
    pid = post['id']
    title = post.get('title', 'Untitled')
    
    # Get draft details
    try:
        r = requests.get(f'https://seithar.substack.com/api/v1/drafts/{pid}', headers=headers)
        r.raise_for_status()
        draft = r.json()
    except Exception as e:
        print(f"  ERROR getting draft {pid} ({title}): {e}")
        errors += 1
        continue
    
    body_json = draft.get('draft_body') or draft.get('body')
    if not body_json:
        print(f"  SKIP {pid} ({title}): no body")
        skipped += 1
        continue
    
    # Check if already has footer
    if 'discord.gg/MktZyb2bvx' in body_json:
        print(f"  SKIP {pid} ({title}): already has footer")
        skipped += 1
        continue
    
    # Parse and append
    try:
        body = json.loads(body_json)
    except:
        print(f"  ERROR {pid} ({title}): can't parse body JSON")
        errors += 1
        continue
    
    body['content'].extend(FOOTER_NODES)
    
    # PUT back
    payload = {"draft_body": json.dumps(body)}
    try:
        r = requests.put(f'https://seithar.substack.com/api/v1/drafts/{pid}', headers=headers, json=payload)
        r.raise_for_status()
        print(f"  UPDATED {pid} ({title})")
        updated += 1
    except Exception as e:
        print(f"  ERROR updating {pid} ({title}): {e} - {r.text[:200] if r else ''}")
        errors += 1

print(f"\nDone: {updated} updated, {skipped} skipped, {errors} errors")
