from tornado import ioloop, httpclient
import settings
import logging
import time
import functools
from collections import deque
from lib.utils import urlencode

class sendgrid:
    def __init__(self, loop=None):
        self.ioloop = loop or ioloop.IOLoop.instance()
        self.http_client = httpclient.AsyncHTTPClient(io_loop=self.ioloop)
        self.http_client.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.write_queue = deque()
        self.started = time.time()
        self.concurrent = 0
        self.max_concurrent = 5
        self.error_level = 0
        self.stats = {
            'sends':0,
            'failures':0,
            'successes':0,
        }
        self.sweeper = ioloop.PeriodicCallback(self.run_sweeper, 1000*1, self.ioloop)
        self.sweeper.start()

    def run_sweeper(self):
        if not self.error_level:
            while len(self.write_queue) and self.concurrent != self.max_concurrent:
                o = self.write_queue.popleft()
                self.send(o['data'], o['account'])
        else:
            self.error_level -= 1

    def get_stats(self):
        stats = self.stats.copy()
        stats['queue_len'] = len(self.write_queue)
        stats['error_level'] = self.error_level
        stats['concurrent'] = self.concurrent
        stats['uptime'] = time.time() - self.started
        return stats

    def send(self, data, account='default'):
        if self.error_level:
            self.write_queue.append(dict(data=data,account=account))
        else:
            self.concurrent += 1
            self.stats['sends'] += 1
            acc = settings.get('accounts').get('account')
            self.http_client.fetch(acc.get('sendgrid_url'),
                functools.partial(self._finish_send, data=data, account=account),
                follow_redirects=False, method="POST", body=urlencode(data, doseq=1),
                validate_cert=False, connect_timeout=5, request_timeout=10)

    def _finish_send(self, response, data, account):
        self.concurrent -= 1
        if response.error:
            self.stats['failures'] += 1
            if response.code != 400:
                self.write_queue.appendleft(dict(data=data,account=account))
                self.error_level = min(settings.get('max_backoff') or 15, (self.error_level + 1 + self.error_level/2))
            logging.exception("send failed", response.error)
            if response.buffer: print response.buffer.getvalue()
        else:
            self.stats['successes'] += 1
            body = response.buffer.getvalue()
