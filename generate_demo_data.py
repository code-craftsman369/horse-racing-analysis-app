#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_demo_data.py
競馬データ分析ツール用のデモ含水率データを自動生成します。
実行すると 含水率.xlsx が作成されます。
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os

random.seed(42)  # 再現性のため固定シード

# ── 競馬場ごとの現実的な含水率・クッション値の範囲 ──
VENUE_PARAMS = {
    '東京': {'turf': (8.0, 22.0), 'dirt': (7.0, 20.0), 'cushion': (8.0, 12.5)},
    '中山': {'turf': (10.0, 25.0), 'dirt': (9.0, 23.0), 'cushion': (7.5, 11.5)},
    '京都': {'turf': (8.0, 20.0), 'dirt': (7.5, 19.0), 'cushion': (8.5, 12.0)},
    '阪神': {'turf': (9.0, 22.0), 'dirt': (8.0, 21.0), 'cushion': (8.0, 12.0)},
    '中京': {'turf': (8.0, 20.0), 'dirt': (7.5, 18.5), 'cushion': (8.5, 12.5)},
    '新潟': {'turf': (9.0, 21.0), 'dirt': (8.5, 20.0), 'cushion': (8.0, 11.5)},
    '福島': {'turf': (10.0, 23.0), 'dirt': (9.0, 22.0), 'cushion': (7.5, 11.0)},
    '小倉': {'turf': (9.0, 20.0), 'dirt': (8.0, 19.0), 'cushion': (8.5, 12.0)},
    '函館': {'turf': (10.0, 24.0), 'dirt': (9.0, 22.0), 'cushion': (7.5, 11.5)},
    '札幌': {'turf': (10.0, 24.0), 'dirt': (9.0, 22.0), 'cushion': (7.5, 11.5)},
}

# ── 季節・月ごとの開催競馬場スケジュール ──
MONTHLY_VENUES = {
    1:  ['東京', '中山', '京都', '阪神'],
    2:  ['東京', '中山', '京都', '阪神'],
    3:  ['中山', '阪神', '中京'],
    4:  ['東京', '京都', '阪神'],
    5:  ['東京', '京都', '新潟'],
    6:  ['東京', '中京', '阪神'],
    7:  ['新潟', '函館', '小倉'],
    8:  ['新潟', '函館', '小倉', '札幌'],
    9:  ['中山', '阪神', '中京'],
    10: ['東京', '京都', '新潟'],
    11: ['東京', '京都', '阪神', '福島'],
    12: ['中山', '阪神', '中京'],
}

def generate_value(min_val, max_val, seasonal_factor=1.0):
    """季節変動を加味した値を生成"""
    base = random.uniform(min_val, max_val)
    # 少しノイズを加える
    noise = random.gauss(0, (max_val - min_val) * 0.05)
    val = base * seasonal_factor + noise
    return round(max(min_val * 0.85, min(max_val * 1.10, val)), 1)

def seasonal_factor(month):
    """梅雨・秋雨期は含水率高め、夏・冬は低め"""
    factors = {
        1: 0.85, 2: 0.90, 3: 1.05, 4: 1.10,
        5: 1.00, 6: 1.20, 7: 0.90, 8: 0.85,
        9: 1.15, 10: 1.10, 11: 0.95, 12: 0.88,
    }
    return factors.get(month, 1.0)

def generate_demo_data():
    rows = []
    # 2023年1月〜2025年12月（3年分）
    start = datetime(2023, 1, 7)  # 2023年最初の土曜

    for week in range(156):  # 3年 = 156週
        dt = start + timedelta(weeks=week)
        month = dt.month
        sf = seasonal_factor(month)

        # 土日の2日間
        for day_offset in [0, 1]:
            race_dt = dt + timedelta(days=day_offset)
            if race_dt.year > 2025:
                break

            # その月の開催競馬場から2〜3場を選択
            venues = MONTHLY_VENUES.get(month, ['東京', '中山'])
            selected = random.sample(venues, min(2, len(venues)))

            for venue in selected:
                if venue not in VENUE_PARAMS:
                    continue
                params = VENUE_PARAMS[venue]

                turf_moisture  = generate_value(*params['turf'],  seasonal_factor=sf)
                dirt_moisture  = generate_value(*params['dirt'],  seasonal_factor=sf)
                cushion        = generate_value(*params['cushion'])

                rows.append({
                    'date':           race_dt.strftime('%Y-%m-%d'),
                    'venue':          venue,
                    'cushion':        cushion,
                    'moisture_turf':  turf_moisture,
                    'moisture_dirt':  dirt_moisture,
                })

    df = pd.DataFrame(rows).drop_duplicates(subset=['date', 'venue'])
    df = df.sort_values(['date', 'venue']).reset_index(drop=True)
    return df

def save_to_excel(df, path='含水率.xlsx'):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        # シンプル形式で保存（main_analysis.pyが読み取れる形式）
        out = df.rename(columns={
            'date':          'date',
            'venue':         'venue',
            'cushion':       'cushion',
            'moisture_turf': 'moisture',   # 芝含水率をデフォルトに
        })
        # 芝・ダート両方を別シートで保存
        df_turf = df[['date','venue','cushion']].copy()
        df_turf['moisture'] = df['moisture_turf']
        df_turf['surface']  = '芝'

        df_dirt = df[['date','venue','cushion']].copy()
        df_dirt['moisture'] = df['moisture_dirt']
        df_dirt['surface']  = 'ダート'

        combined = pd.concat([df_turf, df_dirt], ignore_index=True)
        combined = combined.sort_values(['date','venue','surface']).reset_index(drop=True)

        combined.to_excel(writer, index=False, sheet_name='含水率データ')

        # 統計サマリーシート
        summary = df.groupby('venue').agg(
            レース日数=('date', 'count'),
            芝含水率_平均=('moisture_turf', 'mean'),
            芝含水率_最小=('moisture_turf', 'min'),
            芝含水率_最大=('moisture_turf', 'max'),
            ダート含水率_平均=('moisture_dirt', 'mean'),
            クッション値_平均=('cushion', 'mean'),
        ).round(1).reset_index()
        summary.to_excel(writer, index=False, sheet_name='競馬場別サマリー')

    print(f"✅ {path} を生成しました（{len(combined)}行）")

def main():
    print("デモ用含水率データを生成中...")
    df = generate_demo_data()
    print(f"   生成レコード数: {len(df)}件（芝・ダート合計: {len(df)*2}行）")
    print(f"   期間: {df['date'].min()} 〜 {df['date'].max()}")
    print(f"   競馬場: {sorted(df['venue'].unique().tolist())}")

    save_to_excel(df)

    print("\n競馬場別サマリー:")
    print(df.groupby('venue').agg(
        件数=('date','count'),
        芝含水率平均=('moisture_turf','mean'),
        クッション値平均=('cushion','mean'),
    ).round(1).to_string())

if __name__ == '__main__':
    main()
