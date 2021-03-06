from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


class SentenceFeaturizer(object):
    def __init__(self, opts, dictionary = None):
        self.opts = opts
        self.load_dictionary(dictionary)
        if self.opts.get('egocentric_coordinates'):
            assert(opts.get('visible_range') is not None)

    def load_dictionary(self, dictionary):
        self.dictionary = dictionary
        if not (self.opts.get('separate_loc')):
            self.adjust_dictionary()

    def adjust_dictionary(self):
        if self.dictionary is None:
            return
        if self.opts.get('egocentric_coordinates'):
            vrange = self.opts['visible_range']
            for s in range(-vrange+1,vrange):
                for t in range(-vrange+1,vrange):
                    w = 'rx' + str(s) + 'y' + str(t)
                    self.dictionary['ivocab'].append(w)
                    self.dictionary['vocab'][w] = len(self.dictionary['ivocab']) - 1

    def to_sentence_item(self, item, agent_loc = None):
        if item.attr.get('_invisible'):
            return None
        s = []
        item_loc = item.attr.get('loc')
        if item_loc is None:
            if self.opts.get('separate_loc'):
                # TODO: handle it correctly
                return None
        else:
            if self.opts.get('egocentric_coordinates'):
                loc = (item_loc[0]-agent_loc[0], item_loc[1]-agent_loc[1])
                if abs(loc[0]) < self.opts['visible_range'] and abs(loc[1]) < self.opts['visible_range']:
                    if self.opts.get('separate_loc'):
                        item_loc = (loc[0] + self.opts['visible_range'] - 1,
                                    loc[1] + self.opts['visible_range'] - 1)
                    else:
                        s.append('rx' + str(loc[0]) + 'y' + str(loc[1]))
                else:
                    return None
            elif not self.opts.get('separate_loc'):
                s.append('ax' + str(item_loc[0]) + 'y' + str(item_loc[1]))
        for i in item.attr:
            if i == 'loc':
                continue
            elif i[0] != '_':
                if i[0] != '@':
                    # flag
                    s.append(i)
                else:
                    # categorial
                    s.append(item.attr[i])
        if self.opts.get('separate_loc'):
            return (s, item_loc)
        else:
            return s

    def to_sentence(self, game, agent = None):
        if agent is not None:
            agent_loc = agent.attr['loc']
        else:
            agent_loc = None
        s = []
        for i in game.items:
            w = self.to_sentence_item(i, agent_loc)
            if w is not None:
                s.append(w)
        return s

    def featurize(self, game):
        return self.to_sentence(game, agent = game.agent)


if __name__ == '__main__':
    import mazebase.goto as goto
    import mazebase.switches as switches
    import mazebase.game_factory as gf

    games = {}
    opts = {}
    opts['featurizer'] = {}
#    opts['featurizer']['abs_loc_vocab'] = True
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['fixed_goal'] = True
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    goto_opts = {'game_opts': gf.opts_from_dict(go_dict),
                'featurizer': opts['featurizer']}
    opts['goto'] = goto_opts
    games['goto'] = goto

    #####################################
    # switches:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    go_dict['nswitches'] = [3, 5, 3, 5, 1]
    go_dict['ncolors'] = [3, 3, 3, 3, 0]

    switches_opts = {'game_opts': gf.opts_from_dict(go_dict),
                'featurizer': opts['featurizer']}
    opts['switches'] = switches_opts
    games['switches'] = switches


    ######################################
    F = goto.Factory('goto', opts['goto'], goto.Game)
    F += switches.Factory('switches', opts['switches'],
                          switches.Game)

    featurizer_opts = {'egocentric_coordinates': True, 'visible_range': 5}
    SF = SentenceFeaturizer(featurizer_opts, F.dictionary)
    g = F.init_random_game()
    print(SF.to_sentence(g, g.agent))
