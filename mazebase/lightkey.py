from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.distance_utils as dut
import mazebase.game_factory as gf
import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.standard_grid_actions as standard_grid_actions


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        self.goal_reward = 3.0
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
        s = gi.CycleSwitchOpenedDoor(
            {
                'loc': loc
            }, color=random.randint(0, self.ncolors - 1))
        self.add_prebuilt_item(s)
        gi.add_goal(self, self.sample_reachable_loc(ensure_empty=True), 0)
        gi.add_standard_items(self)

        # agent
        self.agent = self.items_bytype['agent'][0]
        self.agent.replace_action('toggle_close',
                                  standard_grid_actions.toggle_close)

        # whether switches added are reachable by the agent
        self.switch_reachable = gi.add_reachable_cycle_switches(
                self, self.nswitches, self.ncolors, self.agent.attr['loc'])
        #gi.add_random_cycle_switches(self, self.nswitches, self.ncolors)
        # always goal0.  fixme?

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
        if self.finished:
            r += self.goal_reward
        return r

    def get_supervision(self, featurizer, additional_featurizers=[]):
        gloc = self.items_bytype['goal'][0].attr['loc']
        path = []
        all_actions = []
        all_states = []
        num_featurizers = len(additional_featurizers)
        if num_featurizers > 0:
            additional_rep = [[]] * num_featurizers

        door = self.items_bytype['cycle_switch_opened_door'][0]
        p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], gloc)
        if cost >= dut.get_big_cost():
            # switch
            # note: order issue when multiple switches exist
            for switch in self.items_bytype['cycle_switch']:
                switch_loc = switch.attr['loc']
                p_switch, cost_switch = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], switch_loc)
                if cost_switch >= dut.get_big_cost():
                    if num_featurizers == 0:
                        return [[featurizer.featurize(self), 'stop']]
                    else:
                        feat_list = [f.featurize(self) for f in additional_featurizers]
                        return [[featurizer.featurize(self), 'stop', *feat_list]]
                path = dut.collect_path(p_switch, switch_loc)
                actions = dut.path_to_actions(path)
                for a in actions:
                    all_states.append(featurizer.featurize(self))
                    for i_f in range(num_featurizers):
                        additional_rep[i_f].append(additional_featurizers[i_f].featurize(self))
                    self.act(a)
                    self.update()
                all_actions += actions
                while switch.color != door.color:
                    all_states.append(featurizer.featurize(self))
                    for i_f in range(num_featurizers):
                        additional_rep[i_f].append(additional_featurizers[i_f].featurize(self))
                    all_actions.append('toggle_close')
                    self.act('toggle_close')
                    self.update()
        # go to destination after toggling all switches to the same color as door
        p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], gloc)
        path = dut.collect_path(p, gloc)
        actions = dut.path_to_actions(path)
        for a in actions:
            all_states.append(featurizer.featurize(self))
            for i_f in range(num_featurizers):
                additional_rep[i_f].append(additional_featurizers[i_f].featurize(self))
            self.act(a)
            self.update()
        all_actions += actions
        if num_featurizers == 0:
            return list(zip(all_states, all_actions))
        else:
            return list(zip(all_states, all_actions, *additional_rep))


class Factory(gf.GameFactory):
    def __init__(self, game_name, opts, Game):
        super(Factory, self).__init__(game_name, opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'water_cost', 'nblocks',
              'nwater', 'nswitches', 'ncolors')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, opts):
        game_opts = opts['game_opts']
        vocab = []
        vocab.append('info')
        vocab.append('corner')
        vocab.append('obj0')
        vocab.append('switch')
        vocab.append('cycle_switch_opened_door')
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
        actions.append('toggle_close')
        actions.append('stop')
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
