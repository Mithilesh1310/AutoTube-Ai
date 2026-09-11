import urllib.request
import re
import json

vids = ['jt5phkQyXIs', 'PbUxjlJRv5s', 'Nxg4gzQZxkA', 'Kl7izz3TnY0', 'ccvpQOjWxxs', 'V-mX38MRy5w']

print("--- Testing Channel Page ---")
url = "https://www.youtube.com/@kidscartoonuniversa"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
})
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
        # Channel ID
        cid = re.findall(r'"channelId":"(UC[^"]+)"', html)
        print("Channel IDs found:", set(cid))
        
        # Sub count
        subs = re.findall(r'(\d+[\.\d]*[KkMm]?)\s*subscribers?', html)
        print("Sub matches:", subs)
        
        # Check for 0 subscribers or no subscribers text
        no_subs = re.findall(r'([Nn]o subscribers)', html)
        print("No sub matches:", no_subs)
except Exception as e:
    print("Channel fetch error:", e)

print("\n--- Testing Video Views & Likes ---")
total_views = 0
total_likes = 0
for vid in vids:
    v_url = f"https://www.youtube.com/watch?v={vid}"
    v_req = urllib.request.Request(v_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    try:
        with urllib.request.urlopen(v_req, timeout=10) as v_res:
            v_html = v_res.read().decode('utf-8', errors='ignore')
            # Extract view count
            view_match = re.search(r'"viewCount":"(\d+)"', v_html)
            views = int(view_match.group(1)) if view_match else 0
            
            # Extract like count
            like_match = re.search(r'"defaultText":\{"accessibility":\{"accessibilityData":\{"label":"(\d+[\d,]*)\s*likes?"\}\}', v_html)
            if not like_match:
                like_match = re.search(r'"likeCount":"(\d+)"', v_html)
            
            likes = 0
            if like_match:
                likes = int(like_match.group(1).replace(',', ''))
            
            # Title
            title_match = re.search(r'<title>([^<]+)</title>', v_html)
            title = title_match.group(1) if title_match else vid
            
            print(f"Vid: {vid} | Views: {views} | Likes: {likes} | Title: {title[:40]}")
            total_views += views
            total_likes += likes
    except Exception as e:
        print(f"Vid: {vid} | Error: {e}")

print(f"\nTOTAL VIEWS: {total_views} | TOTAL LIKES: {total_likes}")
