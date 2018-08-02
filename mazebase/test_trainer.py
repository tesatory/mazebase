from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import torch
import torch.multiprocessing

# the reason for this flag is because python seems to be mega-slow with the linux-default of
# file-descriptor based sharing in pytorch. The actual cause was tracked down python internals, where
# python.multiprocessing.resource_sharer.DupFd.detach() is unbearably slow
torch.multiprocessing.set_sharing_strategy('file_system')

from torch import optim

import argparse
from collections import namedtuple

import mazebase.game_factory as gf
import mazebase.trainer as trainer
import mazebase.env_wrapper as env_wrapper
#this needs to be renamed or moved
import mazebase.models as models
import mazebase.multi_threaded_trainer as tt
import mazebase.supervised_trainer as st
import mazebase.torch_featurizers as tfs
import mazebase.config_env as config_env

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
parser.add_argument('--batch-size', '-b', dest='batch_size', type=int, default=1500, metavar='N',
                    help='batch size')
parser.add_argument('--log-interval', type=int, default=1, metavar='N',
                    help='interval between training status logs (default: 10)')
parser.add_argument('--normalize_rewards', action='store_true', default=False,
                    help='render the environment')
parser.add_argument('--lrate', type=float, default=1e-3, metavar='G',
                    help='learning rate (default: 1e-3)')
parser.add_argument('--optimizer', type=str, help='adam, rmsprop, adagrad, or sgd')
parser.add_argument('--entr', type=float, default=0, metavar='G',
                    help='entropy regularization')
parser.add_argument('--nthreads', type=int, default=10,
                    help='How many threads to run envs in')
parser.add_argument('--config_path', default="config/test.py",
                    help='path to config file')
parser.add_argument('--gpu', default=False, action="store_true", help='use GPU')
parser.add_argument('--max_steps', default=50, type=int, help='force to end the game after this many steps')
parser.add_argument('--num_iterations', default=10000, type=int, help='number of episodes')
parser.add_argument('--plot', action='store_true', default=False,
                    help='plot training progress')
parser.add_argument('--plot-env', dest='plot_env', default='main', type=str, help='plot env name')
parser.add_argument('--plot-port', dest='plot_port', default=6666, type=int, help='plot env name')
parser.add_argument('--model-type', dest='model_type', type=str, help='fc, conv or commnet')

parser.set_defaults(
        optimizer='adam',
        batch_size=1500,
        model_type='conv'
)

args = parser.parse_args()

args.__NUMPY__ = False

print(args)

LogField = namedtuple('LogField', ('data', 'plot', 'x_axis'))
log = dict()
log['#batch'] = LogField(list(), False, '')
log['reward'] = LogField(list(), True, '#batch')

config = config_env.env_maker_all(args.config_path)
env, factory, featurizer = config[0], config[1], config[2]
args.naction_heads = env.num_actions

if args.model_type == 'fc':
    num_inputs = env.observation_dim
    policy_net = models.Policy(args, num_inputs)
    value_net = models.Value(num_inputs)
    batchifier = None
if args.model_type == 'conv':
    grid_feat = env.featurizer
    num_in_channels, W, H = grid_feat.C, grid_feat.W, grid_feat.H
    policy_net = models.ConvPolicy(args, num_in_channels, 36, W, H).cuda()
    value_net = models.Value(num_inputs)
elif args.model_type == 'commnet':
    batchifier = tfs.SparseSentenceBatchifier
    nwords = len(env.featurizer.dictionary['ivocab'])
    policy_net = models.Commnet(args, nwords, 1, value_or_policy = 'policy')
    value_net = models.Commnet(args, nwords, 1, value_or_policy = 'value')

if args.seed >= 0:
    torch.manual_seed(args.seed)

policy_net.share_memory()
value_net.share_memory()

if args.optimizer == 'rmsprop':
    optimizer = optim.RMSprop(torch.nn.ModuleList([policy_net, value_net]).parameters(),
            lr = args.lrate, alpha=0.97, eps=1e-6)
elif args.optimizer == 'adam':
    optimizer = optim.Adam(list(policy_net.parameters()), lr = args.lrate)
    #attr_optimizer = optim.Adam(list(attr_model.parameters()), lr = args.lrate)


if args.nthreads > 1:
    def build_eprunner():
        return trainer.EpisodeRunner(config_env.env_maker, policy_net, value_net, args)

    runner = tt.ThreadedEpisodeRunner(args, build_eprunner)
else:
    runner = trainer.EpisodeRunner(config_env.env_maker, policy_net, value_net, args)




playground = trainer.Trainer(runner, optimizer, args, batchifier = batchifier)
playground.run(args.num_iterations)

# demo
st.run_episode(factory.init_random_game(), policy_net, featurizer, factory.iactions)

