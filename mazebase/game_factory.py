from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

# featurizer implements egocentric vs absolute coords
# the factory stores the vocab of all the games for the benefit of
# featurizers

# todo curriculum
# todo save and load vocab and action lists

def add_absolute_loc_vocab(vocab, game_opts):
    for s in range(game_opts['range']['map_width'][3]):
        for t in range(game_opts['range']['map_height'][3]):
            vocab.append('ax' + str(s) + 'y' + str(t))

# default range option is specified as 
# [current_min, current_max, min_max, max_max, increment]
# min_max, max_max, and increment are only used in curriculum

def generate_opts(gopts):
    opts = {}
    for s in gopts['static']:
        opts[s] = gopts['static'][s]
    for s in gopts['range']:
        minval = gopts['range'][s][0]
        maxval = gopts['range'][s][1]
        if type(minval) == int:
            opts[s] = random.randint(minval, maxval)
        else:
            opts[s] = random.uniform(minval, maxval)
    return opts


class GameFactory(object):
    def __init__(self, game_name, game_opts, game):
        if game_name is None:
            self.empty = True
        else:
            self.empty = False
            g = {
                'game_opts': game_opts,
                'game': game,
                'opts_generator': generate_opts
            }
            g['counters'] = {}
            g['required_opts'] = ['map_width','map_height']
            self.games = {game_name: g}        
            self.reset_counters(game_name)
            self.ivocab = self.all_vocab(game_opts)
            self.iactions = self.all_actions(game_opts)
            self.sort_vocabs()

    def sort_vocabs(self):
        self.ivocab.sort()
        self.vocab = dict([[self.ivocab[i], i]
                           for i in range(len(self.ivocab))])
        self.iactions.sort()
        self.actions = dict([[self.iactions[i], i]
                             for i in range(len(self.iactions))])
        self.dictionary = {'vocab':self.vocab,'ivocab':self.ivocab}

    def init_game(self, gname):
        g = self.games[gname]
        opts = g['opts_generator'](g['game_opts'])
        game = g['game'](opts)
        game.factory_name = gname
        return game

    def init_random_game(self):
        gname = random.choice(list(self.games.keys()))
        return self.init_game(gname)

    def all_vocab(self, game_opts):
        raise NotImplementedError

    def all_actions(self, game_opts):
        raise NotImplementedError

    # default curriculum methods assumes a range option is 
    # specified as [current_min, current_max, min_max, max_max, increment]
    # that is: to make a game harder, you increase the max of the possible
    # values for that option (but still allow the possibility that smaller
    # values might be generated)
    # to build a custom curriculum, you should override harder_random(), 
    # easier_random(), check_hardness(), hardest(), easiest(), and probably the function
    # generate_opts() above

    def harder_random(self, gname):
        gopts = self.games[gname]['game_opts']
        if gopts.get('curriculm_frozen'):
            return
        range_opts = gopts['range']
        opt = random.choice(list(range_opts))
        range_opts[opt][1] += range_opts[opt][4]
        range_opts[opt][1] = min(range_opts[opt][1], range_opts[opt][3])

    def easier_random(self, gname):
        gopts = self.games[gname]['game_opts']
        if gopts.get('curriculm_frozen'):
            return
        range_opts = gopts['range']
        opt = random.choice(list(range_opts))
        range_opts[opt][1] -= range_opts[opt][4]
        range_opts[opt][1] = max(range_opts[opt][1], range_opts[opt][2])

    def hardest(self, gname):
        gopts = self.games[gname]['game_opts']
        if gopts.get('curriculm_frozen'):
            return
        for opt in gopts['range']:
            gopts['range'][opt][1] = gopts['range'][opt][3]

    def easiest(self, gname):
        gopts = self.games[gname]['game_opts']
        if gopts.get('curriculm_frozen'):
            return
        for opt in gopts['range']:
            gopts['range'][opt][1] = gopts['range'][opt][2]

    def check_curriculum_state(self, gname):
        easiest = True
        hardest = True
        gopts = self.games[gname]['game_opts']
        for opt in gopts['range']:
            if gopts['range'][opt][1] < gopts['range'][opt][3]:
                hardest = False
            if gopts['range'][opt][1] > gopts['range'][opt][2]:
                easiest = False
        if easiest:
            return -1
        elif hardest: 
            return 1
        else:
            return 0        

    def freeze_curriculum(self, gname):
        self.games[gname]['game_opts']['curriculum_frozen'] = True

    def unfreeze_curriculum(self, gname):
        self.games[gname]['game_opts']['curriculum_frozen'] = False

    def collect_results(self, gname, r):
        results = self.games[gname]['counters']
        results['total_count'] += 1
        results['success_count'] += r
        
    #error if no results?
    def success_pct(self, gname):
        results = self.games[gname]['counters']
        return results['success_count']/results['total_count']

    def total_count(self, gname):
        return self.games[gname]['counters']['total_count']

    def reset_counters(self, gname):
        self.games[gname]['counters'] = {'success_count':0,'total_count':0}

    def check_opts(self):
        for g in self.games:
            ro = self.games[g]['required_opts']
            for o in ro:
                has_opt = False
                for opt_type in self.games[g]['game_opts']:
                    for opt_name in self.games[g]['game_opts'][opt_type]:
                        if opt_name == o:
                            has_opt = True
                if not has_opt:
                    print('warning, game "' + g + '" has option "' + o + '" registered as required but that option is not in its game_opts') 
            #todo check the other way around for extraneous opts in game_opts
            #todo eventually do this right?
        

    def __add__(self, other):
        if other.empty:
            return self
        if self.empty:
            return other
        for i in other.games:
            if not self.games.get(i):
                self.games[i] = other.games[i]
            else:
                newname = i + str(random.randint(0,100000))
                self.games[newname] = other.games[i]
        self.ivocab = list(set(self.ivocab) | set(other.ivocab))
        self.iactions = list(set(self.iactions) | set(other.iactions))
        self.sort_vocabs()
        return self


if __name__ == '__main__':
    import mazebase.goto as goto
    import mazebase.switches as switches

    game_opts = {}
    game_opts['featurizer'] = {}
#    game_opts['featurizer']['abs_loc_vocab'] = True
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = [5, 10, 5, 10, 1]
    range_opts['map_height'] = [5, 10, 5, 10, 1]
    range_opts['nblocks'] = [1, 5, 1, 5, 1]
    range_opts['nwater'] = [1, 5, 1, 5, 1]
    go['range'] = range_opts

    go['featurizer'] = game_opts['featurizer']

    game_opts['goto'] = go

    #####################################
    # switches:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = [5, 10, 5, 10, 1]
    range_opts['map_height'] = [5, 10, 5, 10, 1]
    range_opts['nblocks'] = [1, 5, 1, 5, 1]
    range_opts['nwater'] = [1, 5, 1, 5, 1]
    range_opts['nswitches'] = [3, 5, 3, 5, 1]
    range_opts['ncolors'] = [3, 3, 3, 3, 0]
    go['range'] = range_opts

    go['featurizer'] = game_opts['featurizer']

    game_opts['switches'] = go

    ######################################
    F = goto.Factory('goto', game_opts['goto'], goto.Game)
    F += switches.Factory('switches', game_opts['switches'],
                          switches.Game)
    g = F.init_random_game()
