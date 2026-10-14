name: FRED daily
on:
  push:
  workflow_dispatch:
  schedule:
    - cron: '0 21 * * *'
permissions:
  contents: write
concurrency:
  group: fred-relay
  cancel-in-progress: false
jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Fetch FRED
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: python fetch.py
      - name: Fetch FRED bo sung (Ban tin thuc chien)
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: python fetch_ext.py || echo "fred_ext loi - bo qua"
      - name: Fetch World Bank
        run: python fetch_wb.py
      - name: Commit
        run: |
          git config user.name "fred-bot"
          git config user.email "fred-bot@users.noreply.github.com"
          git add docs/
          git commit -m "update fred.json + wb.json" || { echo "no change"; exit 0; }
          for i in 1 2 3; do
            git pull --rebase -X theirs origin main && git push && exit 0
            git rebase --abort 2>/dev/null || true
            sleep 10
          done
          exit 1
