"""
Horse Racing Analysis System - Multi-Race Version
1日分（1〜12R）を一括処理してフォルダに集約

修正内容:
  - get_kaisai_day: race_idから直接開催日番号を安定取得
  - 含水率・クッション値をJRAサイトから自動取得
  - 芝・ダート含水率を自動切り替え
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import os, time, re, platform
from datetime import datetime

# ============================================================
# 定数
# ============================================================
VENUE_CODE = {
    '東京':'05','中山':'06','京都':'08','阪神':'09',
    '中京':'10','新潟':'04','福島':'03','小倉':'02',
    '函館':'01','札幌':'11',
}
VENUE_EN = {
    '東京':'Tokyo','中山':'Nakayama','京都':'Kyoto','阪神':'Hanshin',
    '中京':'Chukyo','新潟':'Niigata','福島':'Fukushima',
    '小倉':'Kokura','函館':'Hakodate','札幌':'Sapporo',
}
# JRA馬場情報URL（競馬場別）
VENUE_BABA_URL = {
    '東京': 'https://www.jra.go.jp/keiba/baba/',
    '中山': 'https://www.jra.go.jp/keiba/baba/index2.html',
    '京都': 'https://www.jra.go.jp/keiba/baba/index2.html',
    '阪神': 'https://www.jra.go.jp/keiba/baba/index2.html',
    '中京': 'https://www.jra.go.jp/keiba/baba/index2.html',
    '新潟': 'https://www.jra.go.jp/keiba/baba/index3.html',
    '福島': 'https://www.jra.go.jp/keiba/baba/index3.html',
    '小倉': 'https://www.jra.go.jp/keiba/baba/index3.html',
    '函館': 'https://www.jra.go.jp/keiba/baba/index3.html',
    '札幌': 'https://www.jra.go.jp/keiba/baba/index3.html',
}
VENUE_LIST = list(VENUE_EN.keys())
MOISTURE_FILE = '含水率.xlsx'

DEMO_SAMPLES = [
    {'horse_name':'Sample_A','cushion':9.3,'moisture':7.4,'rank':2,'distance':1300},
    {'horse_name':'Sample_B','cushion':9.5,'moisture':7.3,'rank':1,'distance':1300},
    {'horse_name':'Sample_C','cushion':9.6,'moisture':8.1,'rank':3,'distance':1400},
    {'horse_name':'Sample_D','cushion':10.2,'moisture':7.2,'rank':5,'distance':1300},
    {'horse_name':'Sample_E','cushion':10.4,'moisture':6.8,'rank':8,'distance':1200},
    {'horse_name':'Sample_F','cushion':10.6,'moisture':5.9,'rank':4,'distance':1300},
    {'horse_name':'Sample_G','cushion':10.8,'moisture':6.2,'rank':6,'distance':1400},
    {'horse_name':'Sample_H','cushion':11.1,'moisture':8.3,'rank':1,'distance':1300},
    {'horse_name':'Sample_I','cushion':11.2,'moisture':7.1,'rank':2,'distance':1300},
    {'horse_name':'Sample_J','cushion':9.8,'moisture':6.5,'rank':7,'distance':1200},
]

if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'MS Gothic'
else:
    try:
        plt.rcParams['font.family'] = 'Hiragino Sans'
    except Exception:
        pass
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# settings.txt 読み込み
# ============================================================
def load_settings():
    defaults = {
        '競馬場':        '東京',
        'レース日':       '2026.2.15',
        'クッション値':   'auto',
        '芝含水率':       'auto',
        'ダート含水率':   'auto',
        'デモモード':     'True',
        'スクレイピング': 'True',
    }
    settings_file = 'settings.txt'
    if not os.path.exists(settings_file):
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write("""# 競馬データ分析ツール 設定ファイル
# ============================================================
# 競馬場名
競馬場 = 東京

# レース日（西暦.月.日）
レース日 = 2026.2.15

# クッション値（auto = 自動取得 / 数値 = 手動: 例 10.1）
クッション値 = auto

# 芝含水率（auto = 自動取得 / 数値 = 手動: 例 14.7）
芝含水率 = auto

# ダート含水率（auto = 自動取得 / 数値 = 手動: 例 18.0）
ダート含水率 = auto

# ============================================================
# 通常変更不要
# ============================================================
デモモード = True
スクレイピング = True
""")
        print("settings.txt を新規作成しました")

    cfg = defaults.copy()
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    if key in cfg:
                        cfg[key] = val
    except Exception as e:
        print(f"settings.txt 読み込みエラー: {e}")
    return cfg

# ============================================================
# ユーティリティ
# ============================================================
def safe_name(text):
    if str(text) in VENUE_EN:
        return VENUE_EN[str(text)]
    KANA = {
        'ア':'a','イ':'i','ウ':'u','エ':'e','オ':'o',
        'カ':'ka','キ':'ki','ク':'ku','ケ':'ke','コ':'ko',
        'サ':'sa','シ':'shi','ス':'su','セ':'se','ソ':'so',
        'タ':'ta','チ':'chi','ツ':'tsu','テ':'te','ト':'to',
        'ナ':'na','ニ':'ni','ヌ':'nu','ネ':'ne','ノ':'no',
        'ハ':'ha','ヒ':'hi','フ':'fu','ヘ':'he','ホ':'ho',
        'マ':'ma','ミ':'mi','ム':'mu','メ':'me','モ':'mo',
        'ヤ':'ya','ユ':'yu','ヨ':'yo',
        'ラ':'ra','リ':'ri','ル':'ru','レ':'re','ロ':'ro',
        'ワ':'wa','ヲ':'wo','ン':'n',
        'ガ':'ga','ギ':'gi','グ':'gu','ゲ':'ge','ゴ':'go',
        'ザ':'za','ジ':'ji','ズ':'zu','ゼ':'ze','ゾ':'zo',
        'ダ':'da','ヂ':'di','ヅ':'du','デ':'de','ド':'do',
        'バ':'ba','ビ':'bi','ブ':'bu','ベ':'be','ボ':'bo',
        'パ':'pa','ピ':'pi','プ':'pu','ペ':'pe','ポ':'po',
        'キャ':'kya','シャ':'sha','チャ':'cha','ジャ':'ja',
        'ショ':'sho','チョ':'cho','ジョ':'jo','シュ':'shu',
        'ッ':'t','ー':'-','ァ':'a','ィ':'i','ゥ':'u','ェ':'e','ォ':'o',
    }
    res = ''
    i = 0
    s = str(text)
    while i < len(s):
        if i+1 < len(s) and s[i:i+2] in KANA:
            res += KANA[s[i:i+2]]; i += 2
        elif s[i] in KANA:
            res += KANA[s[i]]; i += 1
        elif re.match(r'[a-zA-Z0-9_\-]', s[i]):
            res += s[i]; i += 1
        else:
            res += '_'; i += 1
    res = re.sub(r'_+', '_', res).strip('_')
    return res or 'horse'

def clean_venue(text):
    for v in VENUE_LIST:
        if v in str(text):
            return v
    return ''

def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--lang=ja')
    opts.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    )
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )

# ============================================================
# 【修正①】開催日番号取得（安定版）
# ============================================================
def get_kaisai_day(year, month, day, venue_jp):
    """
    netkeibaのレース一覧ページからrace_idを直接取得し
    開催日番号（race_id の 9〜10文字目）を返す。
    取得失敗時は '01' を返す。
    """
    date_str = f"{year}{month:02d}{day:02d}"
    vcode    = VENUE_CODE.get(venue_jp, '05')

    print(f"\n   開催日番号を取得中 ({date_str} / {venue_jp})...")

    for attempt in range(2):
        driver = None
        try:
            from selenium.webdriver.common.by import By
            driver = make_driver()
            url = f"https://race.netkeiba.com/top/race_list.html?kaisai_date={date_str}"
            driver.get(url)
            time.sleep(5 + attempt * 3)

            links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="race_id="]')
            for lnk in links:
                href = lnk.get_attribute('href') or ''
                m = re.search(r'race_id=(\d{12})', href)
                if m:
                    rid = m.group(1)
                    # race_id: YYYY(4)+競馬場(2)+回次(2)+日目(2)+R番号(2)
                    if rid[4:6] == vcode:
                        kaisai_day = rid[8:10]
                        driver.quit()
                        print(f"   開催日番号: {kaisai_day}日目")
                        return kaisai_day
            driver.quit()
            print(f"   {venue_jp}のrace_idが見つかりません（試行{attempt+1}）")
        except Exception as e:
            print(f"   開催日番号取得エラー: {e}")
            if driver:
                try: driver.quit()
                except Exception: pass

    print("   開催日番号の取得失敗 → 01 を使用")
    return '01'

# ============================================================
# 【修正②】JRA馬場情報から含水率・クッション値を自動取得
# ============================================================
def scrape_baba_info(venue_jp):
    """
    JRA馬場情報ページから芝含水率・ダート含水率・クッション値を取得。
    戻り値: {'cushion': float or None,
             'moisture_turf': float or None,
             'moisture_dirt': float or None}
    """
    result = {'cushion': None, 'moisture_turf': None, 'moisture_dirt': None}
    url = VENUE_BABA_URL.get(venue_jp, 'https://www.jra.go.jp/keiba/baba/')

    print(f"\n   JRA馬場情報を取得中: {venue_jp}")
    print(f"   URL: {url}")

    driver = None
    try:
        from selenium.webdriver.common.by import By
        driver = make_driver()
        driver.get(url)
        time.sleep(8)  # JavaScriptの描画を待つ

        page_text = driver.page_source
        driver.quit()
        driver = None

        # ── テキスト全体から数値を収集 ──
        # JRAページは数値をテキストノードとして描画するため
        # ページソースから正規表現で抽出する

        # クッション値: id="cushion_data"内の小数値
        # 例: <div style="left: 46%;">9.4</di
        cushion_m = re.search(
            r'id=.cushion_data.[^>]*>.*?(\d+\.\d+)', page_text, re.DOTALL
        )
        # フォールバック: 「クッション値」直後の小数
        if not cushion_m:
            cushion_m = re.search(
                r'クッション値[^<]{0,300}?(\d+\.\d+)', page_text, re.DOTALL
            )
        if cushion_m:
            val = float(cushion_m.group(1))
            if 4.0 <= val <= 20.0:
                result['cushion'] = val
                print(f"   クッション値: {val}")

        # 芝含水率: id="turf_line" のゴール前（最初の%値）を使用
        # 例: <tr id="turf_line"><th>芝</th><td class="gm">11.3%</td>...
        turf_m = re.search(
            r'id=.turf_line.[^>]*>.*?(\d+(?:\.\d+)?)\s*%',
            page_text, re.DOTALL
        )
        if turf_m:
            val = float(turf_m.group(1))
            if 1.0 <= val <= 60.0:
                result['moisture_turf'] = val
                print(f"   芝含水率: {val}%")

        # ダート含水率: id="dirt_line" のゴール前（最初の%値）を使用
        # 例: <tr id="dirt_line"><th>ダート</th><td class="gm">5.5%</td>...
        dirt_m = re.search(
            r'id=.dirt_line.[^>]*>.*?(\d+(?:\.\d+)?)\s*%',
            page_text, re.DOTALL
        )
        if dirt_m:
            val = float(dirt_m.group(1))
            if 1.0 <= val <= 60.0:
                result['moisture_dirt'] = val
                print(f"   ダート含水率: {val}%")

        # 取得失敗時のフォールバックログ
        if result['moisture_turf'] is None:
            print("   芝含水率: 取得失敗（手動値またはデフォルトを使用）")
        if result['moisture_dirt'] is None:
            print("   ダート含水率: 取得失敗（手動値またはデフォルトを使用）")

    except Exception as e:
        print(f"   馬場情報取得失敗: {e}")
        if driver:
            try: driver.quit()
            except Exception: pass

    return result

# ============================================================
# スクレイピング：1レース分の出走馬データ取得
# ============================================================
def scrape_one_race(race_url, venue_jp, race_no, race_date_str):
    """
    1レース分の出走馬データを取得する。
    Chrome を1インスタンスだけ起動して全頭のページを順番に取得する（高速化）。
    """
    print(f"\n   {venue_jp}{race_no}R 出走馬取得中...")

    from selenium.webdriver.common.by import By

    driver = None
    try:
        driver = make_driver()

        # ── ① 出馬表ページから馬名とURLを収集 ──────────────
        horse_links = {}
        for attempt in range(3):
            wait_sec = 8 + attempt * 5
            try:
                driver.get(race_url)
                time.sleep(wait_sec)

                # URLをキーにして収集（同一URLの重複を防ぐ）
                url_to_names = {}
                for css in ['td.HorseName a', 'span.Horse_Name a', 'a[href*="/horse/"]']:
                    elems = driver.find_elements(By.CSS_SELECTOR, css)
                    for e in elems:
                        name = e.text.strip()
                        href = e.get_attribute('href') or ''
                        base_url = href.split('?')[0].rstrip('/')
                        if name and '/horse/' in href and len(name) >= 2:
                            if base_url not in url_to_names:
                                url_to_names[base_url] = []
                            url_to_names[base_url].append((name, href))
                    if url_to_names:
                        break

                # 各URLから最も適切な馬名を選択
                # 優先順位：数字で始まらない名前 > 最短の名前
                for base_url, candidates in url_to_names.items():
                    best_name, best_href = None, None
                    for name, href in candidates:
                        if re.match(r'^\d', name):
                            continue
                        if best_name is None or len(name) < len(best_name):
                            best_name, best_href = name, href
                    # 全候補が数字始まりだった場合は数字部分を除去して使う
                    if best_name is None and candidates:
                        raw, href = candidates[0]
                        best_name = re.sub(r'^\d+\s*', '', raw).strip() or raw
                        best_href = href
                    if best_name:
                        horse_links[best_name] = best_href

                if horse_links:
                    print(f"      {len(horse_links)}頭検出")
                    break
                print(f"      検出0頭、リトライ ({attempt+1}/3)...")
            except Exception as e:
                print(f"      出馬表取得エラー: {e}")

        if not horse_links:
            print(f"      出走馬取得失敗（レース未登録の可能性）")
            driver.quit()
            return [], pd.DataFrame()

        # ── ② 同じChromeで各馬のページを順番に取得 ─────────
        all_rows = []
        for idx, (horse_name, h_url) in enumerate(horse_links.items(), 1):
            for attempt in range(2):
                try:
                    driver.get(h_url)
                    # 2頭目以降は待機時間を短くする（ページキャッシュが効くため）
                    time.sleep(2 if idx > 1 else 3)

                    rows = driver.find_elements(
                        By.CSS_SELECTOR,
                        'table.db_h_race_results tbody tr, table.Race_Table tbody tr'
                    )
                    past_count = 0
                    for rrow in rows:
                        if past_count >= 7:
                            break
                        try:
                            cells = rrow.find_elements(By.TAG_NAME, 'td')
                            if len(cells) < 6:
                                continue
                            date_m = re.search(r'(\d{4})/(\d{2})/(\d{2})', cells[0].text)
                            if not date_m:
                                continue
                            race_dt = datetime(
                                int(date_m.group(1)),
                                int(date_m.group(2)),
                                int(date_m.group(3))
                            ).date()
                            venue_raw   = cells[1].text.strip() if len(cells) > 1 else ''
                            venue_clean = clean_venue(venue_raw)
                            race_nm     = cells[4].text.strip() if len(cells) > 4 else ''

                            # 距離と芝・ダート判定
                            dist_num = None
                            surf = '芝'
                            for ci in [5, 6, 7]:
                                if ci < len(cells):
                                    cell_text = cells[ci].text
                                    if 'ダ' in cell_text or 'D' in cell_text:
                                        surf = 'ダート'
                                    dm = re.search(r'(\d{4})', cell_text)
                                    if dm:
                                        dist_num = int(dm.group(1))
                                        break

                            rank_num = None
                            for ci in [11, 12, 13, 10]:
                                if ci < len(cells):
                                    t = cells[ci].text.strip()
                                    if re.match(r'^\d+$', t):
                                        rank_num = int(t)
                                        break

                            all_rows.append({
                                'race_no':    race_no,
                                'horse_name': horse_name,
                                'race_date':  race_dt,
                                'venue':      venue_clean,
                                'race_name':  race_nm,
                                'distance':   dist_num,
                                'surface':    surf,
                                'rank':       rank_num,
                            })
                            past_count += 1
                        except Exception:
                            continue

                    print(f"      [{idx}/{len(horse_links)}] {horse_name}: {past_count}走取得")
                    break  # 成功したら次の馬へ

                except Exception as e:
                    print(f"      [{idx}] {horse_name} エラー ({attempt+1}/2): {e}")
                    if attempt == 1:
                        # 2回失敗したらドライバーを再起動して継続
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = make_driver()

    except Exception as e:
        print(f"      致命的エラー: {e}")
    finally:
        # ── ③ 最後に1回だけChromeを終了 ──────────────────
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return list(horse_links.keys()) if 'horse_links' in dir() else [], \
           pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

# ============================================================
# 含水率マスタ読み込み
# ============================================================
def load_moisture_history():
    print("\n含水率履歴を読み込み中...")
    candidates = [MOISTURE_FILE, './data/含水率.xlsx', './data/moisture_data.xlsx']
    filepath = None
    for c in candidates:
        if os.path.exists(c):
            filepath = c
            print(f"   ファイル: {filepath}")
            break
    if filepath is None:
        print("   含水率ファイルが見つかりません")
        return pd.DataFrame(columns=['date','venue','cushion','moisture','surface'])

    df_raw = pd.read_excel(filepath, header=None)

    # シンプル形式チェック
    try:
        first = [str(x).strip() for x in df_raw.iloc[0]]
        if 'date' in first and 'venue' in first:
            df_raw.columns = df_raw.iloc[0]
            df_raw = df_raw.iloc[1:].reset_index(drop=True)
            df_raw['date']     = pd.to_datetime(df_raw['date'], errors='coerce').dt.date
            df_raw['cushion']  = pd.to_numeric(df_raw['cushion'],  errors='coerce')
            df_raw['moisture'] = pd.to_numeric(df_raw['moisture'], errors='coerce')
            df_raw['venue']    = df_raw['venue'].astype(str)
            if 'surface' not in df_raw.columns:
                df_raw['surface'] = '芝'
            df_raw = df_raw.dropna(subset=['date','cushion','moisture'])
            print(f"   {len(df_raw)}件 (シンプル形式)")
            return df_raw[['date','venue','cushion','moisture','surface']].copy()
    except Exception:
        pass

    # マルチヘッダー形式
    header_row = 0
    for idx in range(min(15, len(df_raw))):
        row_vals = [str(x) for x in df_raw.iloc[idx]]
        if any('開催日次' in v or '年' == v.strip() for v in row_vals):
            header_row = idx
            break

    try:
        r0 = df_raw.iloc[header_row].fillna('').astype(str)
        r1 = df_raw.iloc[header_row+1].fillna('').astype(str) if header_row+1 < len(df_raw) else r0
        r2 = df_raw.iloc[header_row+2].fillna('').astype(str) if header_row+2 < len(df_raw) else r0
        cols = []
        for h0, h1, h2 in zip(r0, r1, r2):
            parts = [x.strip() for x in [h0, h1, h2] if x.strip() and x.strip() != 'nan']
            cols.append('_'.join(parts) if parts else f'c{len(cols)}')
    except Exception:
        cols = [f'c{i}' for i in range(len(df_raw.columns))]

    data = df_raw.iloc[header_row+3:].copy()
    if len(data.columns) != len(cols):
        cols = [f'c{i}' for i in range(len(data.columns))]
    data.columns = cols
    data = data.reset_index(drop=True)

    records = []
    for _, row in data.iterrows():
        try:
            year_val = None
            for ci in range(min(20, len(cols))):
                try:
                    v = float(row[cols[ci]])
                    if 2000 <= v <= 2030:
                        year_val = int(v)
                        break
                except Exception:
                    continue
            if year_val is None:
                continue

            date_found = None
            for ci in range(min(5, len(cols))):
                m = re.search(r'(\d{1,2})月\s*(\d{1,2})日', str(row[cols[ci]]))
                if m:
                    try:
                        date_found = datetime(year_val, int(m.group(1)), int(m.group(2))).date()
                        break
                    except Exception:
                        continue
            if date_found is None:
                continue

            venue = ''
            for ci in range(10, min(16, len(cols))):
                v = clean_venue(row[cols[ci]])
                if v:
                    venue = v
                    break

            cushion = None
            for ci in range(4, min(8, len(cols))):
                try:
                    v = float(row[cols[ci]])
                    if 1.0 <= v <= 25.0:
                        cushion = v
                        break
                except Exception:
                    continue

            # 芝含水率
            moisture_turf = None
            for col in cols:
                if 'ゴール前' in col and '芝' in col:
                    try:
                        moisture_turf = float(row[col])
                        break
                    except Exception:
                        continue
            if moisture_turf is None:
                for ci in range(6, min(10, len(cols))):
                    try:
                        v = float(row[cols[ci]])
                        if 1.0 <= v <= 60.0:
                            moisture_turf = v
                            break
                    except Exception:
                        continue

            # ダート含水率
            moisture_dirt = None
            for col in cols:
                if 'ダート' in col or ('ダ' in col and '含水率' in col):
                    try:
                        v = float(row[col])
                        if 1.0 <= v <= 60.0:
                            moisture_dirt = v
                            break
                    except Exception:
                        continue
            if moisture_dirt is None:
                moisture_dirt = moisture_turf  # なければ芝と同値

            if date_found and venue and cushion is not None and moisture_turf is not None:
                records.append({'date': date_found, 'venue': venue,
                                'cushion': cushion, 'moisture': moisture_turf, 'surface': '芝'})
                records.append({'date': date_found, 'venue': venue,
                                'cushion': cushion, 'moisture': moisture_dirt, 'surface': 'ダート'})
        except Exception:
            continue

    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=['date','venue','cushion','moisture','surface'])
    print(f"   {len(result)}件 (マルチヘッダー形式)")
    return result

# ============================================================
# データ結合
# ============================================================
def merge_data(race_df, moisture_df, surface='芝'):
    if race_df.empty or moisture_df.empty:
        return pd.DataFrame()
    r = race_df.copy()
    if 'surface' in moisture_df.columns:
        m = moisture_df[moisture_df['surface'] == surface].copy()
    else:
        m = moisture_df.copy()
    r['_dt'] = pd.to_datetime(r['race_date'], errors='coerce').dt.date
    m['_dt'] = pd.to_datetime(m['date'],      errors='coerce').dt.date
    r['_vc'] = r['venue'].apply(clean_venue)
    m['_vc'] = m['venue'].apply(clean_venue)
    merged = pd.merge(r, m[['_dt','_vc','cushion','moisture']],
                      on=['_dt','_vc'], how='left')
    matched = merged['cushion'].notna().sum()
    if len(merged) > 0:
        print(f"   マッチング: {matched}/{len(merged)} ({matched/len(merged)*100:.1f}%)")
    return merged

# ============================================================
# グラフ描画
# ============================================================
def classify_point(row, target_dist):
    dist = row.get('distance', None)
    rank = row.get('rank', None)
    same = (dist == target_dist)
    good = (isinstance(rank, (int, float)) and not pd.isna(rank) and float(rank) <= 3)
    if good:
        return 'red_double' if same else 'red_circle'
    else:
        return 'blue_circle' if same else 'blue_cross'

def draw_graph(plot_df, out_path, title_str, target_cushion, target_moisture,
               target_dist, highlight=None, demo_overlay=False, demo_mode=True):
    all_pts = plot_df.copy() if not plot_df.empty else pd.DataFrame()
    if demo_overlay and demo_mode:
        ddf = pd.DataFrame(DEMO_SAMPLES)
        ddf['is_demo'] = True
        if not all_pts.empty:
            all_pts['is_demo'] = False
        all_pts = pd.concat([all_pts, ddf], ignore_index=True)
    if 'is_demo' not in all_pts.columns:
        all_pts['is_demo'] = False

    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('#e1e4ea')
    ax.set_facecolor('#f5f6f8')

    for _, row in all_pts.iterrows():
        x = row.get('cushion', np.nan)
        y = row.get('moisture', np.nan)
        if pd.isna(x) or pd.isna(y):
            continue
        hn      = str(row.get('horse_name', ''))
        is_demo = bool(row.get('is_demo', False))
        pt      = classify_point(row, target_dist)

        if highlight:
            if hn == highlight:
                alpha, size, lw = 1.0, 380, 4.5
            else:
                alpha, size, lw = (0.3 if is_demo else 0.04), 220, 2.5
        else:
            alpha, size, lw = (0.5 if is_demo else 0.9), 300, 3.5

        if pt == 'red_double':
            ax.scatter(x, y, s=size*0.8, facecolors='#ef4444', edgecolors='#dc2626',
                       alpha=alpha, linewidths=lw, zorder=3)
            ax.scatter(x, y, s=size*2.5, facecolors='none', edgecolors='#ef4444',
                       alpha=alpha, linewidths=lw, zorder=3)
        elif pt == 'red_circle':
            ax.scatter(x, y, s=size*1.2, facecolors='none', edgecolors='#ef4444',
                       alpha=alpha, linewidths=lw, zorder=3)
        elif pt == 'blue_circle':
            ax.scatter(x, y, s=size*1.2, facecolors='none', edgecolors='#3b82f6',
                       alpha=alpha, linewidths=lw, zorder=3)
        elif pt == 'blue_cross':
            ax.scatter(x, y, s=size*1.3, marker='x', c='#3b82f6',
                       alpha=alpha, linewidths=lw+1, zorder=3)

    ax.axvline(x=target_cushion, color='#f59e0b', linewidth=4, linestyle='--',
               alpha=0.85, zorder=4)
    ax.axhline(y=target_moisture, color='#f59e0b', linewidth=4, linestyle='--',
               alpha=0.85, zorder=4)
    ax.plot(target_cushion, target_moisture, 'o', ms=16, color='#d97706',
            mew=4, mfc='none', zorder=5)

    ax.set_title(title_str, fontsize=18, fontweight='bold', pad=20, color='#1e293b')
    ax.set_xlabel('Cushion Value', fontsize=14, fontweight='bold', color='#334155')
    ax.set_ylabel('Moisture (%)',  fontsize=14, fontweight='bold', color='#334155')
    ax.grid(True, alpha=0.08, color='#cbd5e1', zorder=1)
    ax.set_axisbelow(True)

    # cushion/moisture列が存在しない場合（マッチングゼロ）は空DataFrameとして扱う
    if 'cushion' not in all_pts.columns or 'moisture' not in all_pts.columns:
        valid = pd.DataFrame()
    else:
        valid = all_pts[all_pts['cushion'].notna() & all_pts['moisture'].notna()]
    if not valid.empty:
        c_vals = list(valid['cushion'].dropna()) + [target_cushion]
        m_vals = list(valid['moisture'].dropna()) + [target_moisture]
        cr = max(max(c_vals)-min(c_vals), 1.5)
        mr = max(max(m_vals)-min(m_vals), 1.5)
        ax.set_xlim(min(c_vals)-cr*0.12, max(c_vals)+cr*0.12)
        ax.set_ylim(min(m_vals)-mr*0.12, max(m_vals)+mr*0.12)

    legend_elements = [
        Line2D([0],[0],marker='o',color='w',mfc='#ef4444',ms=14,
               label='赤◎：同距離 & 3着以内',mec='#dc2626',mew=3),
        Line2D([0],[0],marker='o',color='w',mfc='none',ms=14,
               label='赤○：別距離 & 3着以内',mec='#ef4444',mew=3),
        Line2D([0],[0],marker='o',color='w',mfc='none',ms=14,
               label='青○：同距離 & 4着以下',mec='#3b82f6',mew=3),
        Line2D([0],[0],marker='x',color='#3b82f6',ms=14,
               label='青×：別距離 & 4着以下',mew=3),
        Line2D([0],[0],marker='o',color='w',mfc='#d97706',ms=14,
               label=f'★：今回 C={target_cushion} M={target_moisture}%',
               mec='#d97706',mew=3),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11,
              frameon=True, fancybox=True, shadow=True,
              facecolor='white', edgecolor='#cbd5e1', framealpha=0.95)
    for sp in ax.spines.values():
        sp.set_edgecolor('#94a3b8')
        sp.set_linewidth(2)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else '.', exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#f8f9fb')
    plt.close()
    print(f"      {os.path.basename(out_path)}")

# ============================================================
# メイン処理
# ============================================================
def main():
    cfg = load_settings()
    venue_jp = cfg['競馬場']
    date_str = cfg['レース日']
    demo_mode = cfg['デモモード'].strip().lower() in ('true','1','yes','はい')
    scraping  = cfg['スクレイピング'].strip().lower() in ('true','1','yes','はい')

    print(f"\n{'='*60}")
    print(f"Horse Racing Analysis System")
    print(f"   {venue_jp}  {date_str}  1R-12R")
    print(f"{'='*60}")

    os.makedirs('./data', exist_ok=True)

    parts      = date_str.split('.')
    date_slug  = f"{parts[0]}_{int(parts[1]):02d}_{int(parts[2]):02d}"
    venue_slug = safe_name(venue_jp)
    out_dir    = f"./output/{date_slug}_{venue_slug}"
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output: {out_dir}/")

    # ── 含水率・クッション値の決定 ──────────────────────────
    cushion_cfg       = cfg['クッション値'].strip()
    moisture_turf_cfg = cfg['芝含水率'].strip()
    moisture_dirt_cfg = cfg['ダート含水率'].strip()

    cushion       = None
    moisture_turf = None
    moisture_dirt = None

    # autoが1つでもあればJRAサイトから自動取得
    need_auto = any(
        v.lower() == 'auto'
        for v in [cushion_cfg, moisture_turf_cfg, moisture_dirt_cfg]
    )

    # 含水率のauto取得はスクレイピングフラグに関係なく常に実行
    if need_auto:
        print("\nJRAサイトから馬場情報を自動取得中...")
        baba = scrape_baba_info(venue_jp)
        if cushion_cfg.lower() == 'auto':
            cushion = baba.get('cushion')
            if cushion is None:
                print("   クッション値: 自動取得失敗")
        if moisture_turf_cfg.lower() == 'auto':
            moisture_turf = baba.get('moisture_turf')
            if moisture_turf is None:
                print("   芝含水率: 自動取得失敗")
        if moisture_dirt_cfg.lower() == 'auto':
            moisture_dirt = baba.get('moisture_dirt')
            if moisture_dirt is None:
                print("   ダート含水率: 自動取得失敗")

    # 手動値で補完
    if cushion is None:
        try:
            cushion = float(cushion_cfg)
        except Exception:
            cushion = 10.0
            print(f"   クッション値: 手動値なし → デフォルト {cushion} を使用")
    if moisture_turf is None:
        try:
            moisture_turf = float(moisture_turf_cfg)
        except Exception:
            moisture_turf = 14.7
            print(f"   芝含水率: 手動値なし → デフォルト {moisture_turf}% を使用")
    if moisture_dirt is None:
        try:
            moisture_dirt = float(moisture_dirt_cfg)
        except Exception:
            moisture_dirt = 18.0
            print(f"   ダート含水率: 手動値なし → デフォルト {moisture_dirt}% を使用")

    print(f"\n使用する馬場情報:")
    print(f"   クッション値  : {cushion}")
    print(f"   芝含水率      : {moisture_turf}%")
    print(f"   ダート含水率  : {moisture_dirt}%")

    # ── 含水率マスタ読み込み ─────────────────────────────────
    moisture_df = load_moisture_history()
    today_date  = datetime(*[int(x) for x in date_str.split('.')]).date()

    # 今日の芝・ダートデータを追記
    new_rows = []
    for surf, mval in [('芝', moisture_turf), ('ダート', moisture_dirt)]:
        has = False
        if not moisture_df.empty:
            has = any(
                str(r['date']) == str(today_date) and
                str(r.get('venue','')) == venue_jp and
                str(r.get('surface','')) == surf
                for _, r in moisture_df.iterrows()
            )
        if not has:
            new_rows.append({
                'date': today_date, 'venue': venue_jp,
                'cushion': cushion, 'moisture': mval, 'surface': surf
            })
    if new_rows:
        moisture_df = pd.concat(
            [moisture_df, pd.DataFrame(new_rows)], ignore_index=True
        )

    # ── 開催日番号取得 ────────────────────────────────────────
    year_int  = int(parts[0])
    month_int = int(parts[1])
    day_int   = int(parts[2])
    vcode     = VENUE_CODE.get(venue_jp, '05')
    kaisai_day = get_kaisai_day(year_int, month_int, day_int, venue_jp)

    all_csv_rows = []

    # ── 1R〜12R ループ ────────────────────────────────────────
    for race_no in range(1, 13):
        print(f"\n{'─'*50}")
        print(f"{venue_jp} {race_no}R 処理中...")

        rnum     = f"{race_no:02d}"
        race_id  = f"{parts[0]}{vcode}01{kaisai_day}{rnum}"
        race_url = (
            f"https://race.netkeiba.com/race/shutuba.html"
            f"?race_id={race_id}&rf=race_list"
        )
        print(f"   URL: {race_url}")

        race_file = f"./data/race_data_{venue_slug}_{race_no}R.xlsx"
        if scraping:
            horse_names, race_df = scrape_one_race(
                race_url, venue_jp, race_no, date_str
            )
            if not race_df.empty:
                race_df.to_excel(race_file, index=False)
        else:
            horse_names = []
            race_df = pd.DataFrame()
            if os.path.exists(race_file):
                race_df = pd.read_excel(race_file)
                horse_names = (
                    race_df['horse_name'].unique().tolist()
                    if 'horse_name' in race_df.columns else []
                )
                print(f"      既存ファイル使用: {len(race_df)}行 / {len(horse_names)}頭")

        if race_df.empty:
            print(f"      {race_no}Rはデータなし（全頭0走 - 新馬戦の可能性）")
            continue

        # 芝・ダート判定
        race_surface = '芝'
        if 'surface' in race_df.columns:
            mode = race_df['surface'].mode()
            if not mode.empty:
                race_surface = mode.iloc[0]

        moisture = moisture_dirt if race_surface == 'ダート' else moisture_turf
        print(f"   馬場: {race_surface} → 含水率: {moisture}%")

        # データ結合
        merged = merge_data(race_df, moisture_df, surface=race_surface)

        # 距離取得
        if not merged.empty and 'distance' in merged.columns:
            mode_d = merged['distance'].dropna().mode()
            target_dist = int(mode_d[0]) if not mode_d.empty else 1600
        else:
            target_dist = 1600

        race_label = (
            f"{venue_jp} {race_no}R {race_surface} {target_dist}m"
            f"  C={cushion} M={moisture}%"
        )
        if demo_mode:
            race_label += "\n（サンプルデータ含む）"

        # グラフ出力
        draw_graph(
            merged, f"{out_dir}/{race_no:02d}R_all.png",
            race_label, cushion, moisture, target_dist,
            demo_overlay=True, demo_mode=demo_mode
        )
        for hname in horse_names:
            h_df = (
                merged[merged['horse_name'] == hname].copy()
                if not merged.empty else pd.DataFrame()
            )
            draw_graph(
                h_df, f"{out_dir}/{race_no:02d}R_{safe_name(hname)}.png",
                f"{race_label}\n【{hname}】",
                cushion, moisture, target_dist,
                highlight=hname, demo_overlay=False, demo_mode=False
            )

        if not merged.empty:
            merged['race_no'] = race_no
            all_csv_rows.append(merged)

        print(f"   {race_no}R 完了")

    # 統合CSV保存
    print(f"\n{'='*60}")
    if all_csv_rows:
        combined = pd.concat(all_csv_rows, ignore_index=True)
        csv_path = f"{out_dir}/analysis_result_all.csv"
        combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"CSV saved: {csv_path} ({len(combined)} rows)")

    print(f"\nDone! Output: {out_dir}/")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
