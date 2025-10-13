# coding:utf-8
import os
import datetime
import requests
import urllib.parse
from pyquery import PyQuery as pq

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8'
}

# -------------------------
# 核心爬取函数
# -------------------------
def scrape_url(url):
    print(f"🕸️ Fetching: {url}")
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"⚠️ Request failed: {r.status_code}")
        return []

    d = pq(r.content)
    items = d('div.Box article.Box-row')

    results = []
    for item in items:
        i = pq(item)
        title = i(".lh-condensed a").text()
        description = i("p.col-9").text()
        href = i(".lh-condensed a").attr("href")
        if not href:
            continue
        url = "https://github.com" + href.strip()
        results.append({
            'title': title,
            'url': url,
            'description': format_description(description)
        })
    return results


# -------------------------
# 爬取单语言（英文 + 中文）
# -------------------------
def scrape_lang(language):
    """抓取某个语言的英文 trending"""
    lang_url = f"https://github.com/trending/{urllib.parse.quote_plus(language)}" if language else "https://github.com/trending"
    return scrape_url(lang_url)


def scrape_lang_zh(language):
    """抓取某个语言的中文 trending"""
    lang_url = f"https://github.com/trending/{urllib.parse.quote_plus(language)}?spoken_language_code=zh" if language else "https://github.com/trending?spoken_language_code=zh"
    return scrape_url(lang_url)


# -------------------------
# Markdown 输出逻辑
# -------------------------
def format_description(desc):
    return desc.replace('\r', '').replace('\n', '') if desc else ''


def convert_lang_title(lang):
    return "## All language" if lang == '' else f"## {lang.capitalize()}"


def format_results_md(results):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    content = ""
    for r in results:
        content += f"* 【{date_str}】[{r['title']}]({r['url']}) - {r['description']}\n"
    return content


def write_daily_file(base_dir, lang, results):
    """写入每日 markdown 文件"""
    os.makedirs(base_dir, exist_ok=True)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(base_dir, f"{today}.md")

    lang_title = convert_lang_title(lang)
    md_content = format_results_md(results)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{lang_title}\n\n{md_content}\n")

    print(f"✅ Wrote {len(results)} items for {lang or 'all'} to {file_path}")


# -------------------------
# 主任务
# -------------------------
def job():
    """主入口：抓取多语言 trending"""
    languages = ['', 'java', 'python', 'javascript', 'go', 'c', 'c++', 'c#', 'html', 'css', 'unknown']

    # 抓英文 trending
    for lang in languages:
        results = scrape_lang(lang)
        if results:
            write_daily_file("daily", lang, results)

    # 抓中文 trending
    for lang in languages:
        results_zh = scrape_lang_zh(lang)
        if results_zh:
            write_daily_file("daily_zh", lang, results_zh)


if __name__ == "__main__":
    job()
