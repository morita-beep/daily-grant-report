import os
import requests
from anthropic import Anthropic
import sys

# 設定
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def get_news():
    print("--- Google検索を開始します ---")
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q=融資+補助金+最新+ニュース"
    try:
        response = requests.get(url)
        response.raise_for_status()
        items = response.json().get("items", [])
        print(f"検索成功: {len(items)}件の記事を見つけました")
        text = ""
        for item in items:
            text += f"タイトル: {item['title']}\nリンク: {item['link']}\n概要: {item['snippet']}\n\n"
        return text
    except Exception as e:
        print(f"【Google検索エラー】: {e}")
        return None

def generate_report(news_text):
    print("--- Claudeによるレポート生成を開始します ---")
    if not news_text:
        return "ニュースが取得できませんでした。"
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        # どのティアでも確実に使える「haiku」モデルでテストします
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": f"以下の最新ニュースを元に、経営者向けの補助金・融資レポートをHTML形式で出力してください。説明文は不要です。\n\n{news_text}"}]
        )
        print("レポート作成に成功しました！")
        return message.content[0].text
    except Exception as e:
        print(f"【Anthropic APIエラー】: {e}")
        print("※APIキーが正しいか、クレジット残高があるか確認してください。")
        sys.exit(1)

# メイン処理
try:
    news = get_news()
    html_content = generate_report(news)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("すべての処理が正常に完了しました。")
except Exception as e:
    print(f"予期せぬエラー: {e}")
    sys.exit(1)
