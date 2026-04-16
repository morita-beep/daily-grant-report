import os
import requests
from anthropic import Anthropic
import sys

# 名前が1文字でも違うとダメなので、すべての可能性をチェックします
def get_env(key):
    val = os.environ.get(key)
    if not val:
        # 末尾にスペースが入っているケースなども考慮
        for k, v in os.environ.items():
            if k.strip() == key:
                return v
    return val

GOOGLE_API_KEY = get_env("GOOGLE_API_KEY")
GOOGLE_CSE_ID = get_env("GOOGLE_CSE_ID")
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")

def get_news():
    print("--- 検索開始 ---")
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("設定エラー: Googleの鍵またはIDが設定されていません")
        return None
        
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q=補助金+最新&hl=ja"
    
    try:
        response = requests.get(url)
        data = response.json()
        if "error" in data:
            print(f"Google APIエラー詳細: {data['error'].get('message')}")
            # もしGoogleがダメでも、AIに一般情報を書かせるためにNoneを返して続行します
            return None
        return "".join([f"タイトル:{i['title']}\nURL:{i['link']}\n" for i in data.get("items", [])])
    except:
        return None

def generate_report(news_text):
    print("--- レポート作成開始 ---")
    if not ANTHROPIC_API_KEY:
        print("設定エラー: Anthropicの鍵が設定されていません")
        sys.exit(1)
        
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # モデルが見つからないエラーを防ぐため、一番確実な3.5 Sonnet（最新）と3.0の両方を試みる構造にします
    models = ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"]
    
    for model_name in models:
        try:
            print(f"モデル {model_name} で試行中...")
            message = client.messages.create(
                model=model_name,
                max_tokens=3000,
                messages=[{"role": "user", "content": f"最新の補助金ニュースレポートをHTMLで作ってください。ニュースが空なら一般的なアドバイスを。HTMLのみ出力せよ。\n\n{news_text}"}]
            )
            content = message.content[0].text
            if "```html" in content:
                content = content.split("```html")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return content.strip()
        except Exception as e:
            print(f"モデル {model_name} が失敗: {e}")
            continue
    
    print("すべてのモデルで失敗しました")
    sys.exit(1)

# メイン処理
news = get_news()
html_content = generate_report(news)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("完了")
