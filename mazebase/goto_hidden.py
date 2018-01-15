from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.game_factory as gf
import mazebase.distance_utils as dut


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        self.ngoals = opts['ngoals']
        self.goal_locs = []
        for s in range(self.ngoals):
            loc = self.sample_reachable_loc(ensure_empty=True)
            destination = 'ax' + str(loc[0]) + 'y' + str(loc[1])
            info = gi.build_info_attr('goal' + str(s) + ' at absolute ' + destination)
            self.build_add_item(info)
            #add actual goals to prevent duplicate locs as in original mb
            # don't really need this?
            self.goal_locs.append(loc)
            gi.add_goal(self, loc, s)
            self.items_bytype['goal'][s].attr['_invisible'] = True
        gid = random.randint(0, self.ngoals - 1)
        info = gi.build_info_attr('obj0 go goal' + str(gid))
        self.build_add_item(info)        
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.finished = False
        self.goal_loc = self.items_bytype['goal'][gid].attr['loc']

    def update(self):
        super(Game, self).update()
        location = self.goal_loc
        if (self.agent.attr['loc'][0] == location[0]
                and self.agent.attr['loc'][1] == location[1]):
            self.finished = True

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r

    def get_supervision(self, featurizer):
        gloc = self.goal_loc
        p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], gloc)
        if cost >= dut.get_big_cost():
            return [[featurizer.featurize(self), 'stop']]
        path = dut.collect_path(p, gloc)
        actions = dut.path_to_actions(path)
        states = []
        for a in actions:
            states.append(featurizer.featurize(self))
            self.act(a)
            self.update()
        return list(zip(states, actions))

class Factory(gf.GameFactory):
    def __init__(self, game_name, game_opts, Game):
        super(Factory, self).__init__(game_name, game_opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'nblocks', 'nwater',
              'ngoals', 'water_cost')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('corner')
        vocab.append('obj0')
        vocab.append('at')
        vocab.append('go')
        vocab.append('absolute')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        gf.add_absolute_loc_vocab(vocab, game_opts)
        for s in range(game_opts['range']['ngoals'][3]):
            vocab.append('goal' + str(s))
        return vocab

    def all_actions(self, game_opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('stop')
        return actions


if __name__ == '__main__':
    import mazebase.featurizer as sf
    opts = {
        'map_width': 10,
        'map_height': 10,
        'step_cost': -.1,
        'nblocks': 3,
        'nwater': 3,
        'ngoals': 3
    }
    g = Game(opts)
    #FIXME ngoals
    F = Factory('goto',
                {'static': {'step_cost': -.1, 'nwater': 5, 'water_cost': -.2},
                 'featurizer': {},
                 'range': {'ngoals': [5,5,5,5,0], 'map_width': [10,10,10,10,0],
                           'map_height': [10,10,10,10,0]}},
                Game)
    feat = sf.SentenceFeaturizer({'egocentric_coordinates': True,
                                  'visible_range': 5},
                                 F.dictionary)
    g.interactive_ascii()
