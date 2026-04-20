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
            f"信用保証協会 保証制度 {year} 最新",
            f"中小企業 低金利融資 {year}",
        ],
        "補助金": [
            f"補助金 公募開始 中小企業 {ym}",
            f"ものづくり補助金 {year} 最新 要件",
            f"IT導入補助金 {year} 申請 要件",
            f"事業再構築補助金 {year} 最新",
            f"小規模事業者持続化補助金 {year}",
            f"省力化投資補助金 {year}",
        ],
        "助成金": [
            f"助成金 中小企業 {ym} 新設",
            f"雇用調整助成金 {year} 最新",
            f"キャリアアップ助成金 {year} 要件",
            f"業務改善助成金 {year} 申請",
            f"人材開発支援助成金 {year}",
        ],
        "税制": [
            f"中小企業 税制改正 {year} 詳細",
            f"税制優遇 延長 新設 {year}",
            f"賃上げ促進税制 {year} 要件",
            f"中小企業経営強化税制 {year}",
            f"研究開発税制 中小企業 {year}",
        ],
    }

    results = {}
    for genre, qs in queries.items():
        genre_news = []
        for q in qs:
            items = search_google(q, google_api_key, google_cse_id, num=5)
            genre_news.extend(items)
            if len(genre_news) >= 15:
                break
        results[genre] = genre_news[:15]
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

1. ヘッダー
   - <img src="rogo.png" alt="HONEST" style="height:60px;"> でロゴ表示
   - ロゴ右に「株式会社HONEST」と表示
   - 右端に「{today_str}時点の情報」と表示

2. AI検索機能（ページ上部に設置）
   以下のHTMLとJavaScriptを必ず実装する：
   - テキスト入力欄（placeholder：「制度名を入力して検索（例：ものづくり補助金）」）
   - 「AIに質問する」ボタン
   - 結果表示エリア
   - JavaScriptでAnthropicAPIを呼び出す：
     fetch('https://api.anthropic.com/v1/messages', {{
       method: 'POST',
       headers: {{
         'Content-Type': 'application/json',
         'x-api-key': '{{{{ANTHROPIC_API_KEY}}}}',
         'anthropic-version': '2023-06-01',
         'anthropic-dangerous-direct-browser-access': 'true'
       }},
       body: JSON.stringify({{
         model: '{target_model}',
         max_tokens: 1000,
         messages: [{{role:'user', content: '中小企業の財務コンサルタントとして、次の制度について詳しく教えてください。対象者・金額・申請条件・注意点・申請窓口を箇条書きで: ' + query}}]
       }})
     }})
   - APIキーはHTML内に直接埋め込む（下記の REPLACE_API_KEY の部分）
   - ローディング中は「AIが調査中...」と表示
   - 結果は見やすく整形して表示

3. タブ切り替え（6タブ）
   - ①エグゼクティブサマリー
   - ②融資（最重要）
   - ③補助金
   - ④助成金
   - ⑤税制
   - ⑥コンサルティング提言

4. 各タブの情報量（重要）
   融資タブ：
   - 各制度ごとに「融資上限額」「金利」「返済期間」「対象者」「申請条件」「注意点」「窓口」を記載
   - 中東情勢対応の緊急融資は赤枠で強調
   
   補助金タブ：
   - 各制度ごとに「上限額」「補助率」「対象者」「対象経費」「申請要件」「スケジュール」「注意点」を記載
   
   助成金タブ：
   - 各制度ごとに「支給額」「対象者」「受給要件」「申請手続き」「注意点」を記載
   
   税制タブ：
   - 各制度ごとに「控除額・税額控除率」「対象者」「適用要件」「申請方法」「期限」を記載

5. タブJS：
   <script>
   function showTab(tabId, btn) {{
     document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
     document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
     document.getElementById(tabId).style.display = 'block';
     btn.classList.add('active');
   }}
   window.onload = function() {{
     document.getElementById('tab1').style.display = 'block';
     document.querySelector('.tab-btn').classList.add('active');
   }};
   </script>

6. プロフェッショナルな紺色ベースのデザイン

7. 完全なHTML（<!DOCTYPE html>から</html>まで）のみ出力

重要：APIキーの埋め込み箇所は必ず文字列 REPLACE_API_KEY と書いてください。

</html>で終わるコードのみ出力してください。"""

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=target_model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text
        html = re.sub(r'^.*?<!DOCTYPE', '<!DOCTYPE', raw,
                     flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'</html>.*$', '</html>', html,
                     flags=re.DOTALL | re.IGNORECASE)

        # REPLACE_API_KEY を実際のAPIキーに置き換える
        html = html.replace('REPLACE_API_KEY', api_key)

        return html
    except Exception as e:
        print(f"APIエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"完了: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} にindex.htmlを生成")
