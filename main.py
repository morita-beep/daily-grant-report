import os
import requests
import anthropic
import sys
from datetime import datetime

def get_clean_api_key():
    raw = os.environ.get("ANTHROPIC_API_KEY", "")
    clean = "".join(c for c in raw.strip() if c.isprintable() and ord(c) < 128)
    if not clean.startswith("sk-ant-"):
        print(f"Error: {clean[:10]!r}")
        sys.exit(1)
    return clean

def search_google(query, api_key, cse_id, num=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": api_key, "cx": cse_id, "num": num, "lr": "lang_ja", "dateRestrict": "m1"}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return [{"title": i.get("title",""), "snippet": i.get("snippet",""), "link": i.get("link","")}
                    for i in response.json().get("items", [])]
    except Exception as e:
        print(f"検索エラー: {e}")
    return []

def collect_latest_news():
    google_api_key = os.environ.get("GOOGLE_API_KEY", "")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID", "")
    if not google_api_key or not google_cse_id:
        print("警告: Google APIキーが未設定")
        return {}
    now = datetime.now()
    year = now.year
    ym = now.strftime("%Y年%m月")
    queries = {
        "融資": [
            f"中小企業 緊急融資 資金繰り {ym}",
            f"セーフティネット貸付 最新 {year}",
            f"日本政策金融公庫 新制度 {year}",
            "中東情勢 中小企業 融資 支援 最新",
            f"信用保証協会 保証制度 {year}",
        ],
        "補助金": [
            f"補助金 公募開始 中小企業 {ym}",
            f"ものづくり補助金 {year} 最新",
            f"IT導入補助金 {year} 申請",
            f"事業再構築補助金 {year}",
            f"小規模事業者持続化補助金 {year}",
        ],
        "助成金": [
            f"助成金 中小企業 {ym} 新設",
            f"キャリアアップ助成金 {year} 要件",
            f"業務改善助成金 {year}",
            f"人材開発支援助成金 {year}",
        ],
        "税制": [
            f"中小企業 税制改正 {year}",
            f"賃上げ促進税制 {year} 要件",
            f"中小企業経営強化税制 {year}",
            f"研究開発税制 中小企業 {year}",
        ],
    }
    results = {}
    for genre, qs in queries.items():
        genre_news = []
        for q in qs:
            items = search_google(q, google_api_key, google_cse_id, num=5)
            genre_news.extend(items)
            if len(genre_news) >= 10:
                break
        results[genre] = genre_news[:10]
    return results

def get_available_model(api_key):
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            for p in ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-3-5-sonnet-20241022"]:
                if p in models:
                    return p
            return models[0] if models else "claude-haiku-4-5"
    except:
        pass
    return "claude-haiku-4-5"

def make_cards(items):
    if not items:
        return "<p style='color:#888;'>本日は該当する新着情報がありませんでした。</p>"
    html = ""
    for item in items:
        html += f"""<div style='border:1px solid #dde3f0;border-radius:6px;padding:14px;margin-bottom:12px;background:#fafbff;'>
<div style='font-weight:bold;color:#0d1b4b;margin-bottom:6px;'>{item['title']}</div>
<div style='font-size:0.88rem;color:#555;margin-bottom:8px;line-height:1.6;'>{item['snippet']}</div>
<a href='{item['link']}' target='_blank' style='font-size:0.82rem;color:#2563eb;'>詳細を見る →</a>
</div>"""
    return html

def generate_report():
    api_key = get_clean_api_key()
    target_model = get_available_model(api_key)
    print(f"使用モデル: {target_model}")
    news_dict = collect_latest_news()
    today_str = datetime.now().strftime("%Y年%m月%d日")

    融資_html = make_cards(news_dict.get("融資", []))
    補助金_html = make_cards(news_dict.get("補助金", []))
    助成金_html = make_cards(news_dict.get("助成金", []))
    税制_html = make_cards(news_dict.get("税制", []))

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>株式会社HONEST 支援制度レポート</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:Arial,sans-serif;background:#f0f2f5;color:#333;}}
header{{background:#0d1b4b;color:white;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;}}
.hl{{display:flex;align-items:center;gap:14px;}}
header img{{height:56px;}}
header h1{{font-size:1.4rem;}}
.db{{background:white;color:#0d1b4b;padding:6px 14px;border-radius:4px;font-size:0.85rem;font-weight:bold;}}
.sb{{background:white;margin:20px auto;max-width:960px;border-radius:8px;padding:20px 24px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.sb h2{{font-size:1rem;margin-bottom:12px;color:#0d1b4b;}}
.sr{{display:flex;gap:10px;}}
.sr input{{flex:1;padding:10px 14px;border:1px solid #ccc;border-radius:4px;font-size:0.95rem;}}
.sr button{{background:#0d1b4b;color:white;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;font-size:0.95rem;}}
#result{{margin-top:14px;padding:14px;background:#f8f9ff;border-left:4px solid #0d1b4b;border-radius:4px;display:none;white-space:pre-wrap;line-height:1.7;font-size:0.9rem;}}
.em{{background:#fff0f0;border:2px solid #e53e3e;border-radius:8px;padding:14px 18px;margin:0 auto 16px;max-width:960px;}}
.et{{color:#e53e3e;font-weight:bold;margin-bottom:6px;}}
.tabs{{max-width:960px;margin:0 auto;display:flex;gap:4px;flex-wrap:wrap;padding:0 4px;}}
.tb{{background:#dde3f0;border:none;padding:10px 18px;border-radius:6px 6px 0 0;cursor:pointer;font-size:0.88rem;color:#555;}}
.tb.active{{background:#0d1b4b;color:white;}}
.tc{{display:none;max-width:960px;margin:0 auto 30px;background:white;border-radius:0 8px 8px 8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.tc h2{{font-size:1.2rem;color:#0d1b4b;border-left:4px solid #0d1b4b;padding-left:10px;margin-bottom:18px;}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}}
.ss{{background:#f0f4ff;border-radius:6px;padding:14px;}}
.ss h3{{color:#0d1b4b;font-size:0.95rem;margin-bottom:8px;}}
.ab{{background:#f0f4ff;border-radius:6px;padding:16px;margin-bottom:14px;}}
.ab h3{{color:#0d1b4b;margin-bottom:8px;}}
.ab ul{{padding-left:18px;line-height:1.8;font-size:0.9rem;}}
</style>
</head>
<body>
<header>
  <div class="hl">
    <img src="rogo.png" alt="HONEST">
    <h1>株式会社HONEST</h1>
  </div>
  <div class="db">{today_str}時点の情報</div>
</header>

<div class="sb">
  <h2>🔍 AI制度検索</h2>
  <div class="sr">
    <input type="text" id="qi" placeholder="制度名を入力して検索（例：ものづくり補助金）">
    <button onclick="askAI()">AIに質問する</button>
  </div>
  <div id="result"></div>
</div>

<div class="em">
  <div class="et">⚠️ 緊急情報：中東情勢による中小企業支援</div>
  中小企業庁は中東情勢・原油価格高騰の影響を受ける事業者向けにセーフティネット貸付の要件を緩和。
  売上減少の数値要件なしでも資金繰りに支障がある場合は融資対象。（2026年3月27日発表）
  相談窓口：日本政策金融公庫 / 信用保証協会 / 各都道府県窓口
</div>

<div class="tabs">
  <button class="tb" id="b1" onclick="st(1)">①エグゼクティブサマリー</button>
  <button class="tb" id="b2" onclick="st(2)">②融資（最重要）</button>
  <button class="tb" id="b3" onclick="st(3)">③補助金</button>
  <button class="tb" id="b4" onclick="st(4)">④助成金</button>
  <button class="tb" id="b5" onclick="st(5)">⑤税制</button>
  <button class="tb" id="b6" onclick="st(6)">⑥コンサルティング提言</button>
</div>

<div class="tc" id="t1">
  <h2>エグゼクティブサマリー</h2>
  <div class="sg">
    <div class="ss"><h3>🏦 融資（最重要）</h3>中東情勢対応のセーフティネット貸付要件緩和中。日本政策金融公庫・信用保証協会が対応。上限4,800万円。</div>
    <div class="ss"><h3>💰 補助金</h3>ものづくり補助金（上限4,000万円）・IT導入補助金（上限450万円）・小規模事業者持続化補助金（上限250万円）が公募中。</div>
    <div class="ss"><h3>👥 助成金</h3>キャリアアップ助成金（57万円〜）・業務改善助成金（最大600万円）・人材開発支援助成金（経費45〜75%）が活用可能。</div>
    <div class="ss"><h3>📊 税制</h3>賃上げ促進税制（最大45%控除）・中小企業経営強化税制（即時償却）・研究開発税制（最大17%控除）が適用可能。</div>
  </div>
</div>

<div class="tc" id="t2">
  <h2>🏦 融資・資金繰り支援（最重要）</h2>
  {融資_html}
</div>

<div class="tc" id="t3">
  <h2>💰 補助金</h2>
  {補助金_html}
</div>

<div class="tc" id="t4">
  <h2>👥 助成金</h2>
  {助成金_html}
</div>

<div class="tc" id="t5">
  <h2>📊 税制優遇</h2>
  {税制_html}
</div>

<div class="tc" id="t6">
  <h2>💼 コンサルティング提言</h2>
  <div class="ab">
    <h3>🚨 今すぐ確認すべき案件</h3>
    <ul>
      <li>中東情勢の影響を受けている顧客 → セーフティネット貸付（要件緩和中）を即座に提案</li>
      <li>原材料・エネルギーコスト上昇の顧客 → 業務改善助成金と組み合わせて提案</li>
      <li>設備投資を検討中の顧客 → ものづくり補助金＋経営強化税制の併用を検討</li>
    </ul>
  </div>
  <div class="ab">
    <h3>📋 今月の重点提案項目</h3>
    <ul>
      <li>賃上げ実施予定の顧客 → 賃上げ促進税制＋キャリアアップ助成金を同時提案</li>
      <li>IT化・DX推進の顧客 → IT導入補助金＋経営強化税制（ソフトウェア）の併用</li>
      <li>採用・人材育成の顧客 → 人材開発支援助成金＋両立支援助成金を確認</li>
    </ul>
  </div>
  <div class="ab">
    <h3>⚠️ 注意事項</h3>
    <ul>
      <li>本レポートの情報は{today_str}時点のものです</li>
      <li>申請要件・金額は変更される場合があります。必ず公式サイトで最新情報を確認してください</li>
      <li>補助金・助成金は原則として事前申請が必要です</li>
    </ul>
  </div>
</div>

<script>
function st(n) {{
  for(var i=1;i<=6;i++){{
    document.getElementById('t'+i).style.display='none';
    document.getElementById('b'+i).classList.remove('active');
  }}
  document.getElementById('t'+n).style.display='block';
  document.getElementById('b'+n).classList.add('active');
}}
document.addEventListener('DOMContentLoaded',function(){{st(1);}});
async function askAI(){{
  var q=document.getElementById('qi').value.trim();
  if(!q){{alert('制度名を入力してください');return;}}
  var el=document.getElementById('result');
  el.style.display='block';
  el.textContent='AIが調査中...';
  try{{
    var r=await fetch('https://api.anthropic.com/v1/messages',{{
      method:'POST',
      headers:{{'Content-Type':'application/json','x-api-key':'{api_key}','anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'}},
      body:JSON.stringify({{model:'{target_model}',max_tokens:1000,messages:[{{role:'user',content:'中小企業の財務コンサルタントとして、次の制度について詳しく教えてください。対象者・金額・申請条件・注意点・申請窓口を箇条書きで: '+q}}]}})
    }});
    var d=await r.json();
    el.textContent=d.content&&d.content[0]?d.content[0].text:'回答を取得できませんでした。';
  }}catch(e){{el.textContent='エラー: '+e.message;}}
}}
</script>
</body>
</html>"""
    return html

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"完了: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} にindex.htmlを生成")
