You are working on a quantitative trading research and execution system.

GLOBAL RULES:
- Never invent data, stats, or results.
- If a value is not computed in code, say “not available”.
- No lookahead. Ever.
- Timezone is UTC+10 unless explicitly stated otherwise.
- Prefer simple, explicit logic over clever abstractions.
- Ask before changing schemas, session times, or R definitions.

DATA RULES:
- All session labels must be derivable at or before decision time.
- If a feature is only known after a session ends, it cannot be used intraday.
- Backtests must match live execution logic exactly.

CODE RULES:
- No silent behavior changes.
- When modifying logic, explain:
  1) What changed
  2) Why
  3) Impact on results
- Keep functions small and testable.
