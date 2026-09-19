# Settrade full-SET50 collection result

The current 2026 H2 universe is recorded as exactly 50 symbols. The authenticated official SDK probe covered quote, daily candlestick, and 1m/5m/15m candlestick access for every symbol. The bounded collector then stored recent 1m bars and derived 5m/15m bars in the pilot-only storage root.

Realtime evidence is intentionally limited to four topics for PTT and ADVANC. The observed bid/offer payload exposed ten bid and ten ask levels; the configured hard ceiling remains 40 topics. Realtime rotation for a production-like collector requires an explicit operator decision and must keep each connection at or below that ceiling.

The Settrade `volume`/`value` semantics are retained as source fields but remain unresolved for cross-source conversion. No volume ratio or artificial turnover conversion is applied.
