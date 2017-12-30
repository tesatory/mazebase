from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.standard_grid_actions as standard_grid_actions
import mazebase.game_factory as gf
import mazebase.distance_utils as dut



class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        #these are decoys:
        self.nswitches = opts.get('nswitches') or 0
        self.ncolors = opts.get('ncolors') or 3

        self.ngoals = opts['ngoals']
        self.ngoals_active = min(opts['ngoals_active'], self.ngoals)
        
        self.ngoals_reached = 0
        self.goal_order = [i for i in  range(self.ngoals)]
        random.shuffle(self.goal_order)        
        for i in range(self.ngoals):
            gi.add_goal(self, self.sample_reachable_loc(ensure_empty=True), i)
        for i in range(self.ngoals_active):
            objective = 'obj' + str(i) +  ' go goal' + str(self.goal_order[i])
            info = gi.build_info_attr(objective)
            self.build_add_item(info)
        self.current_goal = 'goal' + str(self.goal_order[0])

        gi.add_random_cycle_switches(self, self.nswitches, self.ncolors)
        gi.add_standard_items(self)
        self.finished = False
        #TODO breadcrumb action
        self.flag_visited = False
        if opts['flag_visited'] == 1:
            self.flag_visited = True
        self.agent = self.items_bytype['agent'][0]

    def update(self):
        super(Game, self).update()
        self.finished = False
        items = self.items_byloc[self.agent.attr['loc']]
        for i in items:
            gname = i.attr.get('@goal')
            if gname is not None:
                if gname == self.current_goal:
                    self.ngoals_reached += 1
                    if self.flag_visited:
                        i.attr['visited'] = True
                    if self.ngoals_reached == self.ngoals_active:
                        self.finished = True
                        break
                    else:
                        self.current_goal = ('goal' +
                            str(self.goal_order[self.ngoals_reached]))

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r

    def get_supervision(self, featurizer):
        states = []
        actions = []
        for i in range(self.ngoals_active):
            current_goal = 'goal' + str(self.goal_order[i])
            for j in self.items_bytype['goal']:
                if j.attr['@goal'] == current_goal:
                    gloc = j.attr['loc']
            p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], gloc)
            if cost >= dut.get_big_cost():
                return [[featurizer.featurize(self), 'stop']]
            else:
                path = dut.collect_path(p, gloc)
                thisgoal_actions = dut.path_to_actions(path)
                actions.extend(thisgoal_actions)
                for a in thisgoal_actions:
                    states.append(featurizer.featurize(self))
                    self.act(a)
                    self.update()
        return list(zip(states, actions))

class Factory(gf.GameFactory):
    def __init__(self, game_name, game_opts, Game):
        super(Factory, self).__init__(game_name, game_opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks', 
              'nwater', 'nswitches', 'ngoals', 'ngoals_active', 'flag_visited')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('go')
        vocab.append('switch')
        vocab.append('cycle_switch')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('goal')
        vocab.append('visited')
        for s in range(game_opts['range']['ncolors'][3]):
            vocab.append('color' + str(s))
        for s in range(game_opts['range']['ngoals'][3]):
            vocab.append('goal' + str(s))
        for s in range(game_opts['range']['ngoals_active'][3]):
            vocab.append('obj' + str(s))            
        if game_opts['featurizer'].get('abs_loc_vocab'):
            gf.add_absolute_loc_vocab(vocab, game_opts)
        return vocab

    def all_actions(self, game_opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('stop')
        #TODO breadcrumb
        return actions


if __name__ == '__main__':
    opts = {
        'map_width': 12,
        'map_height': 12,
        'step_cost': -.1,
        'water_cost': -.1,
        'ngoals':5,
        'ngoals_active':3,
        'flag_visited':1,
        'nblocks': 3,
        'nwater': 3
    }
    g = Game(opts)
    g.interactive_ascii()
