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
    # 検索ワードを広げ、かつ日本語の検索結果を優先します
    query = "補助金 融資 助成金 中小企業 最新 2026"
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}&hl=ja"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            print(f"Google APIエラー: {data['error']['message']}")
            return None
            
        items = data.get("items", [])
        if not items:
            return None
            
        text = ""
        for item in items:
            text += f"タイトル: {item['title']}\nURL: {item['link']}\n概要: {item['snippet']}\n\n"
        return text
    except Exception as e:
        print(f"通信エラー: {e}")
        return None

def generate_report(news_text):
    print("--- Claudeによるレポート生成を開始します ---")
    
    # ニュース内容に応じたプロンプト
    prompt_content = f"""
    あなたは優秀な経営コンサルタントです。
    以下の最新ニュースをもとに、中小企業の経営者が今すぐ役立てられる「日刊・補助金融資レポート」を作成してください。

    【ニュース内容】
    {news_text if news_text else "最新ニュースは取得されませんでしたが、現在の日本の一般的な補助金・融資のトレンドに基づいたアドバイスを作成してください。"}

    【出力条件】
    1. HTMLファイル(index.html)として出力してください。
    2. CSSを使用して、モダンで高級感のあるデザインにしてください（ダークモード対応や青系の配色が好ましい）。
    3. 各ニュースには必ず元記事へのリンクを貼ってください。
    4. 「今、経営者が取るべきアクション」という項目を最後に含めてください。
    5. HTMLコード（<!DOCTYPE html>から始まる）のみを出力し、前後の説明文は一切不要です。
    """
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        # ご指定の最新モデルを使用
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt_content}]
        )
        content = message.content[0].text
        # 余計なマークダウン記号を除去
        if "```html" in content:
            content = content.split("```html")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return content.strip()
    except Exception as e:
        print(f"Anthropicエラー: {e}")
        sys.exit(1)

# 実行
news = get_news()
html_content = generate_report(news)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("完了しました。")
