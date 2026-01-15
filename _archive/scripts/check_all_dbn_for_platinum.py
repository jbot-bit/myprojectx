"""Check ALL DBN files for platinum symbols"""
import databento as db
from pathlib import Path

dbn_folder = Path("dbn")
dbn_files = sorted(dbn_folder.glob("*.dbn.zst"))

print(f"Checking {len(dbn_files)} DBN files for platinum...")
print("="*80)

all_symbols = set()
platinum_found = []

for i, dbn_file in enumerate(dbn_files):
    try:
        store = db.DBNStore.from_file(str(dbn_file))
        df = store.to_df()

        if 'symbol' in df.columns:
            symbols = set(df['symbol'].unique())
            all_symbols.update(symbols)

            # Check for platinum in this file
            platinum = [s for s in symbols if 'MPL' in str(s).upper() or (str(s).startswith('PL') and len(str(s)) <= 5)]

            if platinum:
                print(f"\nFOUND PLATINUM in {dbn_file.name}:")
                print(f"  Platinum symbols: {sorted(platinum)}")
                platinum_found.extend(platinum)

        # Progress indicator
        if (i+1) % 10 == 0:
            print(f"  ...checked {i+1}/{len(dbn_files)} files")

    except Exception as e:
        print(f"  Error reading {dbn_file.name}: {e}")
        continue

print("\n" + "="*80)
print("FINAL RESULTS:")
print("="*80)

if platinum_found:
    print(f"SUCCESS - PLATINUM DATA FOUND!")
    print(f"Total platinum symbols: {len(set(platinum_found))}")
    print(f"Symbols: {sorted(set(platinum_found))}")
    print("\nYou can now run:")
    print("  python scripts/ingest_databento_dbn_mpl.py dbn")
else:
    print("NO PLATINUM DATA FOUND")
    print(f"Total instruments found: {len(all_symbols)}")
    print(f"Sample instruments: {sorted(list(all_symbols))[:30]}")

    # Check if any look like platinum
    possible_pl = [s for s in all_symbols if 'PL' in str(s).upper()]
    if possible_pl:
        print(f"\nInstruments with 'PL' in name (might be platinum): {sorted(possible_pl)[:20]}")
