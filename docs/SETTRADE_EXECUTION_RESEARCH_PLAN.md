# Settrade execution research boundary

The pilot has authenticated only market-data surfaces. No account object was initialized, no account number was requested, and no order method was called. Safe next research is limited to documenting sandbox order schemas, order-type/IOC constraints, rejection handling, and paper execution through `src/execution/settrade_paper.py`.

Human approval is required before any account integration, continuous licensed retention, or order submission is enabled. Real-money orders remain prohibited for this phase.
