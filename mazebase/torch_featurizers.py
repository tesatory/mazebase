from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mazebase.featurizer import SentenceFeaturizer
import torch

#to be fed into e.g. nn.EmbeddingBag
class SparseSentenceFeaturizer(SentenceFeaturizer):
    def __init__(self, opts, dictionary = None):
        super(SparseSentenceFeaturizer, self).__init__(opts, 
                                                       dictionary = dictionary)
        
    def to_tensor(self, game, agent = None):
        X = self.to_sentence(game, agent = agent)
        N = len(X)
        item_lengths = torch.LongTensor(N)
        x = torch.LongTensor(0)
        vocab = self.dictionary['vocab']
        count = 0
        for item in X:
            item_lengths[count] = len(item)
            count += 1
            lx = torch.LongTensor([vocab[j] for j in item])
            x = torch.cat((x,lx))
        return x, item_lengths

# returns a tensor of size Height x Width x VocabSize
class GridFeaturizer(SentenceFeaturizer):
    def __init__(self, opts, dictionary = None):
        opts['separate_loc'] = True
        super(GridFeaturizer, self).__init__(opts, dictionary = dictionary)
                                                       
    def to_tensor(self, game, agent = None):
        vocab = self.dictionary['vocab']
        S = self.to_sentence(game, agent = agent)
        if self.opts['egocentric_coordinates']:
            x = torch.zeros(self.opts['visible_range']*2-1, 
                            self.opts['visible_range']*2-1, len(vocab))
        else:
            # TODO: or we can get the size from factory
            x = torch.zeros(self.opts['max_map_sizes'][0], 
                            self.opts['max_map_sizes'][1], len(vocab))
        for item, loc in S:
            for w in item:
                x[loc[0]][loc[1]][vocab[w]] += 1
        return x
            

if __name__ == '__main__':
    import mazebase.goto as goto
    import mazebase.switches as switches

    game_opts = {}
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = (5, 10, 5, 10, 1)
    range_opts['map_height'] = (5, 10, 5, 10, 1)
    range_opts['nblocks'] = (1, 5, 1, 5, 1)
    range_opts['nwater'] = (1, 5, 1, 5, 1)
    go['range'] = range_opts

    game_opts['goto'] = go

    #####################################
    # switches:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = (5, 10, 5, 10, 1)
    range_opts['map_height'] = (5, 10, 5, 10, 1)
    range_opts['nblocks'] = (1, 5, 1, 5, 1)
    range_opts['nwater'] = (1, 5, 1, 5, 1)
    range_opts['nswitches'] = (3, 5, 3, 5, 1)
    range_opts['ncolors'] = (3, 3, 3, 3, 0)
    go['range'] = range_opts

    game_opts['switches'] = go

    ######################################
    F = goto.Factory('goto', game_opts['goto'], goto.Game)
    F += switches.Factory('switches', game_opts['switches'],
                          switches.Game)


    featurizer_opts = {'egocentric_coordinates':True,'visible_range':5}
    SF = SparseSentenceFeaturizer(featurizer_opts, F.dictionary)
    g = F.init_random_game()
    print(SF.to_tensor(g, g.agent))

    featurizer_opts = {'egocentric_coordinates':False}
    SFabs = SparseSentenceFeaturizer(featurizer_opts, F.dictionary)
    print(SFabs.to_tensor(g, g.agent))
