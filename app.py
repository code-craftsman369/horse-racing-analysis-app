"""
Horse Racing Analysis - Streamlit Web App
散布図 + 馬名リスト + レース切り替えを1画面に統合
"""

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import os, re, platform
from datetime import datetime

# ============================================================
# ページ設定
# ============================================================
st.set_page_config(
    page_title="競馬データ分析",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# フォント設定
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'MS Gothic'
else:
    try:
        plt.rcParams['font.family'] = 'Hiragino Sans'
    except:
        plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

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
VENUE_LIST = list(VENUE_EN.keys())
MOISTURE_FILE = '含水率.xlsx'

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

# ============================================================
# settings.txt 読み込み
# ============================================================
def load_settings():
    defaults = {
        '競馬場':       '東京',
        'レース日':      '2026.2.15',
        'クッション値':  '10.0',
        '芝含水率':      '14.7',
        'ダート含水率':  '18.0',
        'デモモード':    'True',
        'スクレイピング':'True',
    }
    for fname in ['settings.txt', './settings.txt']:
        if os.path.exists(fname):
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip(); val = val.strip()
                            if key in defaults:
                                defaults[key] = val
            except:
                pass
            break
    return defaults

# ============================================================
# 含水率マスタ読み込み
# ============================================================
@st.cache_data
def load_moisture_history():
    candidates = [MOISTURE_FILE, './data/含水率.xlsx', './data/moisture_data.xlsx']
    filepath = None
    for c in candidates:
        if os.path.exists(c):
            filepath = c
            break
    if filepath is None:
        return pd.DataFrame(columns=['date','venue','cushion','moisture'])

    df_raw = pd.read_excel(filepath, header=None)

    try:
        first = [str(x).strip() for x in df_raw.iloc[0]]
        if 'date' in first and 'venue' in first:
            df_raw.columns = df_raw.iloc[0]
            df_raw = df_raw.iloc[1:].reset_index(drop=True)
            df_raw['date']     = pd.to_datetime(df_raw['date'], errors='coerce').dt.date
            df_raw['cushion']  = pd.to_numeric(df_raw['cushion'],  errors='coerce')
            df_raw['moisture'] = pd.to_numeric(df_raw['moisture'], errors='coerce')
            df_raw['venue']    = df_raw['venue'].astype(str)
            df_raw = df_raw.dropna(subset=['date','cushion','moisture'])
            return df_raw[['date','venue','cushion','moisture']].copy()
    except:
        pass

    header_row = 0
    for idx in range(min(15, len(df_raw))):
        row_vals = [str(x) for x in df_raw.iloc[idx]]
        if any('開催日次' in v or '年' == v.strip() for v in row_vals):
            header_row = idx; break

    try:
        r0 = df_raw.iloc[header_row].fillna('').astype(str)
        r1 = df_raw.iloc[header_row+1].fillna('').astype(str) if header_row+1 < len(df_raw) else r0
        r2 = df_raw.iloc[header_row+2].fillna('').astype(str) if header_row+2 < len(df_raw) else r0
        cols = []
        for h0,h1,h2 in zip(r0,r1,r2):
            parts = [x.strip() for x in [h0,h1,h2] if x.strip() and x.strip()!='nan']
            cols.append('_'.join(parts) if parts else f'c{len(cols)}')
    except:
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
                    if 2000 <= v <= 2030: year_val = int(v); break
                except: continue
            if year_val is None: continue
            date_found = None
            for ci in range(min(5, len(cols))):
                m = re.search(r'(\d{1,2})月\s*(\d{1,2})日', str(row[cols[ci]]))
                if m:
                    try:
                        date_found = datetime(year_val, int(m.group(1)), int(m.group(2))).date()
                        break
                    except: continue
            if date_found is None: continue
            venue = ''
            for ci in range(10, min(16, len(cols))):
                v = clean_venue(row[cols[ci]])
                if v: venue = v; break
            cushion = None
            for ci in range(4, min(8, len(cols))):
                try:
                    v = float(row[cols[ci]])
                    if 1.0 <= v <= 25.0: cushion = v; break
                except: continue
            moisture = None
            for col in cols:
                if 'ゴール前' in col and '芝' in col:
                    try: moisture = float(row[col]); break
                    except: continue
            if moisture is None:
                for ci in range(6, min(10, len(cols))):
                    try:
                        v = float(row[cols[ci]])
                        if 1.0 <= v <= 60.0: moisture = v; break
                    except: continue
            if date_found and venue and cushion is not None and moisture is not None:
                records.append({'date':date_found,'venue':venue,'cushion':cushion,'moisture':moisture})
        except: continue

    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=['date','venue','cushion','moisture'])
    return result

# ============================================================
# レースデータ読み込み
# ============================================================
@st.cache_data
def load_race_data(venue_slug, race_no):
    paths = [
        f"./data/race_data_{venue_slug}_{race_no}R.xlsx",
        f"./race_data.xlsx",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                df = pd.read_excel(p)
                if len(df) > 0:
                    return df
            except:
                pass
    return pd.DataFrame()

# ============================================================
# データ結合
# ============================================================
def merge_data(race_df, moisture_df):
    if race_df.empty or moisture_df.empty:
        return pd.DataFrame()
    r = race_df.copy()
    m = moisture_df.copy()
    r['_dt'] = pd.to_datetime(r['race_date'], errors='coerce').dt.date
    m['_dt'] = pd.to_datetime(m['date'],      errors='coerce').dt.date
    r['_vc'] = r['venue'].apply(clean_venue)
    m['_vc'] = m['venue'].apply(clean_venue)
    return pd.merge(r, m[['_dt','_vc','cushion','moisture']],
                    on=['_dt','_vc'], how='left')

# ============================================================
# 散布図描画
# ============================================================
def draw_scatter(plot_df, target_cushion, target_moisture, target_dist,
                 highlight=None, title=""):
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#f8f9fb')
    ax.set_facecolor('#f5f6f8')

    if not plot_df.empty:
        for _, row in plot_df.iterrows():
            x = row.get('cushion', np.nan)
            y = row.get('moisture', np.nan)
            if pd.isna(x) or pd.isna(y): continue
            hn   = str(row.get('horse_name', ''))
            dist = row.get('distance', None)
            rank = row.get('rank', None)
            same = (dist == target_dist)
            good = (isinstance(rank,(int,float)) and not pd.isna(rank) and float(rank) <= 3)

            if highlight and hn == highlight:
                alpha, size, lw = 1.0, 320, 4.0
            elif highlight:
                alpha, size, lw = 0.08, 180, 2.0
            else:
                alpha, size, lw = 0.85, 220, 2.5

            if good and same:
                ax.scatter(x,y,s=size*0.7,facecolors='#ef4444',edgecolors='#dc2626',alpha=alpha,linewidths=lw,zorder=3)
                ax.scatter(x,y,s=size*2.2,facecolors='none',edgecolors='#ef4444',alpha=alpha,linewidths=lw,zorder=3)
            elif good:
                ax.scatter(x,y,s=size,facecolors='none',edgecolors='#ef4444',alpha=alpha,linewidths=lw,zorder=3)
            elif same:
                ax.scatter(x,y,s=size,facecolors='none',edgecolors='#3b82f6',alpha=alpha,linewidths=lw,zorder=3)
            else:
                ax.scatter(x,y,s=size,marker='x',c='#3b82f6',alpha=alpha,linewidths=lw,zorder=3)

    ax.axvline(x=target_cushion, color='#f59e0b',linewidth=3,linestyle='--',alpha=0.85,zorder=4)
    ax.axhline(y=target_moisture,color='#f59e0b',linewidth=3,linestyle='--',alpha=0.85,zorder=4)
    ax.plot(target_cushion, target_moisture, 'o',ms=14,color='#d97706',mew=3,mfc='none',zorder=5)

    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10, color='#1e293b')
    ax.set_xlabel('Cushion Value', fontsize=10, color='#334155')
    ax.set_ylabel('Moisture (%)',  fontsize=10, color='#334155')
    ax.grid(True, alpha=0.1, color='#cbd5e1', zorder=1)
    ax.set_axisbelow(True)

    if not plot_df.empty:
        valid = plot_df[plot_df['cushion'].notna() & plot_df['moisture'].notna()]
        if not valid.empty:
            c_vals = list(valid['cushion'].dropna()) + [target_cushion]
            m_vals = list(valid['moisture'].dropna()) + [target_moisture]
            cr = max(max(c_vals)-min(c_vals), 1.5)
            mr = max(max(m_vals)-min(m_vals), 1.5)
            ax.set_xlim(min(c_vals)-cr*0.15, max(c_vals)+cr*0.15)
            ax.set_ylim(min(m_vals)-mr*0.15, max(m_vals)+mr*0.15)

    legend_elements = [
        Line2D([0],[0],marker='o',color='w',mfc='#ef4444',ms=10,label='同距離 好走',mec='#dc2626',mew=2),
        Line2D([0],[0],marker='o',color='w',mfc='none', ms=10,label='他距離 好走',mec='#ef4444',mew=2),
        Line2D([0],[0],marker='o',color='w',mfc='none', ms=10,label='同距離 凡走',mec='#3b82f6',mew=2),
        Line2D([0],[0],marker='x',color='#3b82f6',ms=10,label='他距離 凡走',mew=2),
    ]
    ax.legend(handles=legend_elements,loc='upper left',fontsize=8,
              frameon=True,fancybox=True,facecolor='white',framealpha=0.9)
    for sp in ax.spines.values():
        sp.set_edgecolor('#94a3b8'); sp.set_linewidth(1.5)

    plt.tight_layout()
    return fig

# ============================================================
# 馬リスト集計
# ============================================================
def build_horse_list(merged, horse_names, target_cushion, target_moisture, target_dist, tol=0.5):
    rows = []
    for hname in horse_names:
        h_df = merged[merged['horse_name']==hname] if not merged.empty else pd.DataFrame()
        near = h_df[
            h_df['cushion'].notna() & h_df['moisture'].notna() &
            (abs(h_df['cushion']  - target_cushion)  <= tol) &
            (abs(h_df['moisture'] - target_moisture) <= tol)
        ] if not h_df.empty else pd.DataFrame()
        good = int((near['rank'] <= 3).sum()) if not near.empty and 'rank' in near.columns else 0
        bad  = int((near['rank'] >  3).sum()) if not near.empty and 'rank' in near.columns else 0
        rows.append({'馬名': hname, '好走': good, '凡走': bad,
                     '_df': h_df, '_merged': merged})
    return rows

# ============================================================
# メインUI
# ============================================================
def main():
    # ヘッダー
    st.markdown("""
    <style>
    .main-title {
        font-size: 1.8rem; font-weight: 800; color: #1e293b;
        border-bottom: 3px solid #f59e0b; padding-bottom: 8px; margin-bottom: 16px;
    }
    .race-metric {
        background: #1e293b; color: #f8fafc; padding: 8px 16px;
        border-radius: 8px; font-size: 1.1rem; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }
    .horse-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 10px 14px; margin-bottom: 6px; cursor: pointer;
    }
    .horse-card:hover { border-color: #f59e0b; }
    .badge-good { background:#fef2f2; color:#dc2626; padding:2px 8px;
                  border-radius:12px; font-size:0.8rem; font-weight:600; }
    .badge-bad  { background:#eff6ff; color:#2563eb; padding:2px 8px;
                  border-radius:12px; font-size:0.8rem; font-weight:600; }
    </style>
    """, unsafe_allow_html=True)

    # サイドバー：設定
    with st.sidebar:
        st.markdown("## ⚙️ 設定")
        cfg = load_settings()

        venue_jp = st.selectbox("競馬場", VENUE_LIST,
                                index=VENUE_LIST.index(cfg['競馬場']) if cfg['競馬場'] in VENUE_LIST else 0)
        date_str = st.text_input("レース日（例: 2026.2.15）", value=cfg['レース日'])
        def _to_float(val, default):
            try:
                return float(val) if str(val).lower() != 'auto' else default
            except Exception:
                return default
        cushion       = st.number_input("クッション値",     value=_to_float(cfg['クッション値'], 10.0), step=0.1, format="%.1f")
        moisture_turf = st.number_input("芝含水率 (%)",     value=_to_float(cfg['芝含水率'],     14.7), step=0.1, format="%.1f")
        moisture_dirt = st.number_input("ダート含水率 (%)", value=_to_float(cfg['ダート含水率'], 18.0), step=0.1, format="%.1f")

        st.divider()
        st.markdown("**凡例**")
        st.markdown("🔴◎ 同距離 好走（3着以内）")
        st.markdown("🔴○ 他距離 好走")
        st.markdown("🔵○ 同距離 凡走")
        st.markdown("🔵× 他距離 凡走")
        st.markdown("⭐ 今回のターゲット")

    # データ読み込み
    venue_slug   = safe_name(venue_jp)
    moisture_df  = load_moisture_history()
    today_date   = datetime(*[int(x) for x in date_str.split('.')]).date()

    # 今日のデータを追記
    if not moisture_df.empty:
        has_today = any(
            str(r['date'])==str(today_date) and str(r['venue'])==venue_jp
            for _, r in moisture_df.iterrows()
        )
        if not has_today:
            new_rows = pd.DataFrame([
                {'date':today_date,'venue':venue_jp,'cushion':cushion,'moisture':moisture_turf},
                {'date':today_date,'venue':venue_jp,'cushion':cushion,'moisture':moisture_dirt},
            ])
            moisture_df = pd.concat([moisture_df, new_rows], ignore_index=True)
    else:
        moisture_df = pd.DataFrame([
            {'date':today_date,'venue':venue_jp,'cushion':cushion,'moisture':moisture_turf},
            {'date':today_date,'venue':venue_jp,'cushion':cushion,'moisture':moisture_dirt},
        ])

    # 利用可能レース一覧を検出
    available_races = []
    for rno in range(1, 13):
        fpath = f"./data/race_data_{venue_slug}_{rno}R.xlsx"
        if os.path.exists(fpath):
            available_races.append(rno)

    if not available_races:
        st.warning("⚠️ データが見つかりません。スクレイピングを先に実行してください。")
        st.info(f"探しているファイル: ./data/race_data_{venue_slug}_1R.xlsx 〜 12R.xlsx")
        return

    # タイトル
    st.markdown(f'<div class="main-title">🏇 {venue_jp}  {date_str}  C={cushion} / 芝{moisture_turf}% ダート{moisture_dirt}%</div>',
                unsafe_allow_html=True)

    # レース選択タブ
    tab_labels = [f"{rno}R" for rno in available_races]
    tabs = st.tabs(tab_labels)

    for tab_idx, race_no in enumerate(available_races):
        with tabs[tab_idx]:
            race_df = load_race_data(venue_slug, race_no)
            if race_df.empty:
                st.warning(f"{race_no}R のデータがありません")
                continue

            # 馬名リスト取得
            horse_names = race_df['horse_name'].unique().tolist() if 'horse_name' in race_df.columns else []

            # 芝・ダート判定
            surface = '芝'
            if 'surface' in race_df.columns:
                mode = race_df['surface'].mode()
                if not mode.empty:
                    surface = mode.iloc[0]
            moisture = moisture_dirt if surface == 'ダート' else moisture_turf

            # データ結合
            merged = merge_data(race_df, moisture_df)

            # 距離取得
            if not merged.empty and 'distance' in merged.columns:
                dist_mode = merged['distance'].dropna().mode()
                target_dist = int(dist_mode.iloc[0]) if not dist_mode.empty else 1600
            else:
                target_dist = 1600

            # レース情報ヘッダー
            st.markdown(
                f'<div class="race-metric">{venue_jp} {race_no}R | {surface} {target_dist}m | '
                f'C={cushion} M={moisture}%</div>',
                unsafe_allow_html=True
            )

            # 馬名検索
            search = st.text_input("🔍 馬名検索", key=f"search_{race_no}", placeholder="馬名を入力...")
            filtered_horses = [h for h in horse_names if search.lower() in h.lower()] if search else horse_names

            # 馬選択状態
            sel_key = f"selected_{race_no}"
            if sel_key not in st.session_state:
                st.session_state[sel_key] = None
            selected_horse = st.session_state[sel_key]

            # レイアウト：散布図（左）+ 馬リスト（右）
            col_plot, col_list = st.columns([3, 2])

            with col_plot:
                title_str = f"{venue_jp} {race_no}R {surface} {target_dist}m"
                if selected_horse:
                    title_str += f"  【{selected_horse}】"
                fig = draw_scatter(merged, cushion, moisture, target_dist,
                                   highlight=selected_horse, title=title_str)
                st.pyplot(fig)
                plt.close()

            with col_list:
                st.markdown("**出走馬リスト**（クリックで個別表示）")

                # 馬リスト構築
                horse_rows = build_horse_list(merged, filtered_horses, cushion, moisture, target_dist)

                # TSVエクスポート
                if horse_rows:
                    tsv_df = pd.DataFrame([{
                        '馬名': r['馬名'], '好走': r['好走'], '凡走': r['凡走']
                    } for r in horse_rows])
                    tsv_str = tsv_df.to_csv(sep='\t', index=False)
                    st.download_button(
                        label="📋 TSV出力",
                        data=tsv_str.encode('utf-8-sig'),
                        file_name=f"{venue_jp}_{race_no}R.tsv",
                        mime="text/tab-separated-values",
                        key=f"tsv_{race_no}"
                    )

                # 馬カードリスト
                for hr in horse_rows:
                    hname = hr['馬名']
                    good  = hr['好走']
                    bad   = hr['凡走']
                    is_sel = (selected_horse == hname)
                    bg = "#fffbeb" if is_sel else "white"
                    border = "2px solid #f59e0b" if is_sel else "1px solid #e2e8f0"

                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        if st.button(f"{'▶ ' if is_sel else ''}{hname}",
                                     key=f"btn_{race_no}_{hname}",
                                     use_container_width=True):
                            if is_sel:
                                st.session_state[sel_key] = None
                            else:
                                st.session_state[sel_key] = hname
                            st.rerun()
                    with col_b:
                        st.markdown(f'<span class="badge-good">好走 {good}</span>', unsafe_allow_html=True)
                    with col_c:
                        st.markdown(f'<span class="badge-bad">凡走 {bad}</span>', unsafe_allow_html=True)

                # 選択馬の個別グラフ（リスト下に表示）
                if selected_horse and not merged.empty:
                    st.divider()
                    st.markdown(f"**【{selected_horse}】 近7走の詳細**")
                    h_df = merged[merged['horse_name']==selected_horse]
                    if not h_df.empty:
                        disp = h_df[['race_date','venue','distance','rank','cushion','moisture']].copy()
                        disp.columns = ['日付','競馬場','距離','着順','クッション','含水率']
                        st.dataframe(disp.reset_index(drop=True), use_container_width=True)

if __name__ == '__main__':
    main()
