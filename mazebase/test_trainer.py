from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import torch
from torch import optim

import argparse
from collections import namedtuple

import mazebase.game_factory as gf
import mazebase.trainer as trainer
import mazebase.env_wrapper as env_wrapper
#this needs to be renamed or moved
import mazebase.models as models
import mazebase.multi_threaded_trainer as tt
from mazebase.torch_featurizers import GridFeaturizer

def load_config(config_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", config_path)
    config  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.game_opts()


#torch.utils.backcompat.broadcast_warning.enabled = True
#torch.utils.backcompat.keepdim_warning.enabled = True

torch.set_default_tensor_type('torch.DoubleTensor')

parser = argparse.ArgumentParser(description='PyTorch actor-critic example')
parser.add_argument('--gamma', type=float, default=1.0, metavar='G',
                    help='discount factor')
parser.add_argument('--tau', type=float, default=1.0, metavar='G',
                    help='gae')
parser.add_argument('--seed', type=int, default=-1, metavar='N',
                    help='random seed')
parser.add_argument('--batch-size', '-b', type=int, default=1500, metavar='N',
                    help='batch size')
parser.add_argument('--log-interval', type=int, default=1, metavar='N',
                    help='interval between training status logs (default: 10)')
parser.add_argument('--normalize_rewards', action='store_true', default=False,
                    help='render the environment')
parser.add_argument('--lrate', type=float, default=1e-2, metavar='G',
                    help='learning rate (default: 1e-2)')
parser.add_argument('--entr', type=float, default=0, metavar='G',
                    help='entropy regularization')
parser.add_argument('--nthreads', type=int, default=10,
                    help='How many threads to run envs in')                    
parser.add_argument('--config_path', default="config/test.py",
                    help='path to config file')
parser.add_argument('--gpu', default=False, action="store_true", help='use GPU')
parser.add_argument('--max_steps', default=20, type=int, help='force to end the game after this many steps')
parser.add_argument('--num_iterations', default=10000, type=int, help='number of episodes')
parser.add_argument('--plot', action='store_true', default=False,
                    help='plot training progress')
parser.add_argument('--plot_env', default='main', type=str, help='plot env name')

args = parser.parse_args()

args.__NUMPY__ = True

print(args)

LogField = namedtuple('LogField', ('data', 'plot', 'x_axis'))
log = dict()
log['#batch'] = LogField(list(), False, '')
log['reward'] = LogField(list(), True, '#batch')


def env_maker():
    game_opts, games = load_config(args.config_path)
    F = gf.GameFactory(None, None, None)
    for g in games:
        F += games[g].Factory(g, game_opts[g], games[g].Game)
    featurizer = GridFeaturizer(game_opts['featurizer'], F.dictionary)
    return env_wrapper.MazeBaseWrapper(F, featurizer, args)
env = env_maker()  # dummy

num_inputs = env.observation_dim
args.naction_heads = env.num_actions

if args.seed >= 0:
    torch.manual_seed(args.seed)

policy_net = models.Policy(args, num_inputs)
value_net = models.Value(num_inputs)

policy_net.share_memory()
value_net.share_memory()

optimizer = optim.RMSprop(torch.nn.ModuleList([policy_net, value_net]).parameters(), 
    lr = args.lrate, alpha=0.97, eps=1e-6)

                
if args.nthreads > 1:               
    def build_eprunner(): 
        return trainer.EpisodeRunner(env_maker, policy_net, value_net, args)

    runner = tt.ThreadedEpisodeRunner(args, build_eprunner)
else:
    runner = trainer.EpisodeRunner(env_maker, policy_net, value_net, args)

playground = trainer.Trainer(runner, optimizer, args)
playground.run(args.num_iterations)