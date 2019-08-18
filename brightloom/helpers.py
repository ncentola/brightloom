from pandas.io.json import json_normalize
import pandas as pd

def get_date_intervals(start_in, end_in, day_chunk_size):
    freq_var = '{}D'.format(day_chunk_size)
    td_start = '{} days'.format(day_chunk_size)

    days_apart = (end_in-start_in).days
    n_periods = pd.np.ceil(days_apart / day_chunk_size)

    start = start_in
    intervals = []
    for delta in pd.timedelta_range(start=td_start, periods=n_periods, freq=freq_var):
        if start_in + delta > end_in:
            end = end_in
        else:
            end = start_in + delta
        intervals.append((start, end))
        start = end + pd.DateOffset(1)

    return intervals

def flatten_orders(orders):
    line_items = []
    applied_taxes = []
    modifications = []

    for order in orders:

        for tax in order['applied_taxes']:
            tax['order_id'] = order['id']
            applied_taxes.append(tax)

        for line_item in order['line_items']:
            line_item['order_id'] = order['id']
            line_items.append(line_item)

            for modification in line_item['modifications']:
                modification['line_item_id'] = line_item['id']
                modifications.append(modification)

    orders_df = json_normalize(orders, sep='_')
    line_items_df = pd.DataFrame(line_items)
    applied_taxes_df = pd.DataFrame(applied_taxes)
    modifications_df = pd.DataFrame(modifications)

    orders_data = {
        'orders':           orders_df,
        'line_items':       line_items_df,
        'applied_taxes':    applied_taxes_df,
        'modifications':    modifications_df,
    }
    return orders_data
