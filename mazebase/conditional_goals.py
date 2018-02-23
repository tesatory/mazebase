from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.standard_grid_actions as standard_grid_actions
import mazebase.game_factory as gf


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)

        self.ngoals = opts.get('ngoals') or 2
        for i in range(self.ngoals):
            gi.add_goal(self, self.sample_reachable_loc(ensure_empty=True), i)
        self.ncolors = opts.get('ncolors') or 2
        gi.add_random_cycle_switches(self, 1, self.ncolors)
        self.cmap = []
        for s in range(self.ncolors):
            g = random.randint(0, self.ngoals - 1)
            self.cmap.append(g)
            info = gi.build_info_attr('if cycle_switch color ' + 'color' +
                                      str(s) + ' go goal' + str(g))
            self.build_add_item(info)

        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.agent.replace_action('toggle_close',
                                  standard_grid_actions.toggle_close)
        self.finished = False

    def update(self):
        super(Game, self).update()
        self.finished = False
        items = self.items_byloc[self.agent.attr['loc']]
        c = self.items_bytype['cycle_switch'][0].color
        g = self.cmap[c]
        for i in items:
            gname = i.attr.get('@goal')
            if gname is not None:
                if int(gname[4:]) == g:
                    self.finished = True

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r


class Factory(gf.GameFactory):
    def __init__(self, game_name, opts, Game):
        super(Factory, self).__init__(game_name, opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks', 
              'nwater', 'ngoals', 'nswitches', 'ncolors')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, opts):
        game_opts = opts['game_opts']
        vocab = []
        vocab.append('if')
        vocab.append('info')
        vocab.append('go')
        vocab.append('cycle_switch')
        vocab.append('color')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        for s in range(game_opts['ncolors'].max_possible()):
            vocab.append('color' + str(s))
        for s in range(game_opts['ngoals'].max_possible()):
            vocab.append('goal' + str(s))
        feat_opts = opts.get('featurizer')
        if (feat_opts is not None) and feat_opts.get('abs_loc_vocab'):
            gf.add_absolute_loc_vocab(vocab, game_opts)
        return vocab

    def all_actions(self, opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('toggle_close')
        actions.append('stop')
        return actions


if __name__ == '__main__':
    opts = {
        'map_width': 10,
        'map_height': 10,
        'step_cost': -.1,
        'water_cost': -.1,
        'nblocks': 3,
        'nwater': 3,
        'ngoals': 5,
        'ncolors': 3
    }
    g = Game(opts)
