class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

    def sendStatusKeys(self, cmd):

        #cmd.inform('{}={}'.format(key, value))
        pass

    def sendImage(self, filepath):

        self.logger.info('sendImage: {}'.format(filepath))
        #pass
