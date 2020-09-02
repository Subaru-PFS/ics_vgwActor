import fitsio


class Vgw:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

    def receiveStatusKeys(self, key):

        self.logger.info('receiveStatusKeys: {},{},{},{},{},{}'.format(
            key.actor,
            key.name,
            key.timestamp,
            key.isCurrent,
            key.isGenuine,
            [x.__class__.baseType(x) for x in key.valueList]
        ))

        if all((key.name == 'filepath', key.isCurrent, key.isGenuine)):
            data, header = fitsio.read(key.valueList[0], header=True)

    def sendStatusKeys(self, cmd):

        pass
