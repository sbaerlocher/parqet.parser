"""Transaction data type processors."""

from app.lib.data_types.trades import process_trades
from app.lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from app.lib.data_types.dividends import process_dividends
from app.lib.data_types.interest import process_interest
from app.lib.data_types.fees import process_fees

__all__ = [
    "process_trades",
    "process_deposits_withdrawals",
    "process_dividends",
    "process_interest",
    "process_fees",
]
