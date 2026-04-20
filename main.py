import os
import requests
import anthropic
import sys
import re

# キーを読み込み、余計な文字（BOMや空白）を完全に除去
raw_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_API_KEY = ''.join(c for c in raw_key if c.isprintable() and ord(c) < 128)

def get_available_model():
    # 自分のキーで今「本当に」使えるモデル一覧を公式から取得する
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            # Sonnet系を優先、なければ何でもいいからリストの最初を使う
            priority = ["claude-sonnet-4-6", "claude-3-5-sonnet-20241022"]
            for p in priority:
                if p in models: return p
            return models[0] if models else "claude-3-5-sonnet-20241022"
    except:
        pass
    # 万が一取得失敗した時のフォールバック
    return "claude-3-5-sonnet-20241022"

def generate_report():
    if not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        print(f"Error: Invalid API Key format. Starts with: {ANTHROPIC_API_KEY[:10]}")
        sys.exit(1)

    target_model = get_available_model()
    print(f"Using model: {target_model}")
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
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
        print(f"API Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
