import os
import requests
from anthropic import Anthropic

# 設定
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

def get_news():
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q=融資+補助金+最新+ニュース"
    response = requests.get(url).json()
    items = response.get("items", [])
    text = ""
    for item in items:
        text += f"タイトル: {item['title']}\nリンク: {item['link']}\n概要: {item['snippet']}\n\n"
    return text

def generate_report(news_text):
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4000,
        messages=[{"role": "user", "content": f"以下の最新ニュースを元に、経営者向けの補助金・融資レポートを美しいHTML（index.html）として出力してください。ダッシュボード形式を希望します。スタイルはCSSでモダンに整えてください。なお、HTMLコードのみを出力し、説明文は不要です。\n\n{news_text}"}]
    )
    return message.content[0].text

# 実行
news = get_news()
html_content = generate_report(news)

# 保存
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
