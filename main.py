import os
import requests
from anthropic import Anthropic
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
        return "検索設定が不完全です。"
    
    # 補助金、助成金、融資、税制の4本柱で検索
    query = "補助金 助成金 融資 税制優遇 最新 2026"
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}&hl=ja"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if "error" in data:
            print(f"Google APIエラー: {data['error'].get('message')}")
            return None
        items = data.get("items", [])
        return "".join([f"【{i['title']}】\n{i['link']}\n{i['snippet']}\n\n" for i in items])
    except:
        return None

def generate_report(news_text):
    print("--- Claudeレポート生成開始 ---")
    if not ANTHROPIC_API_KEY:
        sys.exit("ANTHROPIC_API_KEYが設定されていません。")
        
    # 登録したばかりの組織IDを指定して接続
    client = Anthropic(
        api_key=ANTHROPIC_API_KEY,
        organization_id=ANTHROPIC_ORG_ID
    )
    
    # 2026年時点で確実に動作するモデル候補
    model_candidates = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-haiku-20240307"
    ]
    
    prompt = f"""
    日本の中小企業経営者向けに、以下の4項目を網羅した日刊ビジネスレポートをHTMLで作ってください。
    1. 補助金、2. 助成金、3. 融資、4. 税制優遇
    
    【ニュースソース】
    {news_text if news_text else "最新ニュースが取得できなかったため、2026年の税制改正や一般的な資金繰りアドバイスを記述してください。"}
    
    出力は index.html 用のコードのみ。CSSでプロフェッショナルなデザインにすること。説明文は不要です。
    """
    
    for model_name in model_candidates:
        try:
            print(f"モデル {model_name} を試行中...")
            message = client.messages.create(
                model=model_name,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
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
            
    print("全モデルで失敗。残高があるのにエラーが出る場合はAPIキー自体の権限を確認してください。")
    sys.exit(1)

# メイン処理
news_data = get_news()
report_html = generate_report(news_data)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
print("完了！")
