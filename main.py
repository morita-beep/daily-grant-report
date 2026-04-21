import os
import time
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

def get_available_model(api_key):
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            models = [m['id'] for m in response.json().get('data', [])]
            for p in ["claude-haiku-4-5", "claude-3-5-sonnet-20241022", "claude-sonnet-4-5"]:
                if p in models:
                    return p
            return models[0] if models else "claude-haiku-4-5"
    except:
        pass
    return "claude-haiku-4-5"

def search_google(query, api_key, cse_id, num=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": api_key, "cx": cse_id, "num": num, "lr": "lang_ja", "dateRestrict": "m1"}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return [{"title": i.get("title",""), "snippet": i.get("snippet",""), "link": i.get("link","")} for i in response.json().get("items", [])]
        elif response.status_code in [429, 403]:
            print("Google検索上限超過 → Anthropic Web検索に切り替えます")
            return None
    except Exception as e:
        print(f"Google検索エラー: {e}")
    return []

def search_with_anthropic(client, model, query):
    time.sleep(30)  # 15秒待機してレート制限を回避
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": query}]
        )
        result = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result += block.text
        return result
    except Exception as e:
        print(f"Anthropic検索エラー: {e}")
        return ""

def check_google_available(google_api_key, google_cse_id):
    if not google_api_key or not google_cse_id:
        return False
    test = search_google("中小企業 融資", google_api_key, google_cse_id, num=1)
    if test is None:
        return False
    return True

def collect_all_news(client, model, google_available, google_api_key, google_cse_id):
    now = datetime.now()
    year = now.year
    ym = now.strftime("%Y年%m月")
    results = {}

    print("世界情勢・緊急事態を調査中...")
    世界情勢_text = search_with_anthropic(client, model,
        f"現在（{ym}）の世界情勢で日本の中小企業に影響する出来事を調査。戦争・地政学リスク・災害・パンデミック・金融危機・原油価格・為替・サプライチェーンについて、中小企業への影響と対応策を簡潔にまとめてください。")
    results["世界情勢"] = {"mode": "anthropic", "text": 世界情勢_text}

    if google_available:
        print("Google検索モードで各制度情報を取得中...")
        queries = {
            "融資": [
                f"中小企業 緊急融資 資金繰り {ym}",
                f"セーフティネット貸付 {year} 最新",
                "中東情勢 災害 融資 中小企業 緊急支援",
                f"日本政策金融公庫 {year} 新制度",
            ],
            "補助金": [
                f"補助金 公募 中小企業 {ym}",
                f"ものづくり補助金 {year}",
                f"IT導入補助金 {year}",
            ],
            "助成金": [
                f"助成金 中小企業 {ym}",
                f"キャリアアップ助成金 {year}",
                f"雇用調整助成金 {year}",
            ],
            "税制": [
                f"中小企業 税制優遇 {year}",
                f"賃上げ促進税制 {year}",
            ],
        }
        for genre, qs in queries.items():
            items = []
            for q in qs:
                r = search_google(q, google_api_key, google_cse_id, num=3)
                if r:
                    items.extend(r)
                if len(items) >= 6:
                    break
            results[genre] = {"mode": "google", "items": items[:6]}
    else:
        print("Anthropic Web検索モードで各制度情報を取得中...")

        print("融資情報を検索中...")
        融資_text = search_with_anthropic(client, model,
            f"日本の中小企業向け融資制度{ym}最新情報。セーフティネット貸付・日本政策金融公庫・信用保証協会・緊急融資の上限額・金利・対象者・条件を教えてください。")
        results["融資"] = {"mode": "anthropic", "text": 融資_text}

        print("補助金情報を検索中...")
        補助金_text = search_with_anthropic(client, model,
            f"日本の中小企業向け補助金{ym}最新情報。ものづくり補助金・IT導入補助金・持続化補助金・省力化補助金の上限額・補助率・要件を教えてください。")
        results["補助金"] = {"mode": "anthropic", "text": 補助金_text}

        print("助成金情報を検索中...")
        助成金_text = search_with_anthropic(client, model,
            f"日本の中小企業向け助成金{ym}最新情報。キャリアアップ助成金・業務改善助成金・人材開発支援助成金・雇用調整助成金の支給額・要件を教えてください。")
        results["助成金"] = {"mode": "anthropic", "text": 助成金_text}

        print("税制情報を検索中...")
        税制_text = search_with_anthropic(client, model,
            f"日本の中小企業向け税制優遇{ym}最新情報。賃上げ促進税制・経営強化税制・研究開発税制・投資促進税制の控除率・要件・期限を教えてください。")
        results["税制"] = {"mode": "anthropic", "text": 税制_text}

    return results

def make_html_section(data):
    if data["mode"] == "google":
        items = data.get("items", [])
        if not items:
            return "<p style='color:#888;'>該当する新着情報がありませんでした。</p>"
        html = ""
        for item in items:
            html += f"""<div style='border:1px solid #dde3f0;border-radius:6px;padding:14px;margin-bottom:12px;background:#fafbff;'>
<div style='font-weight:bold;color:#0d1b4b;margin-bottom:6px;'>{item['title']}</div>
<div style='font-size:0.88rem;color:#555;margin-bottom:8px;line-height:1.6;'>{item['snippet']}</div>
<a href='{item['link']}' target='_blank' style='font-size:0.82rem;color:#2563eb;'>詳細を見る →</a>
</div>"""
        return html
    else:
        text = data.get("text", "")
        if not text:
            return "<p style='color:#888;'>情報を取得できませんでした。</p>"
        html = ""
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('###'):
                line = line.lstrip('#').strip()
                html += f"<h4 style='color:#0d1b4b;margin:14px 0 6px;font-size:0.95rem;'>{line}</h4>"
            elif line.startswith('##') or line.startswith('#'):
                line = line.lstrip('#').strip()
                html += f"<h3 style='color:#0d1b4b;margin:16px 0 8px;font-size:1rem;border-left:3px solid #0d1b4b;padding-left:8px;'>{line}</h3>"
            elif line.startswith(('・','•','-','*')):
                html += f"<div style='padding:4px 0 4px 16px;font-size:0.9rem;color:#444;line-height:1.6;'>{line}</div>"
            elif line.startswith('**'):
                line = line.replace('**','').strip()
                html += f"<div style='font-weight:bold;color:#0d1b4b;margin:10px 0 4px;'>{line}</div>"
            else:
                html += f"<p style='font-size:0.9rem;color:#444;line-height:1.7;margin-bottom:8px;'>{line}</p>"
        return html

def generate_report():
    api_key = get_clean_api_key()
    target_model = get_available_model(api_key)
    print(f"使用モデル: {target_model}")

    client = anthropic.Anthropic(api_key=api_key)
    today_str = datetime.now().strftime("%Y年%m月%d日")

    google_api_key = os.environ.get("GOOGLE_API_KEY", "")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID", "")

    # Google上限超過のため強制的にAnthropicモード
    google_available = False
    search_mode = "AI Web検索"
    print(f"検索モード: {search_mode}")

    news = collect_all_news(client, target_model, google_available, google_api_key, google_cse_id)

    世界情勢_html = make_html_section(news.get("世界情勢", {"mode":"anthropic","text":""}))
    融資_html = make_html_section(news.get("融資", {"mode":"anthropic","text":""}))
    補助金_html = make_html_section(news.get("補助金", {"mode":"anthropic","text":""}))
    助成金_html = make_html_section(news.get("助成金", {"mode":"anthropic","text":""}))
    税制_html = make_html_section(news.get("税制", {"mode":"anthropic","text":""}))

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
.em{{background:#fff0f0;border:2px solid #e53e3e;border-radius:8px;padding:14px 18px;margin:0 auto 16px;max-width:960px;font-size:0.9rem;line-height:1.6;}}
.et{{color:#e53e3e;font-weight:bold;margin-bottom:6px;}}
.sm{{background:#e8f4f8;border:1px solid #bee3f8;border-radius:4px;padding:4px 10px;font-size:0.75rem;color:#2c5282;display:inline-block;margin-bottom:12px;}}
.tabs{{max-width:960px;margin:0 auto;display:flex;gap:4px;flex-wrap:wrap;padding:0 4px;}}
.tb{{background:#dde3f0;border:none;padding:10px 16px;border-radius:6px 6px 0 0;cursor:pointer;font-size:0.85rem;color:#555;}}
.tb.active{{background:#0d1b4b;color:white;}}
.tc{{display:none;max-width:960px;margin:0 auto 30px;background:white;border-radius:0 8px 8px 8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.tc h2{{font-size:1.2rem;color:#0d1b4b;border-left:4px solid #0d1b4b;padding-left:10px;margin-bottom:18px;}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}}
.ss{{background:#f0f4ff;border-radius:6px;padding:14px;}}
.ss h3{{color:#0d1b4b;font-size:0.95rem;margin-bottom:8px;}}
.ab{{background:#f0f4ff;border-radius:6px;padding:16px;margin-bottom:14px;}}
.ab h3{{color:#0d1b4b;margin-bottom:8px;}}
.ab ul{{padding-left:18px;line-height:1.8;font-size:0.9rem;}}
.world-alert{{background:#fff3cd;border:2px solid #f39c12;border-radius:8px;padding:16px;margin-bottom:16px;}}
.world-alert-title{{color:#856404;font-weight:bold;margin-bottom:8px;font-size:1rem;}}
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
    <input type="text" id="qi" placeholder="制度名・状況を入力（例：ものづくり補助金、パンデミック時の融資）">
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
  <button class="tb" id="b1" onclick="st(1)">①サマリー</button>
  <button class="tb" id="b2" onclick="st(2)">🌍世界情勢</button>
  <button class="tb" id="b3" onclick="st(3)">②融資（最重要）</button>
  <button class="tb" id="b4" onclick="st(4)">③補助金</button>
  <button class="tb" id="b5" onclick="st(5)">④助成金</button>
  <button class="tb" id="b6" onclick="st(6)">⑤税制</button>
  <button class="tb" id="b7" onclick="st(7)">⑥提言</button>
</div>

<div class="tc" id="t1">
  <h2>エグゼクティブサマリー</h2>
  <div class="sm">🤖 検索モード：{search_mode}</div>
  <div class="sg">
    <div class="ss"><h3>🏦 融資（最重要）</h3>中東情勢対応のセーフティネット貸付要件緩和中。日本政策金融公庫・信用保証協会が対応。上限4,800万円。</div>
    <div class="ss"><h3>💰 補助金</h3>ものづくり補助金（上限4,000万円）・IT導入補助金（上限450万円）・小規模事業者持続化補助金（上限250万円）が公募中。</div>
    <div class="ss"><h3>👥 助成金</h3>キャリアアップ助成金（57万円〜）・業務改善助成金（最大600万円）・人材開発支援助成金（経費45〜75%）が活用可能。</div>
    <div class="ss"><h3>📊 税制</h3>賃上げ促進税制（最大45%控除）・中小企業経営強化税制（即時償却）・研究開発税制（最大17%控除）が適用可能。</div>
  </div>
</div>

<div class="tc" id="t2">
  <h2>🌍 世界情勢・リスク分析</h2>
  <div class="world-alert">
    <div class="world-alert-title">⚡ 中小企業に影響する世界情勢（{today_str}時点）</div>
    {世界情勢_html}
  </div>
</div>

<div class="tc" id="t3">
  <h2>🏦 融資・資金繰り支援（最重要）</h2>
  {融資_html}
</div>

<div class="tc" id="t4">
  <h2>💰 補助金</h2>
  {補助金_html}
</div>

<div class="tc" id="t5">
  <h2>👥 助成金</h2>
  {助成金_html}
</div>

<div class="tc" id="t6">
  <h2>📊 税制優遇</h2>
  {税制_html}
</div>

<div class="tc" id="t7">
  <h2>💼 コンサルティング提言</h2>
  <div class="ab">
    <h3>🚨 世界情勢を踏まえた緊急対応</h3>
    <ul>
      <li>地政学リスク・原油高騰の影響を受けている顧客 → セーフティネット貸付（要件緩和中）を即座に提案</li>
      <li>サプライチェーン混乱の顧客 → 緊急融資＋事業継続計画（BCP）の策定を支援</li>
      <li>為替変動の影響を受けている顧客 → 為替リスクヘッジ＋運転資金融資を提案</li>
      <li>パンデミック・災害リスクに備える顧客 → 雇用調整助成金の事前確認を推奨</li>
    </ul>
  </div>
  <div class="ab">
    <h3>📋 今月の重点提案項目</h3>
    <ul>
      <li>賃上げ実施予定の顧客 → 賃上げ促進税制＋キャリアアップ助成金を同時提案</li>
      <li>IT化・DX推進の顧客 → IT導入補助金＋経営強化税制の併用</li>
      <li>設備投資を検討中の顧客 → ものづくり補助金＋経営強化税制の併用を検討</li>
      <li>採用・人材育成の顧客 → 人材開発支援助成金＋両立支援助成金を確認</li>
    </ul>
  </div>
  <div class="ab">
    <h3>🌍 世界情勢別・緊急支援制度早見表</h3>
    <ul>
      <li>【戦争・地政学リスク】セーフティネット貸付・緊急経営安定化特別融資</li>
      <li>【パンデミック】雇用調整助成金・無利子無担保融資・持続化給付金（発動時）</li>
      <li>【自然災害】災害復旧貸付・激甚災害指定補助金・被災者雇用開発助成金</li>
      <li>【経済危機・恐慌】セーフティネット保証・経営改善計画策定支援（405事業）</li>
      <li>【原油・原材料高騰】業務改善助成金・省エネ補助金・価格転嫁対策</li>
    </ul>
  </div>
  <div class="ab">
    <h3>⚠️ 注意事項</h3>
    <ul>
      <li>本レポートの情報は{today_str}時点のものです</li>
      <li>申請要件・金額は変更される場合があります。必ず公式サイトで最新情報を確認してください</li>
      <li>緊急時の特別措置は状況により随時変更されます。速報性の高い情報収集を推奨します</li>
    </ul>
  </div>
</div>

<script>
function st(n){{
  for(var i=1;i<=7;i++){{
    document.getElementById('t'+i).style.display='none';
    document.getElementById('b'+i).classList.remove('active');
  }}
  document.getElementById('t'+n).style.display='block';
  document.getElementById('b'+n).classList.add('active');
}}
document.addEventListener('DOMContentLoaded',function(){{st(1);}});
async function askAI(){{
  var q=document.getElementById('qi').value.trim();
  if(!q){{alert('制度名または状況を入力してください');return;}}
  var el=document.getElementById('result');
  el.style.display='block';
  el.textContent='AIが調査中...';
  try{{
    var r=await fetch('https://api.anthropic.com/v1/messages',{{
      method:'POST',
      headers:{{'Content-Type':'application/json','x-api-key':'{api_key}','anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'}},
      body:JSON.stringify({{model:'{target_model}',max_tokens:1500,messages:[{{role:'user',content:'中小企業の財務コンサルタントとして、次の質問に詳しく答えてください。世界情勢（戦争・災害・パンデミック・経済危機等）も考慮した上で、活用できる融資・補助金・助成金・税制優遇を具体的に教えてください: '+q}}]}})
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
