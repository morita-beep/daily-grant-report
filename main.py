import os
import anthropic
import sys

# 名前を間違えないよう、直接環境変数から取得
key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

def run():
    print("--- 最終テスト開始 ---")
    client = anthropic.Anthropic(api_key=key)
    
    # Tier 1 なので、本来ならどれでも動きます。
    # 最も確実に存在する 3.5 Sonnet を「一発勝負」で指定します。
    try:
        print("モデル: claude-3-5-sonnet-20241022 で実行中...")
        res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": "補助金・助成金・融資・税制について、中小企業向けの日刊レポートをHTMLで作ってください。説明不要。"}]
        )
        print("【大成功】AIが応答しました！")
        return res.content[0].text
    except Exception as e:
        print(f"【エラー発生】: {e}")
        sys.exit(1)

# 保存
content = run()
with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("完了しました。GitHub Pagesを確認してください。")
