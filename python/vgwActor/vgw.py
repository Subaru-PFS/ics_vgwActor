import os
from vgwActor.export import export
from vgwActor.data_sink import DataSink


class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger
        confpath = os.path.expandvars(actor.config.get('data_sink', 'confpath'))
        hostname = actor.config.get('data_sink', 'hostname')
        username = actor.config.get('data_sink', 'username')
        topic = actor.config.get('data_sink', 'topic')
        self.rdatadir = os.path.expandvars(actor.config.get('data_sink', 'datadir'))
        self.datadir = os.path.expandvars(actor.config.get(actor.name, 'datadir'))
        self.data_sink = DataSink(confpath=confpath, hostname=hostname, username=username, topic=topic)

    def sendStatusKeys(self, cmd):

        #cmd.inform('{}={}'.format(key, value))
        pass

    def sendImage(self, filepath, **kwargs):

        self.logger.info('sendImage: {}'.format(filepath))
        filename = os.path.basename(filepath)
        rdatapath = os.path.join(self.rdatadir, filename)
        datapath = os.path.join(self.datadir, filename)
        export(filepath, datapath, **kwargs)
        with self.data_sink.connect() as conn:
            try:
                conn.submit(rdatapath, os.path.getsize(datapath))
            except Exception as e:
                self.logger.warn(e)
