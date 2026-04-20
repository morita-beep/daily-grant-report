import os
import requests
import anthropic
import sys
import re
from datetime import datetime

def get_clean_api_key():
    raw = os.environ.get("ANTHROPIC_API_KEY", "")
    clean = "".join(c for c in raw.strip() if c.isprintable() and ord(c) < 128)
    if not clean.startswith("sk-ant-"):
        print(f"Error: {clean[:10]!r}")
        sys.exit(1)
    return clean

def search_google(query, api_key, cse_id, num=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num,
        "lr": "lang_ja",
        "dateRestrict": "m1",  # 常に直近1ヶ月
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            items = response.json().get("items", [])
            return [{"title": i.get("title",""), 
                    "snippet": i.get("snippet",""), 
                    "link": i.get("link","")} for i in items]
    except Exception as e:
        print(f"検索エラー: {e}")
    return []

def collect_latest_news():
    google_api_key = os.environ.get("GOOGLE_API_KEY", "")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID", "")
    
    if not google_api_key or not google_cse_id:
        print("警告: Google APIキーが未設定")
        return ""
    
    # ✅ 年・月・日を全部自動取得（2027年でも2030年でも自動対応）
    now = datetime.now()
    year = now.year          # 例: 2026
    month = now.month        # 例: 4
    ym = now.strftime("%Y年%m月")  # 例: 2026年04月

    search_queries = {
        "融資・資金繰り（最重要）": [
            f"中小企業 緊急融資 資金繰り {ym}",
            f"セーフティネット貸付 最新 {year}",
            f"日本政策金融公庫 新制度 {year}",
            f"中小企業 融資 緊急支援 最新情報",
            # 時事ニュースも自動で拾う
            f"中小企業 資金繰り 支援 緊急 site:meti.go.jp OR site:chusho.meti.go.jp",
        ],
        "補助金": [
            f"補助金 公募開始 中小企業 {ym}",
            f"ものづくり補助金 {year} 最新",
            f"補助金 申請受付 {year} site:j-net21.smrj.go.jp",
        ],
        "助成金": [
            f"助成金 中小企業 {ym} 新設 変更",
            f"雇用助成金 最新 {year}",
        ],
        "税制優遇": [
            f"中小企業 税制改正 {year}",
            f"税制優遇 延長 新設 {year} 中小企業",
        ],
    }
    
    all_news = []
    for genre, queries in search_queries.items():
        genre_news = []
        for query in queries:
            results = search_google(query, google_api_key, google_cse_id, num=3)
            genre_news.extend(results)
            if len(genre_news) >= 6:
                break
        if genre_news:
            all_news.append(f"\n=== {genre} ===")
            for item in genre_news[:6]:
                all_news.append(f"・{item['title']}")
                all_news.append(f"  {item['snippet']}")
                all_news.append(f"  URL: {item['link']}")
    
    return "\n".join(all_news)

def get_available_model(api_key):
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            priority = ["claude-haiku-4-5", "claude-sonnet-4-5", 
                       "claude-3-5-sonnet-20241022"]
            for p in priority:
                if p in models:
                    return p
            return models[0] if models else "claude-haiku-4-5"
    except:
        pass
    return "claude-haiku-4-5"

def generate_report():
    api_key = get_clean_api_key()
    target_model = get_available_model(api_key)
    print(f"使用モデル: {target_model}")
    
    latest_news = collect_latest_news()
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    if latest_news:
        prompt = f"""あなたは財務コンサルタント向け情報整理の専門家です。
以下の【本日({today_str})時点の最新検索情報】を使い、
財務コンサルタントが顧客提案に使えるレポートをHTMLで作成してください。

【最新検索情報】
{latest_news}

【必須条件】
- 融資・資金繰り情報を最初に・最も詳しく記載（最重要）
- 検索情報にある制度名・金額・期限・URLを必ず記載
- 時事的な緊急支援（中東情勢等）は赤枠で目立たせる
- レポート上部に「{today_str}時点の情報」と明記
- 情報源URLをクリックできるリンクとして記載
- 見やすいCSS込みの完全なHTMLで出力
- </html>で終わるコードのみ出力"""
    else:
        prompt = f"""財務コンサルタント向けに{today_str}時点の
補助金・助成金・融資（最重要）・税制レポートを
CSS込みの完全なHTMLで作成してください。
</html>で終わるコードのみ出力してください。"""
    
    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=target_model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text
        html = re.sub(r'^.*?<!DOCTYPE', '<!DOCTYPE', raw, 
                     flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'</html>.*$', '</html>', html, 
                     flags=re.DOTALL | re.IGNORECASE)
        return html
    except Exception as e:
        print(f"APIエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"完了: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} にindex.htmlを生成")
