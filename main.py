import os
import requests
import anthropic
import sys

def get_clean_env(name):
    val = os.environ.get(name, "")
    return val.strip() if val else None

# 設定の読み込み
GOOGLE_API_KEY = get_clean_env("GOOGLE_API_KEY")
GOOGLE_CSE_ID = get_clean_env("GOOGLE_CSE_ID")
ANTHROPIC_API_KEY = get_clean_env("ANTHROPIC_API_KEY")
ANTHROPIC_ORG_ID = get_clean_env("ANTHROPIC_ORG_ID")

def get_news():
    print("--- Google検索開始 ---")
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return None
    
    query = "補助金 助成金 融資 税制優遇 最新 2026"
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}&hl=ja"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if "error" in data:
            print(f"Google APIエラー (スキップします): {data['error'].get('message')}")
            return None
        items = data.get("items", [])
        return "".join([f"【{i['title']}】\n{i['link']}\n{i['snippet']}\n\n" for i in items])
    except:
        return None

def generate_report(news_text):
    print("--- Claudeレポート生成開始 ---")
    if not ANTHROPIC_API_KEY:
        sys.exit("APIキーがありません")
        
    # エラーが起きた書き方を修正しました
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # モデル名を最新のものから順に試します
    model_candidates = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-haiku-20240307"
    ]
    
    prompt = f"""
    日本の中小企業経営者向けに、以下の4項目を網羅した日刊ビジネスレポートをHTMLで作ってください。
    1. 補助金、2. 助成金、3. 融資、4. 税制優遇
    
    ソース:
    {news_text if news_text else "最新ニュースが取得できなかったため、2026年の税制改正トレンドに基づいた専門的なコラムを作成してください。"}
    
    出力は index.html 用のコードのみ。CSSでモダンなデザインにすること。説明不要。
    """
    
    for model_name in model_candidates:
        try:
            print(f"モデル {model_name} を試行中...")
            # 組織IDはヘッダーとして渡す方式に変更（より安全な方法です）
            headers = {"anthropic-organization": ANTHROPIC_ORG_ID} if ANTHROPIC_ORG_ID else {}
            
            message = client.messages.create(
                model=model_name,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                extra_headers=headers
            )
            content = message.content[0].text
            if "```html" in content:
                content = content.split("```html")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return content.strip()
        except Exception as e:
            print(f"モデル {model_name} でエラー: {e}")
            continue
            
    sys.exit("すべてのモデルで失敗しました")

# メイン処理
news_data = get_news()
report_html = generate_report(news_data)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
print("完了！")
