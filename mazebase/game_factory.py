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
    W = game_opts['map_width'].max_possible()
    H = game_opts['map_height'].max_possible()
    for s in range(W):
        for t in range(H):
            vocab.append('ax' + str(s) + 'y' + str(t))


# default range option is specified as
# [current_min, current_max, min_max, max_max, increment]
# min_max, max_max, and increment are only used in curriculum

class GameOpt(object):
    def __init__(self, name, optvals):
        # if optvals is a scalar or list of lenegth 1, will
        # make static opt unaffected by curriculum
        self.name = name
        self.optvals = optvals
        self.static = True
        self.frozen = False
        self.type = None
        if type(optvals) == list:
            if len(optvals) > 1:
                self.static = False
            else:
                self.optvals = optvals[0]
            if type(optvals[0]) == float:
                self.type = 'float'
            else:
                self.type = 'int'

    def generate(self):
        if self.static:
            return self.optvals
        else:
            minval = self.optvals[0]
            maxval = self.optvals[1]
            if self.type == 'int':
                return random.randint(minval, maxval)
            else:
                return random.random()*(maxval-minval) + minval

    #easier and harder are defined by making the current
    #hardest easier or harder.  for different behaviors
    #sublcass
    def harder(self):
        if not self.static:
            if self.optvals[1] < self.optvals[3]:
                self.optvals[1] += self.optvals[4]
                self.optvals[1] = min(self.optvals[1], self.optvals[3])

    def easier(self):
        if not self.static:
            if self.optvals[1] > self.optvals[2]:
                self.optvals[1] -= self.optvals[4]
                self.optvals[1] = max(self.optvals[1], self.optvals[2])

    def hardest(self):
        if not self.static:
            self.optvals[1] = self.optvals[3]

    def easiest(self):
        if not self.static:
            self.optvals[1] = self.optvals[2]

    def is_hardest(self):
        if not self.static:
            return self.optvals[1] == self.optvals[3]
        else:
            return True

    def is_easiest(self):
        if not self.static:
            return self.optvals[1] == self.optvals[2]
        else:
            return True

    def can_make_harder(self):
        if self.static or self.frozen:
            return False
        if self.optvals[1] == self.optvals[3]:
            return False
        return True

    def can_make_easier(self):
        if self.static or self.frozen:
            return False
        if self.optvals[1] == self.optvals[2]:
            return False
        return True

    # halts curriculum on this option
    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False

    # these can be useful when building dictionaries:
    def max_possible(self):
        if self.static:
            return self.optvals
        else:
            return self.optvals[3]

    def min_possible(self):
        if self.static:
            return self.optvals
        else:
            return self.optvals[0]

# takes a dict of GameOpt objects indexed by their names
# and outputs a dict of options to feed to a game generator
def generate_opts(gopts):
    opts = {}
    for o in gopts:
        opts[o] = gopts[o].generate()
    return opts

# simple method to build a dictionary of GameOpt objects
# from a dictionary of with keys given by opt names
# values given either by static opt values or reange opts
# in a length 5 list in the 'standard' form
def opts_from_dict(dopts):
    game_opts = {}
    for opt_name in dopts:
        game_opts[opt_name] = GameOpt(opt_name, dopts[opt_name])
    return game_opts



# inputs into constructor:
# game_name is a string identifying the game.
# opts is a dictionary with the field:
#     game_opts, a dictionary of GameOpt objects
#     can use other fields if desired when subclassing
# game is the class for the game

class GameFactory(object):
    def __init__(self, game_name, opts, game):
        if game_name is None:
            self.empty = True
        else:
            self.empty = False
            g = {
                'game_opts': opts['game_opts'],
                'game': game,
                'opts_generator': generate_opts,
                'curriculum_frozen': False,
                'counters': {},
                'required_opts': ['map_width','map_height']
            }
            self.games = {game_name: g}
            self.reset_counters(game_name)
            self.ivocab = self.all_vocab(opts)
            self.iactions = self.all_actions(opts)
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

    def all_vocab(self, opts):
        raise NotImplementedError

    def all_actions(self, opts):
        raise NotImplementedError

    # default curriculum methods assumes a range option is
    # specified as [current_min, current_max, min_max, max_max, increment]
    # that is: to make a game harder, you increase the max of the possible
    # values for that option (but still allow the possibility that smaller
    # values might be generated)
    # to build a custom curriculum, you should subclass GameOpt, and
    # generate_opts() above

    def harder_random(self, gname):
        g = self.games[gname]
        gopts = g['game_opts']
        if g['curriculum_frozen']:
            return
        can_make_harder = []
        for i in gopts:
            if gopts[j].can_make_harder():
                can_make_harder.append(i)
        if len(can_make_harder) > 0:
            optname = random.choice(list(can_make_harder))
            gopts[optname].make_harder()

    def easier_random(self, gname):
        g = self.games[gname]
        gopts = g['game_opts']
        if g['curriculum_frozen']:
            return
        can_make_easier = []
        for i in gopts:
            if gopts[j].can_make_easier():
                can_make_easier.append(i)
        if len(can_make_easier) > 0:
            optname = random.choice(list(can_make_easier))
            gopts[optname].make_easier()

    def hardest(self, gname):
        gopts = self.games[gname]['game_opts']
        if self.games[gname]['curriculum_frozen']:
            return
        for opt in gopts:
            gopts[opt].hardest()

    def easiest(self, gname):
        gopts = self.games[gname]['game_opts']
        if self.games[gname]['curriculum_frozen']:
            return
        for opt in gopts:
            gopts[opt].easiest()

    def check_curriculum_state(self, gname):
        easiest = True
        hardest = True
        gopts = self.games[gname]['game_opts']
        for opt in gopts:
            hardest = gopts[opt].is_hardest() and hardest
            easiest = gopts[opt].is_hardest() and easiest
        if easiest:
            return -1
        elif hardest:
            return 1
        else:
            return 0

    def freeze_curriculum(self, gname):
        self.games[gname]['curriculum_frozen'] = True

    def unfreeze_curriculum(self, gname):
        self.games[gname]['curriculum_frozen'] = False

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

    def max_possible_opt(self, optname):
        M = -100000000000
        for g in self.games:
            o = self.games[g]['game_opts'].get(optname)
            if o is not None:
                v = o.max_possible()
                if type(v) == int:
                    M = int(max(M, v))
                elif type(v) == float:
                    M = max(M, v)
                else:
                    pass
        return M

    def check_opts(self):
        for g in self.games:
            ro = self.games[g]['required_opts']
            for o in ro:
                has_opt = False
                for opt in self.games[g]['game_opts']:
                    if opt == o:
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

    multigame_opts = {}
    multigame_opts['featurizer'] = {}
#    multigame_opts['featurizer']['abs_loc_vocab'] = True
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    goto_opts = {'game_opts': opts_from_dict(go_dict),
                 'featurizer':multigame_opts['featurizer']}
    multigame_opts['goto'] = goto_opts

    #####################################
    # switches:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    go_dict['nswitches'] = [3, 5, 3, 5, 1]
    go_dict['ncolors'] = [3, 3, 3, 3, 0]
    switches_opts = {'game_opts': opts_from_dict(go_dict),
                     'featurizer':multigame_opts['featurizer']}
    multigame_opts['switches'] = switches_opts

    ######################################
    F = goto.Factory('goto', multigame_opts['goto'], goto.Game)
    F += switches.Factory('switches', multigame_opts['switches'],
                          switches.Game)
    g = F.init_random_game()

