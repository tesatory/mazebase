from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.standard_grid_actions as standard_grid_actions
import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.game_factory as gf


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        self.goal_reward = 3.0
        self.goal_loc = self.sample_reachable_loc(ensure_empty=True)
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        self.explicit = opts.get('explicit') or False
        self.nswitches = opts.get('nswitches') or 2
        self.ncolors = opts.get('ncolors') or 2
        if self.explicit:
            self.target_color = random.randint(0, self.ncolors)
            tcs = 'color' + str(self.target_color)
        else:
            self.target_color = -1
            tcs = 'same'

        info = gi.build_info_attr('obj0 switch color ' + tcs)
        self.build_add_item(info)
        gi.add_random_cycle_switches(self, self.nswitches, self.ncolors)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.agent.replace_action('toggle_close',
                                  standard_grid_actions.toggle_close)
        self.finished = False

    def update(self):
        super(Game, self).update()
        self.finished = True
        if not self.explicit:
            self.target_color = self.items_bytype['cycle_switch'][0].color
        for s in self.items_bytype['cycle_switch']:
            if s.color != self.target_color:
                self.finished = False

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        if self.finished:
            r += self.goal_reward
        return r

class Factory(gf.GameFactory):
    def __init__(self, game_name, opts, Game):
        super(Factory, self).__init__(game_name, opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks',
              'nwater', 'explicit', 'nswitches', 'ncolors')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, opts):
        game_opts = opts['game_opts']
        vocab = []
        vocab.append('info')
        vocab.append('corner')
        vocab.append('obj0')
        vocab.append('switch')
        vocab.append('cycle_switch')
        vocab.append('color')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('same')
        feat_opts = opts.get('featurizer')
        if (feat_opts is not None) and feat_opts.get('abs_loc_vocab'):
            gf.add_absolute_loc_vocab(vocab, game_opts)
        for s in range(game_opts['ncolors'].max_possible()):
            vocab.append('color' + str(s))
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
        'water_cost': -.2,
        'nblocks': 3,
        'nwater': 3
    }
    g = Game(opts)
    g.interactive_ascii()
