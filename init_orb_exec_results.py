import duckdb

DB_PATH = "gold.db"

def main():
    con = duckdb.connect(DB_PATH)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orb_exec_results (
            date_local DATE NOT NULL,
            instrument VARCHAR NOT NULL,
            orb_time VARCHAR NOT NULL,        -- '0900','1000','1100','1800','2300','0030'
            variant VARCHAR NOT NULL,         -- e.g. '1m_close_1', '1m_close_2', '1m_close_3'
            dir VARCHAR,                      -- 'UP'/'DOWN' (NULL if no trade)

            entry_ts TIMESTAMP WITH TIME ZONE,
            entry_price DOUBLE,
            stop_price DOUBLE,
            target_price DOUBLE,

            risk_ticks DOUBLE,
            target_ticks DOUBLE,

            outcome VARCHAR,                  -- 'WIN','LOSS','NO_TRADE','SKIP'
            r_multiple DOUBLE,

            notes VARCHAR,

            PRIMARY KEY (date_local, instrument, orb_time, variant, dir)
        );
    """)

    con.close()
    print("[OK] orb_exec_results ready")

if __name__ == "__main__":
    main()
