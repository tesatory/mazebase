from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import mazebase.grid_game as gg
import mazebase.grid_item as gi
import mazebase.game_factory as gf
import mazebase.distance_utils as dut


class Game(gg.GridGame2D):
    def __init__(self, opts):
        super(Game, self).__init__(opts)
        self.goal_loc = self.sample_reachable_loc(ensure_empty=True)
        if opts.get('fixed_goal'):
            self.goal_loc = (0,0)
        self.nblocks = int(opts.get('nblocks') or 0)
        self.nwater = int(opts.get('nwater') or 0)
        destination = 'ax' + str(self.goal_loc[0]) + 'y' + str(self.goal_loc[1])
        info = gi.build_info_attr('obj0 go absolute ' + destination)
        self.build_add_item(info)
        gi.add_standard_items(self)
        self.agent = self.items_bytype['agent'][0]
        self.finished = False

    def update(self):
        super(Game, self).update()
        location = self.goal_loc
        if (self.agent.attr['loc'][0] == location[0]
                and self.agent.attr['loc'][1] == location[1]):
            self.finished = True

    def get_reward(self):
        r = self.opts['step_cost']
        r += self.agent.touch_cost()
        return r

    def get_supervision(self, featurizer):
        gloc = self.goal_loc
        p, cost = dut.dijkstra_touch_cost(self, self.agent.attr['loc'], gloc)
        if cost >= dut.get_big_cost():
            return [[featurizer.featurize(self), 'stop']]
        path = dut.collect_path(p, gloc)
        actions = dut.path_to_actions(path)
        states = []
        for a in actions:
            states.append(featurizer.featurize(self))
            self.act(a)
            self.update()
        return list(zip(states, actions))

class Factory(gf.GameFactory):
    def __init__(self, game_name, game_opts, Game):
        super(Factory, self).__init__(game_name, game_opts, Game)
        ro = ('map_width', 'map_height', 'step_cost', 'nblocks', 'nwater',
              'water_cost', 'fixed_goal')
        self.games[game_name]['required_opts'] = ro

    def all_vocab(self, game_opts):
        vocab = []
        vocab.append('info')
        vocab.append('corner')
        vocab.append('obj0')
        vocab.append('go')
        vocab.append('absolute')
        vocab.append('block')
        vocab.append('water')
        vocab.append('agent')
        vocab.append('agent0')
        if game_opts['featurizer'].get('abs_loc_vocab'):
            gf.add_absolute_loc_vocab(vocab, game_opts)
        if game_opts['static'].get('fixed_goal'):
            vocab.append('ax0y0')
        else:
            gf.add_absolute_loc_vocab(vocab, game_opts)
        return vocab

    def all_actions(self, game_opts):
        actions = []
        actions.append('up')
        actions.append('down')
        actions.append('left')
        actions.append('right')
        actions.append('stop')
        return actions


if __name__ == '__main__':
    import mazebase.featurizer as sf
    opts = {
        'map_width': 10,
        'map_height': 10,
        'step_cost': -.1,
        'nblocks': 3,
        'nwater': 3
    }
    g = Game(opts)
    F = Factory('goto',
                {'static': {'map_width': 10, 'map_height': 10, 'step_cost': -.1,
                            'nblocks': 5, 'nwater': 5, 'water_cost': -.2,
                            'fixed_goal': False}, 'featurizer': {}},
                Game)
    feat = sf.SentenceFeaturizer({'egocentric_coordinates': True,
                                  'visible_range': 5},
                                 F.dictionary)
