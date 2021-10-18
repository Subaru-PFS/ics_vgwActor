from vgwActor.export import export


class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

    def sendStatusKeys(self, cmd):

        #cmd.inform('{}={}'.format(key, value))
        pass

    def sendImage(self, filepath, **kwargs):

        self.logger.info('sendImage: {}'.format(filepath))
        export(filepath, '/dev/shm/vgw.fits', **kwargs)
