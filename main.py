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
        "dateRestrict": "m1",
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
        return {}

    now = datetime.now()
    year = now.year
    ym = now.strftime("%Y年%m月")

    queries = {
        "融資": [
            f"中小企業 緊急融資 資金繰り {ym}",
            f"セーフティネット貸付 最新 {year}",
            f"日本政策金融公庫 新制度 {year}",
            "中東情勢 中小企業 融資 支援 最新",
        ],
        "補助金": [
            f"補助金 公募開始 中小企業 {ym}",
            f"ものづくり補助金 {year} 最新",
            f"IT導入補助金 {year} 申請",
        ],
        "助成金": [
            f"助成金 中小企業 {ym} 新設",
            f"雇用助成金 最新 {year}",
        ],
        "税制": [
            f"中小企業 税制改正 {year}",
            f"税制優遇 延長 新設 {year}",
        ],
    }

    results = {}
    for genre, qs in queries.items():
        genre_news = []
        for q in qs:
            items = search_google(q, google_api_key, google_cse_id, num=3)
            genre_news.extend(items)
            if len(genre_news) >= 6:
                break
        results[genre] = genre_news[:6]
    return results

def get_available_model(api_key):
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            for p in ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-3-5-sonnet-20241022"]:
                if p in models:
                    return p
            return models[0] if models else "claude-haiku-4-5"
    except:
        pass
    return "claude-haiku-4-5"

def format_news_for_prompt(news_dict):
    lines = []
    for genre, items in news_dict.items():
        lines.append(f"\n=== {genre} ===")
        for item in items:
            lines.append(f"・{item['title']}")
            lines.append(f"  {item['snippet']}")
            lines.append(f"  URL: {item['link']}")
    return "\n".join(lines)

def generate_report():
    api_key = get_clean_api_key()
    target_model = get_available_model(api_key)
    print(f"使用モデル: {target_model}")

    news_dict = collect_latest_news()
    news_text = format_news_for_prompt(news_dict)
    today_str = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""あなたは財務コンサルタント向け情報整理の専門家です。
以下の最新検索情報を使い、{today_str}時点のレポートをHTMLで作成してください。

【最新検索情報】
{news_text}

【デザイン・構成の要件】
1. ヘッダーに会社ロゴを表示する
   - ロゴ画像はリポジトリのルートにある「rogo.png」を使う
   - <img src="rogo.png" alt="HONEST" style="height:60px;">
   - ロゴの右に「株式会社HONEST」と社名を表示

2. タブ切り替え機能を実装する（JavaScriptで動作）
   - タブ①「エグゼクティブサマリー」：全ジャンルの要点を1画面で
   - タブ②「融資（最重要）」：融資・資金繰り情報を詳しく
   - タブ③「補助金」：補助金情報
   - タブ④「助成金」：助成金情報
   - タブ⑤「税制」：税制優遇情報
   - タブ⑥「コンサルティング提言」：顧客提案のポイントまとめ
   - デフォルトはタブ①を表示
   - タブをクリックすると必ずそのタブの内容が表示される

3. 各タブに検索情報の具体的な内容・金額・期限・URLリンクを記載

4. 中東情勢など緊急情報は赤枠で目立たせる

5. レポート上部に「{today_str}時点の情報」と明記

6. プロフェッショナルなデザイン（紺色ベース）

7. 完全なHTML（<!DOCTYPE html>から</html>まで）のみ出力

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
