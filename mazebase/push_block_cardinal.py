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
        self.ncolors = opts.get('ncolors') or 3
        self.nswitches = 1
        gi.add_random_cycle_switches(self, self.nswitches, self.ncolors)
        color = self.items_bytype['cycle_switch'][0].attr['@color']
        direction = random.choice(['up', 'down', 'right', 'left'])
        self.direction = direction
        info = gi.build_info_attr('info push block ' + direction)
        self.build_add_item(info)
        loc = self.sample_reachable_loc(ensure_empty=True)
        s = gi.PushableBlock({'loc': loc})
        self.add_prebuilt_item(s)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.agent.replace_action('push_up', standard_grid_actions.push_up)
        self.agent.replace_action('push_down', standard_grid_actions.push_down)
        self.agent.replace_action('push_left', standard_grid_actions.push_left)
        self.agent.replace_action('push_right',
                                  standard_grid_actions.push_right)
        self.finished = False

    def update(self):
        super(Game, self).update()
        self.finished = False
        ploc = self.items_bytype['pushable_block'][0].attr['loc']
        if self.direction == 'up':
            if ploc[1] == self.mapsize[1] - 1:
                self.finished = True
        if self.direction == 'down':
            if ploc[1] == 0:
                self.finished = True
        if self.direction == 'right':
            if ploc[0] == self.mapsize[0] - 1:
                self.finished = True
        if self.direction == 'left':
            if ploc[0] == 0:
                self.finished = True

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r


    #this is super greedy... TODO fix to at least try multiple equivalent paths
    # if block is stuck
    def get_supervision(self, featurizer):
        self.featurizer = featurizer
        a = self.agent
        b = self.items_bytype['pushable_block'][0]
        cost, goal_loc, p = self.find_good_goal()
        states = []
        actions = []
        if cost < dut.get_big_cost():
            path = dut.collect_path(p, goal_loc)
            if len(path) <= 1: 
                return [[featurizer.featurize(self), 'stop']]
            path = path[1:]
            #TODO fix easy mistakes
            for loc in path:
                #TODO put get_push_location into pushable_block object
                actions, states, success = self.go_and_push(loc, actions, states)
                if not success:
                    return [[featurizer.featurize(self), 'stop']]
                
        return list(zip(states, actions))
    
    def get_push_location(self, block_loc, target_loc):
        loc = (block_loc[0] + block_loc[0] - target_loc[0],
               block_loc[1] + block_loc[1] - target_loc[1])
        return loc

    def find_good_goal(self):
        b = self.items_bytype['pushable_block'][0]
        mincost = dut.get_big_cost()
        if self.direction == 'up':
            for i in range(self.mapsize[0]):                
                p, cost = dut.dijkstra_touch_cost(self,
                                b.attr['loc'], (i, self.mapsize[1]-1))
                if cost < mincost:
                    mincost = cost
                    goal_loc = (i, self.mapsize[1]-1)
                    minp = p
        elif self.direction == 'down':
            for i in range(self.mapsize[0]):                
                p, cost = dut.dijkstra_touch_cost(self,
                                b.attr['loc'], (i, 0))
                if cost < mincost:
                    mincost = cost
                    goal_loc = (i, 0)
                    minp = p
        elif self.direction == 'right':
            for i in range(self.mapsize[1]):                
                p, cost = dut.dijkstra_touch_cost(self,
                                b.attr['loc'], (self.mapsize[0] - 1, i))
                if cost < mincost:
                    mincost = cost
                    goal_loc = (self.mapsize[0] - 1, i)
                    minp = p
        else:
            for i in range(self.mapsize[1]):                
                p, cost = dut.dijkstra_touch_cost(self,
                                b.attr['loc'], (0, i))
                if cost < mincost:
                    mincost = cost
                    goal_loc = (0, i)
                    minp = p
        return mincost, goal_loc, minp

    def go_and_push(self, next_block_loc, actions, states):
        b = self.items_bytype['pushable_block'][0]
        pl = self.get_push_location(b.attr['loc'], next_block_loc)
        p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], pl)
        if cost < dut.get_big_cost():
            path_to_push = dut.collect_path(p, pl)
        else:
            return actions, states, False
        to_push_loc = dut.path_to_actions(path_to_push)
        actions.extend(to_push_loc)
        for a in to_push_loc:
            states.append(self.featurizer.featurize(self))
            self.act(a)
            self.update()
        if pl[0] < b.attr['loc'][0]:
            a = 'push_right'
        elif pl[1] < b.attr['loc'][1]:
            a = 'push_up'
        elif pl[0] > b.attr['loc'][0]:
            a = 'push_left'
        else:
            a = 'push_down'
        actions.append(a)
        states.append(self.featurizer.featurize(self))
        self.act(a)
        self.update()
        return actions, states, True
        
class Factory(gf.GameFactory):
    def __init__(self, game_name, game_opts, Game):
        super(Factory, self).__init__(game_name, game_opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks', 
              'nwater')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('up')
        vocab.append('down')
        vocab.append('left')
        vocab.append('right')
        vocab.append('switch')
        vocab.append('pushable_block')
        vocab.append('cycle_switch')
        vocab.append('switch')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        for s in range(game_opts['range']['ncolors'][3]):
            vocab.append('color' + str(s))
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
        actions.append('push_left')
        actions.append('push_right')
        actions.append('push_up')
        actions.append('push_down')
        return actions


if __name__ == '__main__':
    opts = {
        'map_width': 12,
        'map_height': 12,
        'step_cost': -.1,
        'water_cost': -.1,
        'nblocks': 8,
        'nwater': 3
    }
    g = Game(opts)
    g.interactive_ascii()
