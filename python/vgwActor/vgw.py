import os
from vgwActor.export import export
from vgwActor.data_sink import DataSink


class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger
        self.data_sink = DataSink(confpath=os.path.expandvars('$ICS_VGWACTOR_DIR/etc/pfsag.yml'), hostname='133.40.147.5', username='pfs', topic='pfs_ag')

    def sendStatusKeys(self, cmd):

        #cmd.inform('{}={}'.format(key, value))
        pass

    def sendImage(self, filepath, **kwargs):

        self.logger.info('sendImage: {}'.format(filepath))
        datapath = os.path.expandvars('$ICS_MHS_DATA_ROOT/vgw/pfsag.fits')
        export(filepath, datapath, **kwargs)
        with self.data_sink.connect() as conn:
            try:
                conn.submit(datapath)
            except Exception as e:
                self.logger.warn(e)
