from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.game_factory as gf


class game(gg.grid_game_2d):
    def __init__(self, opts):
        super(game, self).__init__(opts)
        l = self.get_empty_loc()
        self.goal_loc = l
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        destination = 'ax' + str(l[0])+'y'+str(l[1])
        info = gi.build_info_attr('obj0 go absolute ' + destination)
        self.build_add_item(info)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.finished = False

    def update(self):
        super(game, self).update()
        l = self.goal_loc
        if self.agent.attr['loc'][0] == l[0] and self.agent.attr['loc'][0] == l[0]:
            self.finished = True


    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r

class factory(gf.game_factory):
    def __init__(self, game_name, game_opts, game):
        super(factory, self).__init__(game_name, game_opts, game)

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('obj0')
        vocab.append('go')
        vocab.append('absolute')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        for s in range(game_opts['range']['map_width'][3]):
            for t in range(game_opts['range']['map_height'][3]):
                vocab.append('ax' + str(s)+'x'+str(t))
                vocab.append('loc_x' + str(s)+'x'+str(t))
        return vocab

    def all_actions(self, game_opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('stop')
        return actions

if  __name__ == '__main__':
    opts = {'map_width':10,'map_height':10,
            'step_cost':-.1,'nblocks':3,
            'nwater':3}
    g = game(opts)
