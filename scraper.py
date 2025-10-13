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

def scrape_url(url):
    """Scrape github trending url"""
    print(f"Scraping: {url}")
    r = requests.get(url, headers=HEADERS)
    assert r.status_code == 200, f"Request failed: {r.status_code}"

    d = pq(r.content)
    items = d('div.Box article.Box-row')
    results = []

    for item in items:
        i = pq(item)
        title = i(".lh-condensed a").text()
        description = i("p.col-9").text()
        repo_url = i(".lh-condensed a").attr("href")
        if repo_url:
            repo_url = "https://github.com" + repo_url.strip()
        results.append({
            'title': title,
            'url': repo_url,
            'description': (description or '').replace('\r', '').replace('\n', '')
        })
    return results

def scrape_lang(language):
    """Scrape github trending with lang parameters"""
    url1 = f'https://github.com/trending/{urllib.parse.quote_plus(language)}'
    url2 = f'{url1}?spoken_language_code=zh'

    results1 = scrape_url(url1)
    results2 = scrape_url(url2)

    # 合并去重
    seen = set()
    merged = []
    for r in results1 + results2:
        if r['title'] not in seen:
            seen.add(r['title'])
            merged.append(r)
    return merged

def convert_lang_title(lang):
    if lang == '':
        return '## All language'
    return f'## {lang.capitalize()}'

def get_archived_contents():
    archived_contents = []
    if not os.path.exists('./daily'):
        os.makedirs('./daily')
    for file in os.listdir('./daily'):
        if file.endswith('.md'):
            with open(f'./daily/{file}', mode='r', encoding='utf-8') as f:
                archived_contents.append(f.read())
    return archived_contents

def is_title_exist(title, content_list):
    """判断项目是否已存在于任意历史内容中"""
    for content in content_list:
        if f"[{title}]" in content:
            return True
    return False

def write_markdown(lang, results, archived_contents):
    """更新 README.md 并生成 daily 文件"""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    lang_title = convert_lang_title(lang)
    today_file = f'./daily/{today}.md'

    # 生成新增内容
    new_results = [
        r for r in results if not is_title_exist(r['title'], archived_contents)
    ]
    if not new_results:
        print(f"No new results for {lang or 'all'} today.")
        return

    result_str = ""
    for r in new_results:
        result_str += f"* 【{today}】[{r['title']}]({r['url']}) - {r['description']}\n"

    # 写入 README.md
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    else:
        readme_content = ''

    if lang_title not in readme_content:
        readme_content += f'\n{lang_title}\n\n'

    readme_content = readme_content.replace(
        f'{lang_title}\n\n', f'{lang_title}\n\n{result_str}'
    )
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # 写入 daily 文件
    with open(today_file, 'a', encoding='utf-8') as f:
        f.write(f'{lang_title}\n\n{result_str}\n')

    print(f"✅ Wrote {len(new_results)} new results for {lang or 'all'} to {today_file}")

def job():
    """Main job entry"""
    archived_contents = get_archived_contents()

    languages = ['', 'java', 'python', 'javascript', 'go', 'c', 'c++', 'c#', 'html', 'css', 'unknown']
    for lang in languages:
        results = scrape_lang(lang)
        write_markdown(lang, results, archived_contents)

if __name__ == '__main__':
    job()
