from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import torch
from torch import optim

import argparse
from collections import namedtuple

import visdom

import mazebase.game_factory as gf
import mazebase.trainer as trainer
import mazebase.env_wrapper as env_wrapper
#this needs to be renamed or moved
import mazebase.models as models
# don't really need torch here
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
parser.add_argument('--gamma', type=float, default=0.995, metavar='G',
                    help='discount factor (default: 0.995)')
parser.add_argument('--tau', type=float, default=0.97, metavar='G',
                    help='gae (default: 0.97)')
parser.add_argument('--seed', type=int, default=-1, metavar='N',
                    help='random seed (default: 1)')
parser.add_argument('--batch-size', '-b', type=int, default=1500, metavar='N',
                    help='random seed (default: 1)')
parser.add_argument('--render', action='store_true',
                    help='render the environment')
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
parser.add_argument('--max_steps', default=20, type=int, help='force to end the game after this many steps')
parser.add_argument('--num_iterations', default=10000, type=int, help='number of episodes')
parser.add_argument('--nactions', default='1', type=str, help='the number of agent actions (1 for contineous). Use N:M:K for multiple actions')
parser.add_argument('--action_scale', default=1.0, type=float, help='scale action output from model')
parser.add_argument('--plot', action='store_true', default=False,
                    help='plot training progress')
parser.add_argument('--plot_env', default='main', type=str, help='plot env name')

args = parser.parse_args()
print(args)

LogField = namedtuple('LogField', ('data', 'plot', 'x_axis'))
log = dict()
log['#batch'] = LogField(list(), False, '')
log['reward'] = LogField(list(), True, '#batch')

if args.plot:
    vis = visdom.Visdom(env=args.plot_env)


game_opts, games = load_config(args.config_path)
F = gf.GameFactory(None, None, None)
for g in games:
    F += games[g].Factory(g, game_opts[g], games[g].Game)
featurizer = GridFeaturizer(game_opts['featurizer'], F.dictionary)
env = env_wrapper.MazeBaseWrapper(F, featurizer, args)

num_inputs = env.observation_dim
args.num_actions = env.num_actions
args.dim_actions = env.dim_actions
args.naction_heads = [args.num_actions]

if args.seed >= 0:
    torch.manual_seed(args.seed)

policy_net = models.Policy(args, num_inputs)
value_net = models.Value(num_inputs)

policy_net.share_memory()
value_net.share_memory()

optimizer = optim.RMSprop(torch.nn.ModuleList([policy_net, value_net]).parameters(), 
    lr = args.lrate, alpha=0.97, eps=1e-6)

                
#if args.nthreads > 1:               
#    runner = ThreadedEpisodeRunner(args, lambda: EpisodeRunner(data.init(args.env_name, args)))
#else:
#    runner = EpisodeRunner(data.init(args.env_name, args))

runner = trainer.EpisodeRunner(env, policy_net, value_net, args)
trainer = trainer.Trainer(runner, optimizer, args)


trainer.run(args.num_iterations)
