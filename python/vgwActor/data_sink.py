from contextlib import contextmanager
import logging
import os
import time
from datasink.client import JobSource


class DataSink:

    def __init__(self, *, confpath=None, hostname=None, username=None, password=None, topic=None, **kwargs):

        self.hostname = hostname
        self.username = username
        self.password = password
        self.topic = topic

        self.job_source = JobSource(logging.getLogger(topic), topic)
        self.job_source.read_config(confpath)

    @contextmanager
    def connect(self):

        self.job_source.connect()
        try:
            yield self
        finally:
            self.job_source.shutdown()

    def submit(self, datapath):

        job = dict(
            action='transfer',
            srcpath=datapath,
            reqtime=time.time(),
            host=self.hostname,
            transfermethod='scp',
            username=self.username,
            password=self.password,
            topic=self.topic,
            filesize=os.stat(datapath).st_size
        )
        self.job_source.submit(job)


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--conf-path', default='pfsag.yml', help='configuration filepath')
    parser.add_argument('--data-path', required=True, help='data filepath')
    parser.add_argument('--cadence', type=float, default=None, help='cadence (s)')
    args, _ = parser.parse_known_args()

    import traceback

    data_sink = DataSink(confpath=args.conf_path, hostname='133.40.147.5', username='pfs', topic='pfs_ag')
    while True:
        with data_sink.connect() as conn:
            try:
                conn.submit(args.data_path)
            except:
                traceback.print_exc()
        if args.cadence is None:
            break
        time.sleep(args.cadence)
