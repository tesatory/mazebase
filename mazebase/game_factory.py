from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

#featurizer implements egocentric vs absolute coords
#the factory stores the vocab of all the games for the benefit of
#featurizers

#todo curriculum
#todo save and load vocab and action lists


def generate_opts(gopts):
    opts = {}
    for s in gopts['static']:
        opts[s] = gopts['static'][s]
    for s in gopts['range']:
        minval = gopts['range'][s][0]
        maxval = gopts['range'][s][1]
        if type(minval) == int:
            opts[s] =random.randint(minval,maxval)
        else:
            opts[s] =random.uniform(minval,maxval)
    return opts


class game_factory(object):
    def __init__(self, game_name, game_opts, game):
        g = {'game_opts':game_opts,'game':game,'opts_generator':generate_opts}
        self.games = {game_name:g}
        self.ivocab = self.all_vocab(game_opts)
        self.iactions = self.all_actions(game_opts)
        self.sort_vocabs()

    def sort_vocabs(self):
        self.ivocab.sort()
        self.vocab = dict([[self.ivocab[i],i] for i in range(len(self.ivocab))])
        self.iactions.sort()
        self.actions = dict([[self.iactions[i],i] for i in range(len(self.iactions))])

    def init_game(self,gname):
        g = self.games[gname]
        opts = g['opts_generator'](g['game_opts'])
        return g['game'](opts)

    def init_random_game(self):
        gname = random.choice(list(self.games.keys()))
        return self.init_game(gname)

    def all_vocab(self, game_opts):
        raise NotImplementedError

    def all_actions(self, game_opts):
        raise NotImplementedError

    def __add__(self, other):
        for i in other.games:
            self.games[i] = other.games[i]
        self.ivocab = list(set(self.ivocab) | set(other.ivocab))
        self.iactions = list(set(self.iactions) | set(other.iactions))
        self.sort_vocabs()
        return self

if  __name__ == '__main__':
    import switches
    import goto

    games = {}

    game_opts = {}
    game_opts['multigames']  = {}
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    #goto:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = (5,10,5,10,1)
    range_opts['map_height'] = (5,10,5,10,1)
    range_opts['nblocks'] = (1,5,1,5,1)
    range_opts['nwater'] = (1,5,1,5,1)
    go['range'] = range_opts

    game_opts['multigames']['goto'] = go

#    games['goto'] = (goto.game, goto.factory_interface)

    #####################################
    #switches:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = (5,10,5,10,1)
    range_opts['map_height'] = (5,10,5,10,1)
    range_opts['nblocks'] = (1,5,1,5,1)
    range_opts['nwater'] = (1,5,1,5,1)
    range_opts['nswitches'] = (3,5,3,5,1)
    range_opts['ncolors'] = (3,3,3,3,0)
    go['range'] = range_opts

    game_opts['multigames']['switches'] = go

#    games['switches'] = (switches.game, switches.factory_interface)

    ######################################
    F = goto.factory('goto', game_opts['multigames']['goto'], goto.game)
    F += switches.factory('switches', game_opts['multigames']['switches'], switches.game)
