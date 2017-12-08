import torch
from torch import optim
from torch.autograd import Variable

import numpy as np

import random
import argparse
from collections import namedtuple

import mazebase.game_factory as gf
import mazebase.trainer as trainer
import mazebase.env_wrapper as env_wrapper
#this needs to be renamed or moved
import mazebase.models as models
import mazebase.multi_threaded_trainer as tt
import mazebase.torch_featurizers as tfs
from mazebase.torch_featurizers import GridFeaturizer
from mazebase.torch_featurizers import SparseSentenceFeaturizer
from mazebase.trainer import EpisodeRunner

Transition = namedtuple('Transition', ('state', 'action', 'mask', 'next_state',
                                       'reward'))

class Memory(object):
    def __init__(self):
        self.memory = []

    def push(self, *args):
        """Saves a transition."""
        self.memory.append(Transition(*args))

    def sample(self):
        return Transition(*zip(*self.memory))

    def __len__(self):
        return len(self.memory)


def load_config(config_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", config_path)
    config  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.game_opts()


torch.set_default_tensor_type('torch.DoubleTensor')

parser = argparse.ArgumentParser(description='PyTorch actor-critic example')
parser.add_argument('--batch-size', '-b', type=int, default=1500, metavar='N',
                    help='batch size')
parser.add_argument('--config_path', default="config/test.py",
                    help='path to config file')
parser.add_argument('--max_steps', default=20, type=int, help='force to end the game after this many steps')
args = parser.parse_args()

args.__NUMPY__ = True

game_opts, games, feat_class = load_config(args.config_path)
F = gf.GameFactory(None, None, None)
for g in games:
    F += games[g].Factory(g, game_opts[g], games[g].Game)
featurizer = feat_class(game_opts['featurizer'], F.dictionary)


def env_maker():
    game_opts, games, feat_class = load_config(args.config_path)
    F = gf.GameFactory(None, None, None)
    for g in games:
        F += games[g].Factory(g, game_opts[g], games[g].Game)
    featurizer = feat_class(game_opts['featurizer'], F.dictionary)
    return env_wrapper.MazeBaseWrapper(F, featurizer, args)


nwords = len(featurizer.dictionary['ivocab'])
args.naction_heads = [5]
policy_net = models.Commnet(args, nwords, 3, value_or_policy = 'policy')
value_net = models.Commnet(args, nwords, 3, value_or_policy = 'value')

#featurizer = GridFeaturizer(game_opts['featurizer'], F.dictionary)
        
runner = EpisodeRunner(env_maker, policy_net, value_net, args)

memory = Memory()
num_steps = 0
reward_batch = 0
num_batch = 0
num_episodes = 0
while num_steps < args.batch_size:
    if num_steps == 0:
        # discard episodes in buffer since model has changed
        runner.reset()
    episode = runner.get_episode()
    t = len(episode)
    num_steps += (t+1)
    num_episodes += 1
    reward_batch += sum(x[4] for x in episode)
    num_batch += 1
    for tup in episode:
        memory.push(*tup)

reward_batch /= num_batch
batch = memory.sample()

obs = tfs.SparseSentenceBatchifier(batch.state)
for i,j in enumerate(obs):
    obs[i] = Variable(j)
o1 = policy_net(obs)

m = 99
x = [Variable(torch.from_numpy(batch.state[m][0])), 
     Variable(torch.from_numpy(batch.state[m][1]))] 
o2 = policy_net(x)
