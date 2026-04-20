import os
import requests
import anthropic
import sys
import re

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

def get_available_model():
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            priority = ["claude-sonnet-4-6", "claude-opus-4-7", "claude-3-5-sonnet-20241022"]
            for p in priority:
                if p in models: return p
            return models[0] if models else "claude-3-5-sonnet-20241022"
    except: pass
    return "claude-3-5-sonnet-20241022"

def generate_report():
    target_model = get_available_model()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = "日本の中小企業経営者向けに、1.補助金 2.助成金 3.融資 4.税制優遇の最新情報をまとめた週刊レポートを、1枚の完成されたHTML（CSS込み）で作成してください。出力は<html>から始まるHTMLコードのみにしてください。説明や```記号は一切不要です。"

    try:
        message = client.messages.create(
            model=target_model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_content = message.content[0].text
        
        # HTML以外の余計な装飾（```html など）を力技で消去する
        clean_html = re.sub(r'^.*?<html', '<html', raw_content, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'</html>.*$', '</html>', clean_html, flags=re.DOTALL | re.IGNORECASE)
        
        return clean_html
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

# 保存
html_content = generate_report()
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
