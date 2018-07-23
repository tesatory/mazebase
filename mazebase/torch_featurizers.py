from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mazebase.featurizer import SentenceFeaturizer
import torch
#FIXME when numpy not needed for multithreading
import numpy as np


# this inputs tensors
# l0, l1, ... , lk and a0, a1, ... ak
# and builds a sum_i a_i tensor
# 0 0 .. 0 l0 l0 ... l0 l0+l1 ...
# where term i is repeated a_i times
def expand_offsets(l,a):
    s = a.sum()
    u = torch.LongTensor(s).zero_()
    acs = a.cumsum(0)
    u[acs[:-1]] = l[:-1]
    return u.cumsum(0)


# this inputs a tensor
# l0, l1, ... , lk
# and builds a sum_i l_i tensor
# 0 0 .. 0 1 1 ... 1 2 2...
# where term i is repeated l_i times
def expand_ids(l):
    s = l.sum()
    u = torch.LongTensor(s).zero_()
    lcs = l.cumsum(0)
    u[lcs[:-1]] = 1
    return u.cumsum(0)


#todo this should go somewhere else?
#assumes numpy batches for now, FIXME when
#training loop fixed
def SparseSentenceBatchifier(batched_state, numpy = True):
    #input is [[words_0, item_Starts_0], [words_1, item_starts_1],...]
    #output is [words, item_starts, idx_of_state_per_item, num_items_in_state]
    states = list(zip(*batched_state))
    words = states[0]
    starts = states[1]
    lw = torch.LongTensor([len(i) for i in words])
    ls = torch.LongTensor([len(i) for i in starts])
    offsets = expand_offsets(lw, ls)
    ids = expand_ids(ls)
    if not numpy:
        words = torch.cat(words, 0)
        starts = torch.cat(starts, 0)
    else:
        words = torch.from_numpy(np.concatenate(words, axis=0))
        starts = torch.from_numpy(np.concatenate(starts, axis=0))
    starts += offsets
    return [words, starts, ids, ls]


#to be fed into e.g. nn.EmbeddingBag
class SparseSentenceFeaturizer(SentenceFeaturizer):
    def __init__(self, opts, dictionary=None):
        super(SparseSentenceFeaturizer, self).__init__(opts,
                                                       dictionary=dictionary)

    def to_tensor(self, game, agent=None):
        X = self.to_sentence(game, agent=agent)
        N = len(X)
        item_starts = torch.LongTensor(N)
        x = torch.LongTensor(0)
        vocab = self.dictionary['vocab']
        count = 0
        starts = 0
        for item, loc in X:
            item_starts[count] = starts
            count += 1
            starts += len(item)
            lx = torch.LongTensor([vocab[j] for j in item] + [loc[0], loc[1]])
            x = torch.cat((x,lx))
        return [x, item_starts]

    def featurize(self, game):
        return self.to_tensor(game, game.agent)




# returns a tensor of size Height x Width x VocabSize
class GridFeaturizer(SentenceFeaturizer):
    def __init__(self, opts, dictionary = None):
        opts['separate_loc'] = True
        super(GridFeaturizer, self).__init__(opts, dictionary = dictionary)
        if self.opts.get('egocentric_coordinates'):
            self.W = self.opts['visible_range']*2-1
            self.H = self.opts['visible_range']*2-1
        else:
            # TODO: or we can get the size from factory
            self.W = self.opts['max_map_sizes'][0]
            self.H = self.opts['max_map_sizes'][1]
        self.C = len(self.dictionary['vocab'])

    def to_tensor(self, game, agent = None):
        vocab = self.dictionary['vocab']
        S = self.to_sentence(game, agent = agent)
        x = torch.zeros(self.W, self.H, self.C)
        for item, loc in S:
            for w in item:
                x[loc[0]][loc[1]][vocab[w]] += 1
        return x

    def featurize(self, game):
        return self.to_tensor(game, game.agent)


class ObjFeaturizer(SentenceFeaturizer):
    def __init__(self, opts, dictionary=None):
        opts['separate_loc'] = True
        super(ObjFeaturizer, self).__init__(opts, dictionary = dictionary)
        self.vocab = self.dictionary['vocab']
        self.attr_dim = len(self.vocab) + 3    # +3 for including loc attr and reachability

    def to_tensor(self, game, agent = None):
        #print('vocab: ', self.vocab)
        S = self.to_sentence(game, agent = agent)

        attrs = []
        # starts from 1 since game.items[0] is 'info'
        item_idx = 1
        for item, loc in S:
            attr_item = torch.zeros(self.attr_dim)
            #print(item, game.items[item_idx].attr['_type'])
            # attr_item: x, y coordinates; other attributes, reachability
            attr_item[0] = loc[0]
            attr_item[1] = loc[1]
            for w in item:
                attr_item[self.vocab[w] + 2] = 1
            if game.items[item_idx].is_reachable():
                attr_item[-1] = 1
            attrs.append(attr_item)
            item_idx += 1
        out = torch.stack(attrs)
        #print('num items: ', len(S))
        #print('len vocab: ', len(self.vocab))
        #print(out)
        return out

    def featurize(self, game):
        return self.to_tensor(game, game.agent)


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


    featurizer_opts = {'egocentric_coordinates':True,'visible_range':5}
    SF = SparseSentenceFeaturizer(featurizer_opts, F.dictionary)
    g = F.init_random_game()
    print(SF.to_tensor(g, g.agent))

    featurizer_opts = {'egocentric_coordinates':False}
    SFabs = SparseSentenceFeaturizer(featurizer_opts, F.dictionary)
    print(SFabs.to_tensor(g, g.agent))
