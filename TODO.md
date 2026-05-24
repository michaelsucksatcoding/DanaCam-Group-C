# TODO

## Backend fixes
- [x] Fix/replace corrupted `backend/config.py` (make sure it is valid Python and loads correct SQLite URI)

- [ ] Add repayment endpoint (likely `POST /api/loans/<loan_id>/repay`) to record Payment, set paid_at, update loan.status and totals

- [ ] Clean up overdue settlement late-fee arithmetic and ensure it reconciles with total_payable + Payment record
- [ ] (Optional) Add demo token checks so users can only operate on their own loans and admin endpoints require admin

## Testing
- [ ] Run backend and test: /api/health, register/login, apply loan, verify, approve, overdue settle, repay
- [ ] If frontend errors occur, align repayment endpoint path/payload with frontend contract

