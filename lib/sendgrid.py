from tornado import ioloop, httpclient
import settings
import logging
import urllib
import time
import math
import functools
from collections import deque

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
                self.send(self.write_queue.popleft())
        else:
            self.error_level -= 1

    def get_stats(self):
        stats = self.stats.copy()
        stats['queue_len'] = len(self.write_queue)
        stats['error_level'] = self.error_level
        stats['concurrent'] = self.concurrent
        stats['uptime'] = time.time() - self.started
        return stats

    def send(self, data):
        if self.error_level:
            self.write_queue.append(data)
        else:
            self.concurrent += 1
            self.stats['sends'] += 1
            self.http_client.fetch(settings.get('sendgrid_url'),
                functools.partial(self._finish_send, data=data),
                follow_redirects=False, method="POST", body = urllib.urlencode(data, doseq=1),
                validate_cert=False, connect_timeout=5, request_timeout=10)

    def _finish_send(self, response, data):
        print "FINISH", response
        self.concurrent -= 1
        if response.error:
            self.stats['failures'] += 1
            if response.code != 400:
                self.write_queue.appendleft(data)
                self.error_level += (1 + self.error_level/2)
            logging.exception("send failed", response.error)
            if response.buffer: print response.buffer.getvalue()
        else:
            self.stats['successes'] += 1
            body = response.buffer.getvalue()
            print "BODY", body

