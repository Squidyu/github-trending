# coding:utf-8
import os
import datetime
import requests
import urllib.parse
from pyquery import PyQuery as pq

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

# 要抓取的语言列表（不包含 all）
LANGUAGES = ['java', 'python', 'javascript', 'go', 'c', 'c++', 'c#', 'html', 'css', 'unknown']

def scrape_url(url):
    """抓取单个 URL，返回 repo 列表：[{title, url, description}, ...]"""
    print(f"🕸 Fetching: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"⚠️ Request error for {url}: {e}")
        return []

    if r.status_code != 200:
        print(f"⚠️ Request returned status {r.status_code} for {url}")
        return []

    d = pq(r.content)
    items = d('div.Box article.Box-row')
    results = []
    for item in items:
        i = pq(item)
        title = (i(".lh-condensed a").text() or "").strip()
        desc = (i("p.col-9").text() or "").strip()
        href = i(".lh-condensed a").attr("href")
        if not href:
            continue
        repo_url = "https://github.com" + href.strip()
        results.append({
            'title': title,
            'url': repo_url,
            'description': desc.replace('\r', '').replace('\n', ' ')
        })
    return results

def unique_by_url(results):
    """按 URL 去重并保持顺序"""
    seen = set()
    out = []
    for r in results:
        if r['url'] not in seen:
            seen.add(r['url'])
            out.append(r)
    return out

def format_results_md(results):
    """把一组结果格式化成 Markdown 字符串（带当前日期）"""
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    lines = []
    for r in results:
        lines.append(f"* 【{date_str}】[{r['title']}]({r['url']}) - {r['description']}")
    return "\n".join(lines) + ("\n" if lines else "")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def read_today_file_lines(base_dir):
    """读取今日文件的所有行（用于去重），返回 set(url)"""
    ensure_dir(base_dir)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(base_dir, f"{today}.md")
    if not os.path.exists(file_path):
        return set()
    urls = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 期望格式包含 (https://github.com/xxx) ，尝试解析 url
                if '](' in line and ')' in line:
                    try:
                        part = line.split('](')[1]
                        url = part.split(')')[0].strip()
                        if url.startswith('https://github.com'):
                            urls.add(url)
                    except Exception:
                        continue
    except Exception as e:
        print(f"⚠️ Read file error {file_path}: {e}")
    return urls

def append_to_daily(base_dir, lang_title, results):
    """将 results 写入 base_dir/today.md，写前根据 URL 去重（避免今日重复条目）"""
    ensure_dir(base_dir)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(base_dir, f"{today}.md")
    existing_urls = read_today_file_lines(base_dir)

    # 过滤掉已存在的 url
    new_results = [r for r in results if r['url'] not in existing_urls]
    if not new_results:
        print(f"ℹ️ No new items to write for '{lang_title}' in {base_dir}")
        return 0

    md_block = f"{lang_title}\n\n" + format_results_md(new_results) + "\n"
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(md_block)
        print(f"✅ Wrote {len(new_results)} items to {file_path} (section: {lang_title})")
    except Exception as e:
        print(f"⚠️ Failed to write {file_path}: {e}")
        return 0
    return len(new_results)

def run_all():
    # All language (no suffix) -> daily
    print("=== Scraping All language (base) -> daily ===")
    all_results = scrape_url("https://github.com/trending")
    all_results = unique_by_url(all_results)
    append_to_daily("daily", "## All language", all_results)

    # Each language (english pages) -> daily
    for lang in LANGUAGES:
        print(f"--- language: {lang} -> daily ---")
        url = f"https://github.com/trending/{urllib.parse.quote_plus(lang)}"
        results = scrape_url(url)
        results = unique_by_url(results)
        append_to_daily("daily", f"## {lang.capitalize()}", results)

    # All language zh (spoken_language_code=zh) -> daily_zh
    print("=== Scraping All language (spoken_language_code=zh) -> daily_zh ===")
    all_zh = scrape_url("https://github.com/trending?spoken_language_code=zh")
    all_zh = unique_by_url(all_zh)
    append_to_daily("daily_zh", "## All language (zh)", all_zh)

    # Each language zh -> daily_zh
    for lang in LANGUAGES:
        print(f"--- language: {lang} (zh) -> daily_zh ---")
        url = f"https://github.com/trending/{urllib.parse.quote_plus(lang)}?spoken_language_code=zh"
        results = scrape_url(url)
        results = unique_by_url(results)
        append_to_daily("daily_zh", f"## {lang.capitalize()} (zh)", results)

if __name__ == "__main__":
    run_all()
