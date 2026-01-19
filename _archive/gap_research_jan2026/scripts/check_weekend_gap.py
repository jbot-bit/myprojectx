import duckdb
import pandas as pd

conn = duckdb.connect('C:/Users/sydne/OneDrive/myprojectx/gold.db')

result = conn.execute("""
    SELECT ts_utc, open, high, low, close
    FROM bars_1m
    WHERE symbol='MGC'
        AND ts_utc >= '2026-01-10'
        AND ts_utc <= '2026-01-15'
    ORDER BY ts_utc
""").fetchdf()

print(f'Total bars: {len(result)}')
print('\nFirst 10 bars:')
print(result.head(10).to_string())
print('\nLast 10 bars:')
print(result.tail(10).to_string())

result['time_diff_min'] = result['ts_utc'].diff().dt.total_seconds() / 60
gaps = result[result['time_diff_min'] > 60]

print(f'\n\nGaps found: {len(gaps)}')
if len(gaps) > 0:
    print('\nGap details:')
    for idx, gap in gaps.iterrows():
        prev_idx = idx - 1
        if prev_idx >= 0 and prev_idx in result.index:
            prev_close = result.loc[prev_idx, 'close']
            gap_open = gap['open']
            gap_size = gap_open - prev_close
            print(f'\nGap at {gap["ts_utc"]}:')
            print(f'  Previous close: {prev_close:.1f}')
            print(f'  Gap open: {gap_open:.1f}')
            print(f'  Gap size: {gap_size:.1f}')

            # Check subsequent price action
            future_bars = result[result['ts_utc'] > gap['ts_utc']]
            if len(future_bars) > 0:
                max_high = future_bars['high'].max()
                min_low = future_bars['low'].min()
                print(f'  Subsequent high: {max_high:.1f}')
                print(f'  Subsequent low: {min_low:.1f}')

                if gap_size > 0:  # UP gap
                    filled = min_low <= prev_close
                    print(f'  Gap filled? {filled}')
                else:  # DOWN gap
                    filled = max_high >= prev_close
                    print(f'  Gap filled? {filled}')

conn.close()
