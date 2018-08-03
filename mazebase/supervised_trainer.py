import numpy as np
import os
import random
import sklearn.metrics as metrics
import time
import torch
from torch import nn
from torch.autograd import Variable
from torch import optim
#import visdom

import mazebase.config_env as config_env
import mazebase.episode_loader as loader

# collect rewards?
# deprecated
# use episode_loader.DataBuilder instead (use pytorch Dataset and DataLoader)
class DataBuilder(object):
    def __init__(self, factory, featurizer, batchifier, args):
        self.args = args
        self.featurizer = featurizer
        self.factory = factory
        self.batchifier = batchifier
        self.batchsize = args.batch_size or 32
        self.data = []

    def build(self, N):
        data = []
        for _i in tqdm(range(N)):
            g = self.factory.init_random_game()
            S = g.get_supervision(self.featurizer)
            for s in S:
                data.append(s)
        self.data = data
        train_ratio = 0.9
        val_start = int(len(self.data) * train_ratio)
        self.training_data = self.data[:val_start]
        self.val_data = self.data[val_start:]

    def sample(self, training=True):
        if training:
            data = self.training_data
        else:
            data = self.val_data
        L = len(data)
        if L == 0:
            raise Exception('data is empty. first self.build(N)')
        x = []
        for _s in range(self.batchsize):
            i = random.randint(0,L-1)
            x.append(data[i])
        b = list(zip(*x))
        if self.batchifier is not None:
            states = self.batchifier(b[0])
        else:
            states = b[0]
        # to pytorch tensor
        states = torch.stack(states, dim=0)

        return states, torch.LongTensor([self.factory.actions[a] for a in b[1]])


class FixedDataTrainer(object):
    def __init__(self, data, policy_net, optimizer, args):
        '''
        Args:
            data: episode_loader.DataBuilder object
        '''
        self.i_iter = 0
        self.num_total_steps = 0
        self.data = data
        self.args = args
        self.optimizer = optimizer
        self.verbose = args.verbose
        self.policy_net = policy_net
        self.loss_fn = nn.NLLLoss()
        self.eval_every = args.eval_every

    def evaluate(self, name='Test', max_num_examples=None):
        if name == 'Test':
            data = self.data.test_dataset_loader
        else:
            data = self.data.train_dataset_loader
        self.policy_net.eval()
        labels = []
        preds = []
        for batch_idx, batch_data in enumerate(data):
            x = Variable(batch_data['state'].double(), requires_grad=False)
            labels.append(batch_data['action'].squeeze().long().numpy())
            ypred = self.policy_net(x)
            if type(ypred) == list:
                ypred = ypred[0]
            _, indices = torch.max(ypred, 1)
            preds.append(indices.data.numpy())

            if max_num_examples is not None:
                if (batch_idx+1)*args.batch_size > max_num_examples:
                    break

        labels = np.hstack(labels)
        preds = np.hstack(preds)

        result = {'prec': metrics.precision_score(labels, preds, average='macro'),
                  'recall': metrics.recall_score(labels, preds, average='macro'),
                  'F1': metrics.f1_score(labels, preds, average="micro")}
        print(result)
        return result

    def train(self, num_iteration):
        self.policy_net.train()
        avg_loss = 0
        it = 0
        while it < args.num_iterations:
            for batch_idx, batch_data in enumerate(self.data.train_dataset_loader):
                self.optimizer.zero_grad()
                #x, y = self.data.sample()
                #todo recursive conversion to Variable
                #for i,j in enumerate(x):
                #    x[i] = Variable(j)
                # state
                x = Variable(batch_data['state'].double(), requires_grad=False)
                # squeeze since the label should be 1D for torch.nn.NLLLoss
                y = Variable(batch_data['action'].squeeze(), requires_grad=False)
                out = self.policy_net(x)
                if type(out) == list:
                    out = out[0]
                loss = self.loss_fn(out, y)
                loss.backward()
                self.optimizer.step()
                avg_loss += loss.data[0]
                if it % self.verbose == 0:
                    print('loss ' + str(avg_loss/self.verbose) + ' at iteration ' + str(it))
                    avg_loss = 0
                if it % self.eval_every == 0:
                    self.evaluate()
                it += 1

def run_episode(g, policy_net, featurizer, iactions):
    for i in range(30):
        os.system('clear')
        print('Current step: ', i)
        g.display_ascii()
        time.sleep(1.0)
        x = featurizer.featurize(g)
        #todo recursive conversion to Variable
        #for i,j in enumerate(x):
        #    x[i] = Variable(j)
        x = Variable(x.view(1, -1))
        p = policy_net(x)
        a = torch.multinomial(torch.exp(p[0].data.squeeze()),1)
        a = iactions[a[0]]
        print('Action: ', a)
        g.act(a)
        g.update()
        if g.finished:
            os.system('clear')
            g.display_ascii()
            break

def test_supervision(g, featurizer):
    print('Init: ')
    g.display_ascii()
    state_and_action_pairs = g.get_supervision(featurizer)
    print('Num steps: ', len(state_and_action_pairs))
    print('Final: ')
    g.display_ascii()
    print('Finished: ', g.finished)
    print('Goal at: ', g.items_bytype['goal'][0].attr['loc'])
    print('Agent at: ', g.agent.attr['loc'])
    print('Switches at: ', [s.attr['loc'] for s in g.items_bytype['cycle_switch']])

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
    parser.add_argument('--batch-size', '-b', dest='batch_size', type=int, default=32, metavar='N',
                        help='batch size')
    parser.add_argument('--lrate', type=float, default=1e-2, metavar='G',
                        help='learning rate (default: 1e-2)')
    parser.add_argument('--num-data', dest='num_data', default=100000, type=int, help='number of episodes')
    parser.add_argument('--iter', dest='num_iterations', default=100000, type=int, help='number of batches to train on')
    parser.add_argument('--verbose', default=500, type=int, help='how often to print loss')
    parser.add_argument('--edim', default=64, type=int, help='size of embedding dim for model')
    parser.add_argument('--model-type', dest='model_type', default='fc', type=str, help='fc or commnet')
    parser.add_argument('--config-path', dest='config_path', default="config/test.py",
                        help='path to config file')
    parser.add_argument('--num-workers', dest='num_workers', type=int,
                        help='Number of workers to load data.')
    parser.add_argument('--plot', action='store_true', default=False,
                        help='plot training progress')
    parser.add_argument('--plot-env', dest='plot_env', type=str, help='plot env name')
    parser.add_argument('--eval-every', dest='eval_every', type=int, help='run evaluation after every X iterations')
    parser.add_argument('--test-sup', dest='test_sup', action='store_true', default=False,
                        help='test game\'s supervision')

    parser.set_defaults(
            num_workers=1,
            plot_env='main',
            eval_every=1000
    )

    args = parser.parse_args()
    args.naction_heads = [9]


    #F = goto.Factory('goto',
    #            {'game_opts': {'map_width': 10, 'map_height': 10, 'step_cost': -.1,
    #                        'nblocks': 5, 'nwater': 5, 'water_cost': -.2,
    #                        'fixed_goal': False}, 'featurizer': {}},
    #            goto.Game)

    #F = F + blocked_door.Factory('blocked_door',
    #                             {'static': {'map_width': 10, 'map_height': 10,
    #                                         'step_cost': -.1, 'nwater': 3,
    #                                         'water_cost': -.2, 'nblocks': 3},
    #                              'range': {'ncolors': [3,3,3,3,0],
    #                                        'nswitches': [1,1,1,1,0]},

    #                             'featurizer': {}},
    #                             blocked_door.Game)

    #F = F + multi_goals.Factory('multi_goals',
    #                             {'static': {'map_width': 10, 'map_height': 10,
    #                                         'step_cost': -.1, 'nwater': 3,
    #                                         'water_cost': -.2, 'nblocks': 3,
    #                                         'flag_visited': 1},
    #                              'range': {'ncolors': [3,3,3,3,0],
    #                                        'nswitches': [1,1,1,1,0],
    #                                        'ngoals': [5,5,5,5,0],
    #                                        'ngoals_active': [3,3,3,3,0]},
    #                             'featurizer': {}},
    #                             multi_goals.Game)


    #feat = tfs.SparseSentenceFeaturizer({'egocentric_coordinates':True,
    #                               'separate_loc':False,
    #                               'visible_range':8}, F.dictionary)
    def bfi(state):
        # only used for SparseSentenceFeaturizer
        return tfs.SparseSentenceBatchifier(state, numpy = False)

    # Data from similating trajectories
    print('building ' + str(args.num_data) + ' trajectories')
    env_wrapper, factory, featurizer = config_env.env_maker_all(args.config_path)
    args.naction_heads = env_wrapper.num_actions

    if args.test_sup:
        test_supervision(factory.init_random_game(), featurizer)
        exit()

    D = loader.DataBuilder(args.num_data, factory, featurizer, None, args)
    print('Training size: ', len(D.train_dataset_loader))
    print('Test size: ', len(D.test_dataset_loader))

    nwords = len(featurizer.dictionary['ivocab'])
    print('building model')
    if args.model_type == 'fc':
        num_inputs = env_wrapper.observation_dim
        policy_net = models.Policy(args, num_inputs)
        value_net = models.Value(num_inputs)
    elif args.model_type == 'memnet':
        policy_net = models.Memnet(args, nwords, 3, value_or_policy = 'policy')
    elif args.model_type == 'commnet':
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
