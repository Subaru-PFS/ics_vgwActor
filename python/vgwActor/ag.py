import numpy


class Ag:

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

        if all((key.name == 'data', key.isCurrent, key.isGenuine)):
            ra, dec, pa = (float(x) for x in key.valueList[:3])
            guide_objects, detected_objects, identified_objects = (numpy.load(str(x)) for x in key.valueList[3:])
            filepath = self.actor.agcc.filepath
            self.actor.vgw.sendImage(filepath, center=(ra, dec, pa), guide_objects=guide_objects, detected_objects=detected_objects, identified_objects=identified_objects)

    def _getValues(self, key):

        valueList = self.actor.models['ag'].keyVarDict[key].valueList
        return {x.name: x.__class__.baseType(x) for x in valueList} if len(valueList) > 1 else valueList[0].__class__.baseType(valueList[0])

    @property
    def guideReady(self):

        return self._getValues('guideReady')

    @property
    def detectionState(self):

        return self._getValues('detectionState')
