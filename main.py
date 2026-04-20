import os
import requests
import anthropic
import sys
import re

# GitHubのSecretsからAPIキーを取得
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

def get_available_model():
    # 最も多くのアカウントで初期から解放されている標準モデルを指定
    return "claude-3-sonnet-20240229"

def generate_report():
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # AIへの指示（プロンプト）
    prompt = (
        "日本の中小企業経営者向けに、以下の4項目について今週の最新情報をまとめた「週刊 資金調達・優遇制度レポート」を作成してください。\n"
        "1. 注目すべき補助金\n"
        "2. 活用したい助成金\n"
        "3. 最新の融資・金融支援情報\n"
        "4. 節税・税制優遇措置\n\n"
        "【出力形式の指示】\n"
        "・1枚の完成されたHTML（CSSによるデザイン込み）で出力してください。\n"
        "・高級感のあるビジネス向けのデザイン（紺色やゴールドを基調）にしてください。\n"
        "・出力は <html> から始まるコードのみとし、前後の説明文や ``` 記号は一切含めないでください。"
    )

    try:
        message = client.messages.create(
            model=get_available_model(),
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_content = message.content[0].text
        
        # 不要な記号（```htmlなど）を削除してHTML部分だけを抽出する
        clean_html = re.sub(r'^.*?<html', '<html', raw_content, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'</html>.*$', '</html>', clean_html, flags=re.DOTALL | re.IGNORECASE)
        
        return clean_html
    except Exception as e:
        print(f"API Error: {e}")
        sys.exit(1)

# 生成した内容を index.html として書き出し
if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Successfully generated index.html")
