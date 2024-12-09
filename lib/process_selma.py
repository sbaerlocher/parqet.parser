import pandas as pd
import logging
import re

def extract_account_number_from_filename(filename):
    """
    Extracts the account number from the filename.

    Args:
        filename (str): The name of the file.

    Returns:
        str: Extracted account number or a default value if not found.
    """
    sanitized_filename = filename.replace(" ", "")
    match = re.search(r"CH\d+", sanitized_filename)
    return match.group(0) if match else "unknown_account"

def calculate_shares(dividend_row, trades):
    """
    Calculates the shares held for a given dividend record based on previous trades.

    Args:
        dividend_row (Series): The dividend row for which to calculate shares.
        trades (DataFrame): DataFrame containing trade records.

    Returns:
        float: The number of shares held for the given dividend record.
    """
    relevant_trades = trades[(trades['Date'] < dividend_row['Date']) & (trades['Fund'] == dividend_row['Fund'])]
    shares = relevant_trades.apply(lambda x: x['Number of Shares'] if x['Amount'] < 0 else -x['Number of Shares'], axis=1).sum()
    return max(0, shares) if shares > 0 else None

def process_cash_transfers(data, result, portfolio_number, config):
    cash_transfers = data[data['Description'] == 'cash_transfer'].copy()
    logging.info(f"Identified {cash_transfers.shape[0]} cash transfer entries.")

    for index, row in cash_transfers.iterrows():
        date_value = row.get('Date')
        if pd.isna(date_value):
            logging.warning(f"Invalid date in cash transfer row {index}: {row}")
            continue

        result["cash_transfers"].append({
            "datetime": date_value.strftime('%Y-%m-%dT00:00:00.000Z'),
            "date": date_value.strftime('%d.%m.%Y'),
            "time": "08:00:00",
            "price": 1,
            "shares": None,
            "amount": abs(float(row['Amount'])),
            "tax": 0,
            "fee": 0,
            "realizedgains": None,
            "type": "TransferIn",
            "broker": "Selma",
            "assettype": "Cash",
            "identifier": None,
            "wkn": None,
            "originalcurrency": row.get('Currency', "EUR"),
            "currency": row.get('Currency', "EUR"),
            "fxrate": None,
            "holding": config.get(portfolio_number, "hld_67522720e598d6de6f8c9bb5"),
            "holdingname": None,
            "holdingnickname": "Cash",
            "exchange": None,
            "avgholdingperiod": None
        })

def process_trades(data, result):
    trades = data[data['Description'] == 'trade'].copy()
    stamp_duties = data[data['Description'] == 'stamp_duty'].copy()
    logging.info(f"Identified {trades.shape[0]} trade entries and {stamp_duties.shape[0]} stamp duty entries.")

    stamp_duties_grouped = stamp_duties.groupby(['Date', 'Fund'])['Amount'].sum().reset_index()
    combined_data = pd.merge(trades, stamp_duties_grouped, on=['Date', 'Fund'], how='left', suffixes=('', '_stamp_duty'))

    combined_data['tax'] = combined_data['Amount_stamp_duty'].fillna(0).abs()

    for index, row in combined_data.iterrows():
        date_value = row.get('Date')
        if pd.isna(date_value) or pd.isna(row.get('Number of Shares')):
            logging.warning(f"Invalid trade row {index}: {row}")
            continue

        price = (abs(row['Amount']) / row['Number of Shares']) if row['Number of Shares'] > 0 else None
        result["trades"].append({
            "datetime": date_value.strftime('%Y-%m-%dT00:00:00.000Z'),
            "date": date_value.strftime('%d.%m.%Y'),
            "time": "09:00:00",
            "price": round(price, 2) if price else None,
            "shares": float(row['Number of Shares']),
            "amount": abs(float(row['Amount'])),
            "tax": row.get('tax', 0),
            "fee": 0,
            "realizedgains": 0,
            "type": 'Buy' if row['Amount'] < 0 else 'Sell',
            "broker": "Selma",
            "assettype": "Security",
            "identifier": row.get('Fund'),
            "wkn": None,
            "originalcurrency": row.get('Currency', "EUR"),
            "currency": row.get('Currency', "EUR"),
            "fxrate": None,
            "holding": None,
            "holdingname": None,
            "holdingnickname": None,
            "exchange": None,
            "avgholdingperiod": 0
        })

def process_dividends(data, trades, result):
    dividends = data[data['Description'] == 'dividend'].copy()
    withholding_taxes = data[(data['Description'] == 'withholding_tax') & (data['Amount'] < 0)].copy()
    logging.info(f"Identified {dividends.shape[0]} dividend entries and {withholding_taxes.shape[0]} withholding tax entries.")

    dividends_grouped = dividends.groupby(['Fund', 'Date']).agg({'Amount': 'sum', 'Currency': 'first'}).reset_index()
    withholding_taxes_grouped = withholding_taxes.groupby(['Fund', 'Date']).agg({'Amount': 'sum'}).reset_index()

    combined_dividends = pd.merge(dividends_grouped, withholding_taxes_grouped, on=['Fund', 'Date'], how='left', suffixes=('', '_withholding_tax'))
    combined_dividends['tax'] = combined_dividends['Amount_withholding_tax'].fillna(0).abs()

    for index, row in combined_dividends.iterrows():
        date_value = row.get('Date')
        if pd.isna(date_value):
            logging.warning(f"Invalid dividend row {index}: {row}")
            continue

        shares = calculate_shares(row, trades)
        if shares is None or row['Amount'] <= 0:
            logging.warning(f"Skipping dividend row with invalid shares or amount {index}: {row}")
            continue

        result["dividends"].append({
            "datetime": date_value.strftime('%Y-%m-%dT00:00:00.000Z'),
            "date": date_value.strftime('%d.%m.%Y'),
            "time": "00:00:00",
            "price": round(row['Amount'] / shares, 2) if shares > 0 else None,
            "shares": shares,
            "amount": abs(float(row['Amount'])),
            "tax": row.get('tax', 0),
            "fee": 0,
            "realizedgains": None,
            "type": "Dividend",
            "broker": "Selma",
            "assettype": "Security",
            "identifier": row.get('Fund'),
            "wkn": None,
            "originalcurrency": row.get('Currency', "EUR"),
            "currency": row.get('Currency', "EUR"),
            "fxrate": None,
            "holding": None,
            "holdingname": None,
            "holdingnickname": None,
            "exchange": None,
            "avgholdingperiod": None
        })

def process_selma_document(csv_path, config):
    try:
        logging.info(f"Processing Selma CSV file: {csv_path}")

        portfolio_number = extract_account_number_from_filename(csv_path)
        data = pd.read_csv(csv_path, sep=',', skip_blank_lines=True, skipinitialspace=True)
        logging.debug(f"Loaded data from Selma file {csv_path}: {data.head()}")

        required_columns = ["Date", "Description", "Bookkeeping No.", "Fund", "Amount", "Currency", "Number of Shares"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in the Selma CSV file: {', '.join(missing_columns)}")

        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')

        result = {
            "broker": "Selma",
            "trades": [],
            "portfolio_number": portfolio_number,
            "cash_transfers": [],
            "dividends": []
        }

        process_cash_transfers(data, result, portfolio_number, config)
        process_trades(data, result)
        process_dividends(data, data[data['Description'] == 'trade'].copy(), result)

        logging.debug(f"Processed Selma data: {result}")
        return result

    except Exception as e:
        logging.error(f"Error processing Selma file {csv_path}: {e}")
        return None
