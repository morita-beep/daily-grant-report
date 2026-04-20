import os
import requests
import anthropic
import sys

# 鍵の読み込み
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

def get_available_model():
    print("--- 利用可能モデルの確認 ---")
    # 直接APIを叩いて、今この鍵で見えているモデルの一覧を取得します
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            print(f"発見されたモデル: {models}")
            # 2026年の推奨順に候補を並べ、リストにあるものを採用
            priority = ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5-20251001", "claude-3-7-sonnet-latest"]
            for p in priority:
                if p in models:
                    return p
            return models[0] if models else None
    except Exception as e:
        print(f"モデル一覧の取得に失敗: {e}")
    # 取得失敗時の最終フォールバック
    return "claude-sonnet-4-6"

def generate_report():
    print("--- レポート生成プロセス開始 ---")
    if not ANTHROPIC_API_KEY:
        sys.exit("APIキーが設定されていません。")

    # 1. 今使えるモデルを特定
    target_model = get_available_model()
    print(f"使用決定モデル: {target_model}")

    # 2. クライアント作成（組織ID指定なしの最小構成）
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = """
    日本の中小企業経営者向けに、以下の4ジャンルを網羅した日刊レポートをHTMLで作成してください。
    1.補助金 2.助成金 3.融資 4.税制優遇
    2026年の最新トレンドに基づき、専門的かつ読みやすいコラム形式にしてください。
    出力は index.html 用のコードのみ。CSSで高級感を出してください。
    """

    try:
        message = client.messages.create(
            model=target_model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        # 余計な装飾を除去
        if "```html" in content:
            content = content.split("```html")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return content.strip()
    except Exception as e:
        print(f"レポート生成エラー: {e}")
        sys.exit(1)

# 実行と保存
html_content = generate_report()
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("完了しました！GitHub Pagesを確認してください。")
