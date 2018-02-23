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
        self.nswitches = opts.get('nswitches') or 1
        self.ncolors = opts.get('ncolors') or 3
        info = gi.build_info_attr('go goal0')
        self.build_add_item(info)
        gi.build_big_random_wall(self)
        b = random.choice(self.items_bytype['block'])
        loc = b.attr['loc']
        self.remove_item(b)
        s = gi.PushableBlock({'loc': loc})
        self.add_prebuilt_item(s)
        gi.add_random_cycle_switches(self, self.nswitches, self.ncolors)
        # always goal0.  fixme?
        gi.add_goal(self, self.sample_reachable_loc(ensure_empty=True), 0)
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
        items = self.items_byloc[self.agent.attr['loc']]
        for i in items:
            gname = i.attr.get('@goal')
            if gname is not None:
                self.finished = True

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r
    
    def get_supervision(self, featurizer):
        gloc = self.items_bytype['goal'][0].attr['loc']
        aloc = self.agent.attr['loc']
        p, cost = dut.dijkstra_touch_cost(self, aloc, gloc)
        states = []
        actions = []
        if cost < dut.get_big_cost():# goal is on this side...
            path = dut.collect_path(p, gloc)
            actions = dut.path_to_actions(path)
            for a in actions:
                states.append(featurizer.featurize(self))
                self.act(a)
                self.update()
        else: # gonna have to move the block.
            #find where to push:
            bloc = self.items_bytype['pushable_block'][0].attr['loc']
            dw = round((aloc[0]-bloc[0])/(abs(aloc[0]-bloc[0]) + .01))
            dh = round((aloc[1]-bloc[1])/(abs(aloc[1]-bloc[1]) + .01))
            bw = bloc[0]
            bh = bloc[1]
            if self.is_loc_reachable((bw + dw, bh)):
                push_loc = (bw + dw, bh)
                hasspace = (self.is_loc_reachable((bw - dw, bh))
                            and self.is_loc_reachable((bw - 2*dw, bh)))
                if dw > 0:
                    push_direction = 'left'
                else:
                    push_direction = 'right'
            elif self.is_loc_reachable((bloc[0], bloc[1] + dh)):
                push_loc = (bloc[0], bloc[1] + dh)
                hasspace = (self.is_loc_reachable((bw, bh - dh))
                            and self.is_loc_reachable((bw , bh - 2*dh)))
                if dh > 0:
                    push_direction = 'down'
                else:
                    push_direction = 'up'
            else:#push loc is blocked, return with only 'stop'
                return [[featurizer.featurize(self), 'stop']]
            if not hasspace:
                return [[featurizer.featurize(self), 'stop']]
            p, bcost = dut.dijkstra_touch_cost(self, aloc, push_loc)
            path = dut.collect_path(p, push_loc)
            to_block = dut.path_to_actions(path)
            actions.extend(to_block)
            for a in to_block:
                states.append(featurizer.featurize(self))
                self.act(a)
                self.update()

            states.append(featurizer.featurize(self))
            self.act('push_' + push_direction)
            actions.append('push_' + push_direction)
            self.update()
            
            states.append(featurizer.featurize(self))
            self.act(push_direction)
            actions.append(push_direction)
            self.update()
            
            states.append(featurizer.featurize(self))
            self.act('push_' + push_direction)
            actions.append('push_' + push_direction)
            self.update()
            
            aloc = self.agent.attr['loc']
            p, cost = dut.dijkstra_touch_cost(self, aloc, gloc)
            if cost >= dut.get_big_cost():
                # goal still unreachable (e.g. blocks next to door or pushed block onto goal)
                # todo FIXME
                return [[states[0], 'stop']]                
            path = dut.collect_path(p, gloc)
            togoal = dut.path_to_actions(path)
            actions.extend(togoal)
            for a in togoal:
                states.append(featurizer.featurize(self))
                self.act(a)
                self.update()
                
        return list(zip(states, actions))


class Factory(gf.GameFactory):
    def __init__(self, game_name, opts, Game):
        super(Factory, self).__init__(game_name, opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks', 
              'nwater', 'nswitches')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, opts):
        game_opts = opts['game_opts']
        vocab = []
        vocab.append('info')
        vocab.append('obj0')
        vocab.append('switch')
        vocab.append('pushable_block')
        vocab.append('cycle_switch')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        vocab.append('goal')
        vocab.append('goal0')
        for s in range(game_opts['ncolors'].max_possible()):
            vocab.append('color' + str(s))
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
        'nblocks': 3,
        'nwater': 3
    }
    g = Game(opts)
    g.interactive_ascii()
