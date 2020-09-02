#!/usr/bin/env python

import argparse
from actorcore.Actor import Actor
from vgwActor.vgw import Vgw


class VgwActor(Actor):

    # Keyword arguments for this class
    _kwargs = {
    }

    def __init__(self, name, **kwargs):

        # Consume keyword arguments for this class
        for k in VgwActor._kwargs:
            if k in kwargs:
                setattr(self, '_' + k, kwargs[k])
                del kwargs[k]
            else:
                setattr(self, '_' + k, VgwActor._kwargs[k])

        super().__init__(name, **kwargs)

        self._everConnected = False

    def reloadConfiguration(self, cmd):

        pass

    # override
    def connectionMade(self):

        if not self._everConnected:

            self._everConnected = True

            self.vgw = Vgw(actor=self, logger=self.logger)

            _models = ('ag', 'agcam',)
            self.addModels(_models)
            self.models['agcam'].keyVarDict['filepath'].addCallback(self.vgw.receiveStatusKeys, callNow=False)

    # override
    def connectionLost(self, reason):

        pass

    # override
    def commandFailed(self, cmd):

        pass


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--configFile', default=None)
    args = parser.parse_args()

    actor = VgwActor(
        'vgw',
        productName='vgwActor',
        configFile=args.configFile
    )
    actor.run()


if __name__ == '__main__':

    main()
