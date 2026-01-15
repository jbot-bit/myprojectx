"""
Investigate why win rate DECREASES with wider stops (buffer increase)

This is counterintuitive - wider stops should have HIGHER win rates.
Let's find actual trade examples where outcome changed.
"""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*100)
print("BUFFER LOGIC INVESTIGATION")
print("="*100)
print()

# Find trades that changed outcome between buffer=0 and buffer=5
query = """
WITH buf0 AS (
    SELECT date_local, direction, entry_price, stop_price, stop_ticks, target_price, outcome
    FROM orb_trades_5m_exec
    WHERE orb = '1800' AND rr = 2.0 AND close_confirmations = 1
    AND sl_mode = 'half' AND buffer_ticks = 0
    AND outcome IN ('WIN', 'LOSS')
),
buf5 AS (
    SELECT date_local, direction, entry_price, stop_price, stop_ticks, target_price, outcome
    FROM orb_trades_5m_exec
    WHERE orb = '1800' AND rr = 2.0 AND close_confirmations = 1
    AND sl_mode = 'half' AND buffer_ticks = 5
    AND outcome IN ('WIN', 'LOSS')
)
SELECT
    buf0.date_local,
    buf0.direction,
    buf0.entry_price,
    buf0.stop_price as stop_buf0,
    buf5.stop_price as stop_buf5,
    buf0.stop_ticks as ticks_buf0,
    buf5.stop_ticks as ticks_buf5,
    buf0.outcome as outcome_buf0,
    buf5.outcome as outcome_buf5
FROM buf0
INNER JOIN buf5 ON buf0.date_local = buf5.date_local
WHERE buf0.outcome <> buf5.outcome
ORDER BY buf0.date_local
LIMIT 20
"""

trades = con.execute(query).fetchall()

print(f"Found {len(trades)} trades where outcome CHANGED between buffer=0 and buffer=5")
print("-"*100)
print()

if len(trades) > 0:
    print("Date       | Dir  | Entry   | Stop(buf=0) | Stop(buf=5) | Ticks(0) | Ticks(5) | Out(0) | Out(5)")
    print("-"*100)
    for t in trades:
        date, direction, entry, stop0, stop5, ticks0, ticks5, out0, out5 = t
        stop_diff = stop5 - stop0 if direction == "DOWN" else stop0 - stop5
        print(f"{date} | {direction:>4} | {entry:>7.1f} | {stop0:>11.1f} | {stop5:>11.1f} | {ticks0:>8.1f} | {ticks5:>8.1f} | {out0:>6} | {out5:>6}")

    print()
    print("-"*100)
    print("ANALYSIS OF OUTCOME CHANGES:")
    print("-"*100)

    # Count changes
    win_to_loss = sum(1 for t in trades if t[7] == 'WIN' and t[8] == 'LOSS')
    loss_to_win = sum(1 for t in trades if t[7] == 'LOSS' and t[8] == 'WIN')

    print(f"WIN -> LOSS: {win_to_loss} trades")
    print(f"LOSS -> WIN: {loss_to_win} trades")
    print()

    if win_to_loss > loss_to_win:
        print(">>> PROBLEM: More WINS becoming LOSSES than vice versa")
        print("    This explains why win rate DECREASES with buffer")
        print()
        print("    This is COUNTERINTUITIVE because wider stops should prevent stop-outs.")
        print("    Possible explanations:")
        print("    1. Bug in backtest logic (buffer applied incorrectly)")
        print("    2. Entry price or ORB calculation differs between runs")
        print("    3. Different trades being taken due to MAX_STOP filter")
    elif loss_to_win > win_to_loss:
        print(">>> EXPECTED: More LOSSES becoming WINS than vice versa")
        print("    This is what SHOULD happen with wider stops")
    else:
        print(">>> NEUTRAL: Equal swaps in both directions")

else:
    print("No outcome changes found. Investigating why win rate differs...")
    print()

    # Maybe different trades are being taken?
    count0 = con.execute("""
        SELECT COUNT(*) FROM orb_trades_5m_exec
        WHERE orb = '1800' AND rr = 2.0 AND close_confirmations = 1
        AND sl_mode = 'half' AND buffer_ticks = 0
        AND outcome IN ('WIN', 'LOSS')
    """).fetchone()[0]

    count5 = con.execute("""
        SELECT COUNT(*) FROM orb_trades_5m_exec
        WHERE orb = '1800' AND rr = 2.0 AND close_confirmations = 1
        AND sl_mode = 'half' AND buffer_ticks = 5
        AND outcome IN ('WIN', 'LOSS')
    """).fetchone()[0]

    print(f"Buffer=0: {count0} trades")
    print(f"Buffer=5: {count5} trades")
    print(f"Difference: {count5 - count0} trades")

print()
print("="*100)

con.close()
