name: weekly-grant-report

on:
  schedule:
    - cron: '0 0 * * 1' # 毎週月曜 日本時間朝9時
  workflow_dispatch: # 手動実行用

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Pythonをセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: 依存関係をインストール
        run: |
          python -m pip install --upgrade pip
          pip install requests anthropic

      - name: レポート生成
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python main.py

      - name: Pagesの設定を構成
        uses: actions/configure-pages@v4

      - name: 生成したHTMLをアップロード
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.' # index.htmlがある場所

      - name: GitHub Pagesにデプロイ
        id: deployment
        uses: actions/deploy-pages@v4
