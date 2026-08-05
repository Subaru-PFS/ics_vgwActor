#!/usr/bin/env python

import opscore.protocols.keys as keys


class VgwCmd:
    def __init__(self, actor):
        self.actor = actor
        self.vocab = [
            ("ping", "", self.ping),
            ("status", "", self.status),
            ("show", "", self.show),
        ]
        self.keys = keys.KeysDictionary(
            "vgw_vgw",
            (1, 1),
        )

    def ping(self, cmd):
        """Return a product name."""
        cmd.inform(f'text="{self.actor.productName}"')
        cmd.finish()

    def status(self, cmd):
        """Return status keywords."""
        self.actor.sendVersionKey(cmd)
        self.actor.vgw.sendStatusKeys(cmd)
        cmd.finish()

    def show(self, cmd):
        """Show status keywords from all models."""
        for n in self.actor.models:
            try:
                d = self.actor.models[n].keyVarDict
                for _k, v in d.items():
                    cmd.inform(f'text="{v!r}"')
            except Exception as e:
                cmd.warn(f'text="VgwCmd.show: {n}: {e}"')
        cmd.finish()
