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
        self.wrong_goal_cost = opts['wrong_goal_cost']
        
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
        info = gi.build_info_attr('info visit all excluding')
        self.build_add_item(info)
        goals = self.items_bytype['goal']
        self.finished_goals = {}
        for i in range(self.ngoals_active):
            self.finished_goals['goal' + str(self.goal_order[i])] = False
        for i in range(self.ngoals_active, self.ngoals):
            objective = 'info avoid goal' + str(self.goal_order[i])
            info = gi.build_info_attr(objective)
            self.build_add_item(info)
            goals[i].attr['_touch_cost'] = self.wrong_goal_cost
            
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
                if self.finished_goals.get(gname) is not None:
                    self.finished_goals[gname] = True
                    i.attr['_visited'] = True
                    if self.flag_visited:
                        i.attr['visited'] = True
                    if all(self.finished_goals.values()):
                        self.finished = True
                        break

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r

    def get_supervision(self, featurizer):
        states = []
        actions = []
        # this is greedy, not optimal:
        goal_remaining = True
        while goal_remaining:
            mincost = dut.get_big_cost() + 1
            goal_remaining = False
            for j in range(self.ngoals_active):
                aloc = self.agent.attr['loc']
                g = self.items_bytype['goal'][self.goal_order[j]]
                gloc = g.attr['loc']
                v = g.attr.get('_visited')
                if v is None or v is False:#why is v False?
                    goal_remaining = True
                    p, cost = dut.dijkstra_touch_cost(self, aloc, gloc)
                    if cost < mincost:
                        mincost = cost
                        mingloc = gloc
                        minp = p
            if mincost >= dut.get_big_cost(): # necessary goal is unreachable
                return [[featurizer.featurize(self), 'stop']]
            else:
                path = dut.collect_path(minp, mingloc)
                thisgoal_actions = dut.path_to_actions(path)
                actions.extend(thisgoal_actions)
                for a in thisgoal_actions:
                    states.append(featurizer.featurize(self))
                    self.act(a)
                    self.update()
        return list(zip(states, actions))

class Factory(gf.GameFactory):
    def __init__(self, game_name, opts, Game):
        super(Factory, self).__init__(game_name, opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks', 
              'nwater', 'nswitches', 'ngoals', 'ngoals_active', 'flag_visited',
              'wrong_goal_cost' )
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, opts):
        game_opts = opts['game_opts']
        vocab = []
        vocab.append('info')
        vocab.append('go')
        vocab.append('visit')
        vocab.append('all')
        vocab.append('excluding')
        vocab.append('avoid')
        vocab.append('switch')
        vocab.append('cycle_switch')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('goal')
        vocab.append('visited')
        for s in range(game_opts['ncolors'].max_possible()):
            vocab.append('color' + str(s))
        for s in range(game_opts['ngoals'].max_possible()):
            vocab.append('goal' + str(s))
        for s in range(game_opts['ngoals_active'].max_possible()):
            vocab.append('obj' + str(s))
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
        'nwater': 3,
        'wrong_goal_cost': -.5
        
    }
    g = Game(opts)
    g.interactive_ascii()
