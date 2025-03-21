import os
from vgwActor.export import export
from vgwActor.data_sink import DataSink

class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

        config = actor.actorConfig
        sinkConfig = config['data_sink']
        confpath = os.path.expandvars(sinkConfig['confpath'])
        hostname = sinkConfig['hostname']
        username = sinkConfig['username']
        topic = sinkConfig['topic']
        self.rdatadir = os.path.expandvars(sinkConfig['datadir'])
        self.datadir = os.path.expandvars(config['datadir'])
        self.data_sink = DataSink(confpath=confpath, hostname=hostname, username=username, topic=topic)

    def sendStatusKeys(self, cmd):

        #cmd.inform('{}={}'.format(key, value))
        pass

    def sendImage(self, filepath, prefix='', **kwargs):

        self.logger.info('sendImage: filepath={},prefix={}'.format(filepath, prefix))
        filename = os.path.basename(filepath)
        rdatapath = os.path.join(self.rdatadir, prefix + filename)
        datapath = os.path.join(self.datadir, prefix + filename)
        export(filepath, datapath, **kwargs)
        with self.data_sink.connect() as conn:
            try:
                conn.submit(rdatapath, os.path.getsize(datapath))
            except Exception as e:
                self.logger.warn(e)
