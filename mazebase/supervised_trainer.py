import torch
from torch import nn
from torch.autograd import Variable
from torch import optim

import random

#import visdom
#import numpy as np

# collect rewards?
# build as torch dataset?
class DataBuilder(object):
    def __init__(self, factory, featurizer, batchifier, args):
        self.args = args
        self.featurizer = featurizer
        self.factory = factory
        self.batchifier = batchifier
        self.batchsize = args.get('batchsize') or 32
        self.data = []

    def build(self, N):
        data = []
        for _i in range(N):
            g = self.factory.init_random_game()
            S = g.get_supervision(self.featurizer)
            for s in S:
                data.append(s)
        self.data = data

    def sample(self):
        L = len(self.data)
        if L == 0:
            raise Exception('data is empty. first self.build(N)')
        x = []
        for _s in range(self.batchsize):
            i = random.randint(0,L-1)
            x.append(self.data[i])
        b = list(zip(*x))
#        import pdb
#        pdb.set_trace()
        if self.batchifier is not None:
            states = self.batchifier(b[0])
        else:
            states = b[0]
        return states, torch.LongTensor([self.factory.actions[a] for a in b[1]])

class FixedDataTrainer(object):
    def __init__(self, data, policy_net, optimizer, args):
        self.i_iter = 0
        self.num_total_steps = 0
        self.data = data
        self.args = args
        self.optimizer = optimizer
        self.verbose = args.verbose
        self.policy_net = policy_net

    def train(self, num_iteration):
        lf = nn.NLLLoss()
        avg_loss = 0
        for it in range(num_iteration):
            self.optimizer.zero_grad()
            x, y = self.data.sample()
            #todo recursive conversion to Variable
            for i,j in enumerate(x):
                x[i] = Variable(j)
            y = Variable(y)
            out = self.policy_net(x)
            if type(out) == list:
                out = out[0]
            loss = lf(out, y)
            loss.backward()
            self.optimizer.step()
            avg_loss += loss.data[0]
            if it % self.verbose == 0:
                print(avg_loss/self.verbose)
                avg_loss = 0

if __name__ == '__main__':
    torch.set_default_tensor_type('torch.DoubleTensor')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', '-b', type=int, default=32, metavar='N',
                        help='batch size')
    parser.add_argument('--lrate', type=float, default=1e-2, metavar='G',
                        help='learning rate (default: 1e-2)')
    parser.add_argument('--num_data', default=100000, type=int, help='number of episodes')
    parser.add_argument('--num_iterations', default=1000000, type=int, help='number of batches to train on')
    parser.add_argument('--verbose', default=500, type=int, help='how often to print loss')

    args = parser.parse_args()
    args.naction_heads = [5]
    import mazebase.goto as goto
    import mazebase.torch_featurizers as tfs
    import mazebase.models as models

    F = goto.Factory('goto',
                {'static': {'map_width': 10, 'map_height': 10, 'step_cost': -.1,
                            'nblocks': 5, 'nwater': 5, 'water_cost': -.2,
                            'fixed_goal': False}, 'featurizer': {}},
                goto.Game)
    feat = tfs.SparseSentenceFeaturizer({'egocentric_coordinates':True,
                                   'separate_loc':False,
                                   'visible_range':8}, F.dictionary)
    def bfi(state):
        return tfs.SparseSentenceBatchifier(state, numpy = False)
    D = DataBuilder(F, feat, bfi, {})
    D.build(args.num_data)
    nwords = len(feat.dictionary['ivocab'])
    policy_net = models.Commnet(args, nwords, 3, value_or_policy = 'policy')
#    optimizer = optim.SGD(torch.nn.ModuleList([policy_net]).parameters(),lr = args.lrate)
    optimizer = optim.RMSprop(torch.nn.ModuleList([policy_net]).parameters(), lr = args.lrate, alpha=0.97, eps=1e-6)
    trainer = FixedDataTrainer(D, policy_net, optimizer, args)
    trainer.train(args.num_iterations)
