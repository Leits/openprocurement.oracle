# -*- coding: utf-8 -*-
import unittest
import uuid
from openprocurement.edge.databridge import Oracle, ConfigError
from mock import MagicMock, patch

import datetime
import io
import logging
from requests.exceptions import ConnectionError

logger = logging.getLogger()
logger.level = logging.DEBUG

test_tender_data = {
    'status': 'active.auction.decrypt'
    'id': 1
    'bids': [
        {'id': 33, 'key': "super_key1"},
        {'id': 44, 'key': "super_key2"},
        {'id': 55, 'key': "super_key3"}
    ]
}


class TestEdgeDataBridge(unittest.TestCase):
    config = {
        'main': {
            'tenders_api_server': 'https://lb.api-sandbox.openprocurement.org',
            'tenders_api_version': "0",
        },
        'version': 1
    }

    def test_run(self):
        log_string = io.BytesIO()
        stream_handler = logging.StreamHandler(log_string)
        logger.addHandler(stream_handler)

        oracle = Oracle(self.config)
        mock_tender = {'data': test_tender_data}
        mock_bid = {'data': 'yep'}
        oracle.client.get_tender = MagicMock(return_value=mock_tender)
        oracle.client.patch_bid = MagicMock(return_value=mock_bid)
        tid = uuid.uuid4().hex
        oracle.get_teders_list = MagicMock(return_value=[[tid, datetime.datetime.utcnow().isoformat()]])
        oracle.run()
        del oracle.db[tid]

        logger.removeHandler(stream_handler)
        log_string.close()



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEdgeDataBridge))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
