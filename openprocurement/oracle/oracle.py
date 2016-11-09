from gevent import monkey
monkey.patch_all()

try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass

import logging
import logging.config
import os
import argparse
from yaml import load
from urlparse import urljoin
from couchdb import Database, Session, ResourceNotFound
from openprocurement_client.sync import get_tenders
from openprocurement_client.client import TendersClient
import errno
from socket import error
from requests.exceptions import ConnectionError, MissingSchema

logger = logging.getLogger(__name__)


DB = {}


class ConfigError(Exception):
    pass

class Oracle(object):

    def __init__(self, config):
        super(Oracle, self).__init__()
        self.config = config
        self.api_host = self.config_get('tenders_api_server')
        self.api_version = self.config_get('tenders_api_version')
        self.retrievers_params = self.config_get('retrievers_params')

        self.db = DB

        try:
            self.client = TendersClient(host_url=self.api_host,
                api_version=self.api_version, key=''
            )
        except MissingSchema:
            raise ConfigError('In config dictionary empty or missing \'tenders_api_server\'')
        except ConnectionError as e:
            raise e

    def config_get(self, name):
        try:
            return self.config.get('main').get(name)
        except AttributeError as e:
            raise ConfigError('In config dictionary missed section \'main\'')


    def get_teders_list(self):
        for item in get_tenders(host=self.api_host, version=self.api_version,
                                key='', extra_params={'mode': '_all_', 'opt_fields': 'status'},
                                retrievers_params=self.retrievers_params):
            yield (item["id"], item["status"])

    def approve_bids(self, tender_id, date_modified):
        # TODO: At this point must be get_bids
        if self.db[tender['id']] == tender['status']:
            continue
        tender = self.client.get_tender(tender_id).get('data')
        if not tender:
            logger.info('Tender {} not found'.format(tender_id))
            continue

        for bid in tender['bids']:
            doc_id = "{}_{}".format(tender['id'], bid['id'])
            if self.db[doc_id] == tender['status']:
                continue
            shard_key = "Oracle approve: " + bid['key']
            self.client.patch_bid(tender['id'], bid['id'], {'data': {"shard": shard_key}})
            self.db[doc_id] = tender['status']
            self.db[tender['id']] = tender['status']

    def run(self):
        logger.info('Start Oracle',
                    extra={'MESSAGE_ID': 'start_oracle'})
        logger.info('Start data sync...',
                    extra={'MESSAGE_ID': 'oracle__data_sync'})
        for tender_id, status in self.get_teders_list():
            self.aporove_bids(tender_id, date_modified)


def main():
    parser = argparse.ArgumentParser(description='---- Oracle ----')
    parser.add_argument('config', type=str, help='Path to configuration file')
    params = parser.parse_args()
    if os.path.isfile(params.config):
        with open(params.config) as config_file_obj:
            config = load(config_file_obj.read())
        logging.config.dictConfig(config)
        Oracle(config).run()


##############################################################

if __name__ == "__main__":
    main()
