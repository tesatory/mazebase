import torch
from torch import nn
from torch.autograd import Variable
from torch import optim
from tqdm import tqdm
import os
import time
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
        for _i in tqdm(range(N)):
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
                print('loss ' + str(avg_loss/self.verbose) + ' at iteration ' + str(it))
                avg_loss = 0

def run_episode(game, policy_net, featurizer, iactions):
    for i in range(30):
        os.system('clear')
        g.display_ascii()
        time.sleep(.3)
        x = featurizer.featurize(game)
        #todo recursive conversion to Variable
        for i,j in enumerate(x):
            x[i] = Variable(j)
        p = policy_net(x)
        a = torch.multinomial(torch.exp(p[0].data.squeeze()),1)
        a = iactions[a[0]]
        g.act(a)
        g.update()
        if g.finished:
            os.system('clear')
            g.display_ascii()
            break
                
if __name__ == '__main__':
    import mazebase.goto as goto
    import mazebase.blocked_door as blocked_door
    import mazebase.multi_goals as multi_goals
    import mazebase.torch_featurizers as tfs
    import mazebase.models as models

    torch.set_default_tensor_type('torch.DoubleTensor')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--nonlin', default='relu', help='elu or relu')
    parser.add_argument('--optimizer', default='rmsprop', help='rmsprop, adagrad, or sgd')
    parser.add_argument('--batch-size', '-b', type=int, default=32, metavar='N',
                        help='batch size')
    parser.add_argument('--lrate', type=float, default=1e-2, metavar='G',
                        help='learning rate (default: 1e-2)')
    parser.add_argument('--num_data', default=100000, type=int, help='number of episodes')
    parser.add_argument('--num_iterations', default=1000000, type=int, help='number of batches to train on')
    parser.add_argument('--verbose', default=500, type=int, help='how often to print loss')
    parser.add_argument('--edim', default=64, type=int, help='size of embedding dim for model')

    args = parser.parse_args()
    args.naction_heads = [9]
    print(args)
        
    F = goto.Factory('goto',
                {'static': {'map_width': 10, 'map_height': 10, 'step_cost': -.1,
                            'nblocks': 5, 'nwater': 5, 'water_cost': -.2,
                            'fixed_goal': False}, 'featurizer': {}},
                goto.Game)

    F = F + blocked_door.Factory('blocked_door',
                                 {'static': {'map_width': 10, 'map_height': 10,
                                             'step_cost': -.1, 'nwater': 3,
                                             'water_cost': -.2, 'nblocks': 3},
                                  'range': {'ncolors': [3,3,3,3,0],
                                            'nswitches': [1,1,1,1,0]},
                                  
                                 'featurizer': {}},
                                 blocked_door.Game)

    F = F + multi_goals.Factory('multi_goals',
                                 {'static': {'map_width': 10, 'map_height': 10,
                                             'step_cost': -.1, 'nwater': 3,
                                             'water_cost': -.2, 'nblocks': 3,
                                             'flag_visited': 1},
                                  'range': {'ncolors': [3,3,3,3,0],
                                            'nswitches': [1,1,1,1,0],
                                            'ngoals': [5,5,5,5,0],
                                            'ngoals_active': [3,3,3,3,0]}, 
                                 'featurizer': {}},
                                 multi_goals.Game)

    
    feat = tfs.SparseSentenceFeaturizer({'egocentric_coordinates':True,
                                   'separate_loc':False,
                                   'visible_range':8}, F.dictionary)
    def bfi(state):
        return tfs.SparseSentenceBatchifier(state, numpy = False)
    print('building ' + str(args.num_data) + ' trajectories')
    D = DataBuilder(F, feat, bfi, {})
    D.build(args.num_data)
    nwords = len(feat.dictionary['ivocab'])
    print('building model')
    policy_net = models.Commnet(args, nwords, 3, value_or_policy = 'policy')
    if args.optimizer == 'sgd':
        optimizer = optim.SGD(torch.nn.ModuleList([policy_net]).parameters(),lr = args.lrate)
    elif args.optimizer == 'adagrad':
        optimizer = optim.Adagrad(torch.nn.ModuleList([policy_net]).parameters(), lr = args.lrate)
    else:
        optimizer = optim.RMSprop(torch.nn.ModuleList([policy_net]).parameters(), lr = args.lrate, alpha=0.97, eps=1e-6)
    print('training')
    trainer = FixedDataTrainer(D, policy_net, optimizer, args)
    trainer.train(args.num_iterations)
