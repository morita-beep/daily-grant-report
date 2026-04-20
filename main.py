import os
import requests
import anthropic
import sys
import re

def get_clean_api_key():
    # GitHub Secretsから取得
    raw = os.environ.get("ANTHROPIC_API_KEY", "")
    # 改行、空白、目に見えない制御文字をすべて排除
    clean = "".join(c for c in raw.strip() if c.isprintable() and ord(c) < 128)
    # 先頭が sk-ant- で始まっていない場合はエラー
    if not clean.startswith("sk-ant-"):
        print(f"Error: API Key format is invalid. Starts with: {clean[:10]!r}")
        sys.exit(1)
    return clean

def get_available_model(api_key):
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            priority = ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"]
            for p in priority:
                if p in models: return p
            return models[0] if models else "claude-3-5-sonnet-20241022"
    except: pass
    return "claude-3-5-sonnet-20241022"

def generate_report():
    api_key = get_clean_api_key()
    target_model = get_available_model(api_key)
    print(f"Verified Model: {target_model}")
    
    client = anthropic.Anthropic(api_key=api_key)
    prompt = "中小企業経営者向けに、補助金・助成金・融資・税制の最新情報をまとめたレポートを1枚のHTML（CSS込み）で作成してください。</html>で終わるコードのみ出力してください。"

    try:
        message = client.messages.create(
            model=target_model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_content = message.content[0].text
        clean_html = re.sub(r'^.*?<html', '<html', raw_content, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'</html>.*$', '</html>', clean_html, flags=re.DOTALL | re.IGNORECASE)
        return clean_html
    except Exception as e:
        print(f"Final API Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Success: Generated index.html")
