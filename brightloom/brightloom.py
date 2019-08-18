from .helpers import get_date_intervals, flatten_orders
import pandas as pd
import requests

env_lookup = {
    'prod':     'https://api.eatsa.com/v1',
    'sandbox':  'http://api.sandbox.eatsa.com/v1'
}

class Brightloom(object):

    def __init__(self, api_key, env='prod'):
        ''' The Brightloom class provides a convenient wrapper for the Brightloom API

        :param api_key: Your Brightloom API key
        :type api_key: str

        :param brand_id: (Optional) set your Brand ID for use in all requests
        :type brand_id: str
        '''

        if env not in env_lookup.keys():
            raise Exception('env needs to be one of the following: {}'.format(', '.join(env_lookup.keys())))

        self.base_url = env_lookup[env]

        headers = {
            'X-AuthToken': api_key
        }
        self.session = requests.Session()
        self.session.headers.update(headers)

    def get_stores(self):

        url = '{base_url}/stores'.format(base_url=self.base_url)

        response = self._get(url=url)
        stores = response.json()['stores']

        return [Store(**{**store, **self.__dict__}) for store in stores]

    def _get(self, url, params=None):

        response = self.session.get(url, params=params)
        response_json = response.json()

        # handle pagination
        if 'total_pages' in response_json:
            total_pages = response.json()['total_pages']
            response = [response]
            page = 2
            while page <= total_pages:
                params['page_number'] = page
                next_page = self.session.get(url, params=params)
                response.append(next_page)
                page = page + 1

        return response


class Store(Brightloom):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_orders(self, created_at_start, created_at_end=None, day_chunk_size=30):
        ''' Get all orders for this location between the specified date range
        created_at_start <= order.created_at < created_at_end

        :param created_at_start: start of date range (string format 'YYYY-MM-DD')
        :type created_at_start: str

        :param created_at_end: start of date range (optional - if not set will get only created_at_start receipts)
        :type created_at_end: str
        '''

        url = '{base_url}/order-analytics'

        created_at_start = pd.to_datetime(created_at_start) - pd.DateOffset(1)
        created_at_end = pd.to_datetime(created_at_end) or created_at_start + pd.DateOffset(1)

        if pd.to_datetime(created_at_start) > pd.to_datetime(created_at_end):
            raise Exception('created_at_end must come after created_at_start')

        intervals = get_date_intervals(
            start_in=created_at_start,
            end_in=created_at_end,
            day_chunk_size=day_chunk_size
        )

        order_data = []
        for start, end in intervals:
            formatted_url = url.format(
                    base_url=self.base_url,
                )

            params = {
                'store_id': self.id,
                'created_at_after':start.strftime('%Y-%m-%d'),
                'created_at_before':end.strftime('%Y-%m-%d')
            }

            response = super()._get(formatted_url, params)
            # loop over responses because pagination is cool
            order_data.append([r.json()['orders'] for r in response])

        # flatten twice - once for pagination, once for the time interval iterations
        flat = [item for sublist in order_data for item in sublist]
        flat_flat = [item for sublist in flat for item in sublist]

        orders_data = flatten_orders(flat_flat)
        return orders_data
