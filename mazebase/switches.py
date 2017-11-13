from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.standard_grid_actions
import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.game_factory as gf


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        l = self.get_empty_loc()
        self.goal_loc = l
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        self.explicit = opts.get('explicit') or False
        self.nswitches = opts.get('nswitches') or 2
        self.ncolors = opts.get('ncolors') or 2
        if self.explicit:
            self.target_color = random.randint(0,self.ncolors)
            tcs = 'color'+ str(self.target_color)
        else:
            self.target_color = -1
            tcs = 'same'

        info = gi.build_info_attr('obj0 switch color ' + tcs)
        self.build_add_item(info)
        gi.add_random_cycle_switches(self,self.nswitches,self.ncolors)
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
        return r


class Factory(gf.GameFactory):
    def __init__(self, game_name, game_opts, Game):
        super(Factory, self).__init__(game_name, game_opts, Game)

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('obj0')
        vocab.append('switch')
        vocab.append('cycle_switch')
        vocab.append('color')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('same')
        for s in range(game_opts['range']['ncolors'][3]):
            vocab.append('color' + str(s))
        for s in range(game_opts['range']['map_width'][3]):
            for t in range(game_opts['range']['map_height'][3]):
                vocab.append('loc_x' + str(s)+'x'+str(t))

        return vocab

    def all_actions(self, game_opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('toggle_close')
        actions.append('stop')
        return actions


if  __name__ == '__main__':
    opts = {'map_width':10,'map_height':10,
            'step_cost':-.1,'water_cost':-.1, 'nblocks':3,
            'nwater':3}
    g = Game(opts)
