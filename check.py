import requests, json, os, re, sys
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE = "https://egy.voxcinemas.com"
# الصفحات اللي بيراقبها: أفلام معروضة دلوقتي + قريبًا
PAGES = {
    "معروض دلوقتي": BASE + "/movies/whatson",
    "قريبًا": BASE + "/movies/comingsoon",
}
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}
SKIP = {"whatson", "comingsoon", "all", "search", ""}

movies = {}  # path -> (اسم الفيلم, القسم)
for label, page_url in PAGES.items():
    r = requests.get(page_url, timeout=20, headers=HEADERS)
    print(label, "->", r.status_code)
    if r.status_code != 200:
        continue
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.select('a[href*="/movies/"]'):
        path = urlparse(urljoin(page_url, a["href"])).path
        parts = [p for p in path.split("/") if p]
        if len(parts) != 2 or parts[0] != "movies" or parts[1] in SKIP:
            continue
        name = a.get("title") or a.get_text(" ", strip=True)
        if not name:
            name = parts[1].replace("-", " ").title()
        # لو الفيلم ظهر في الصفحتين، نفضّل "معروض دلوقتي"
        if path not in movies or label == "معروض دلوقتي":
            movies[path] = (name, label)

print("لقيت", len(movies), "فيلم")

if not movies:
    sys.exit("مفيش أفلام اتقرأت")

seen = set(json.load(open(FILE, encoding="utf-8"))) if os.path.exists(FILE) else None

# أول تشغيل: بيحفظ القائمة من غير ما يبعت إشعارات
if seen is not None:
    for path in sorted(movies.keys() - seen):
        name, label = movies[path]
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": f"فيلم جديد ({label}): {name}\n{urljoin(BASE, path)}",
            },
            timeout=20,
        )

json.dump(
    sorted((seen or set()) | set(movies)),
    open(FILE, "w", encoding="utf-8"),
    ensure_ascii=False,
)
