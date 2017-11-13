from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
import torch
import random
import grid_game as gg
import grid_item as gi
import standard_grid_actions
import game_factory as gf

class game(gg.grid_game_2d):
    def __init__(self, opts):
        super(game, self).__init__(opts)
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        self.nswitches = opts.get('nswitches') or 1
        self.ncolors = opts.get('ncolors') or 3
        info = gi.build_info_attr('go goal0')
        self.build_add_item(info)
        gi.build_big_random_wall(self)
        b = random.choice(self.items_bytype['block'])
        loc = b.attr['loc']
        self.remove_item(b)
        s = gi.cycle_switch_opened_door({'loc':loc}, 
                                    color = random.randint(0,self.ncolors-1))
        self.add_prebuilt_item(s)
        gi.add_random_cycle_switches(self,self.nswitches,self.ncolors)
        #always goal0.  fixme?
        gi.add_goal(self,self.get_empty_loc(), 0)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.agent.replace_action('toggle_close',
                                  standard_grid_actions.toggle_close)
        self.finished = False

    def update(self):
        super(game, self).update()
        self.finished = False
        items = self.items_byloc[self.agent.attr['loc']]
        for i in items:
            gname = i.attr.get('@goal')
            if gname is not None:  
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
        vocab.append('switch')
        vocab.append('cycle_switch_opened_door')
        vocab.append('cycle_switch')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('goal0')
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
    opts = {'map_width':12,'map_height':12,
            'step_cost':-.1,'water_cost':-.1, 'nblocks':3,
            'nwater':3}
    g = game(opts)
    g.interactive_ascii()
