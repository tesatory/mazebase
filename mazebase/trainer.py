import torch
from torch.autograd import Variable

from collections import namedtuple
from itertools import count
import random

import visdom
import numpy as np
import action_utils
#from multi_threading import *

from utils import Timer
import copy


Transition = namedtuple('Transition', ('state', 'action', 'mask', 'next_state',
                                       'reward'))
                                       
def multinomials_log_density(actions, log_probs):
    log_prob = 0
    for i in range(len(log_probs)):
        log_prob += log_probs[i].gather(1, actions[:, i].long().unsqueeze(1))
    return log_prob


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

class EpisodeRunner(object):
    def __init__(self, env_maker, policy_net, value_net, args):
        self.env = env_maker()
        self.display = False
        self.policy_net = policy_net
        #fixme
        self.value_net = value_net
        self.args = args

    def quit(self):
        pass
    
    def reset(self):
        pass
    
    def get_episode(self):
        env = self.env
        policy_net = self.policy_net
        args = self.args
        episode = []
        state = self.env.reset()
        if self.display:
            env.display()
        for t in range(args.max_steps):
            action = action_utils.select_action(args, policy_net, state)
            action, actual = action_utils.translate_action(args, env, action)
            next_state, reward, done = env.step(actual)
            if self.display:
                env.display()
            mask = 1
            done = done or t == args.max_steps - 1
            if done:
                mask = 0
            if args.__NUMPY__:
                episode.append([state, np.array([action]), mask, next_state, reward])
            else:
                episode.append([state, action, mask, next_state, reward])
            state = next_state
            if done:
                break
        return episode
    

class Trainer:
    def __init__(self, runner, optimizer, args, batchifier = None):
        self.i_iter = 0
        self.num_total_steps = 0
        self.args = args
        self.runner = runner
        self.optimizer = optimizer
        self.batchifier = None
        LogField = namedtuple('LogField', ('data', 'plot', 'x_axis'))
        log = dict()
        log['#batch'] = LogField(list(), False, '')
        log['reward'] = LogField(list(), True, '#batch')
        self.log = log
        if args.plot:
            self.vis = visdom.Visdom(env=args.plot_env)

    def run(self, num_iteration):
        args = self.args
        runner = self.runner
        log = self.log
        batchifier = self.batchifier
        if self.args.gpu:
            gpu_policy = copy.deepcopy(runner.policy_net)
            gpu_value = copy.deepcopy(runner.value_net)
            gpu_policy.cuda()
            gpu_value.cuda()
            self.optimizer.param_groups = [{'params': torch.nn.ModuleList([gpu_policy, gpu_value]).parameters()}]
        for iter_ind in range(num_iteration):
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
                self.num_total_steps += (t+1)
                num_episodes += 1
                reward_batch += sum(x[4] for x in episode)
                num_batch += 1
                for tup in episode:
                    memory.push(*tup)

            reward_batch /= num_batch
            batch = memory.sample()
            #fixme value net
            if self.args.gpu:
                gpu_policy.load_state_dict(runner.policy_net.state_dict())
                gpu_value.load_state_dict(runner.value_net.state_dict())
                update_params(batch, batchifier, gpu_policy, gpu_value, self.optimizer, args)
                runner.policy_net.load_state_dict(gpu_policy.state_dict())
                runner.value_net.load_state_dict(gpu_value.state_dict())
            else:
                update_params(batch, batchifier, runner.policy_net, 
                              runner.value_net, self.optimizer, args)
            runner.reset()

            if self.i_iter % args.log_interval == 0:
                np.set_printoptions(precision=4)
                print('Iteration {}\tSteps {}\tAverage reward {:10.4f}'.format(
                    self.i_iter, self.num_total_steps, reward_batch
                ))
                log['#batch'].data.append(self.i_iter)
                log['reward'].data.append(reward_batch)
                if args.plot:
                    
                    for k, v in log.items():
                        if v.plot:
                            self.vis.line(np.asarray(v.data), np.asarray(log[v.x_axis].data),
                            win=k, opts=dict(xlabel=v.x_axis, ylabel=k))
            
            self.i_iter += 1
        
def update_params(batch, batchifier, policy_net, value_net, optimizer, args):
    # print("Updating params..")
    rewards = torch.Tensor(batch.reward)
    masks = torch.Tensor(batch.mask)
    if args.__NUMPY__:
        actions = torch.from_numpy(np.concatenate(batch.action, 0))
    else:
        actions = torch.Tensor(batch.action)
    if batchifier is None:
        if args.__NUMPY__:
            states = torch.from_numpy(np.stack(batch.state, axis = 0))
        else:
            states = torch.stack(batch.state, 0)
    else:
        states = batchifier(batch)
    if args.gpu:
        states = states.cuda()
        actions = actions.cuda()
    states = Variable(states, requires_grad=False)
    values = value_net(states)

    returns = torch.Tensor(actions.size(0),1)
    deltas = torch.Tensor(actions.size(0),1)
    advantages = torch.Tensor(actions.size(0),1)

    prev_return = 0
    prev_value = 0
    prev_advantage = 0
    for i in reversed(range(rewards.size(0))):
        returns[i] = rewards[i] + args.gamma * prev_return * masks[i]
        deltas[i] = rewards[i] + args.gamma * prev_value * masks[i] - values.data[i]
        advantages[i] = deltas[i] + args.gamma * args.tau * prev_advantage * masks[i]

        prev_return = returns[i, 0]
        prev_value = values.data[i]
        prev_advantage = advantages[i, 0]

    targets = Variable(returns).squeeze()
    if args.gpu:
        advantages = advantages.cuda()
        targets = targets.cuda()

    if args.normalize_rewards:
        advantages = (advantages - advantages.mean()) / advantages.std()
    
    optimizer.zero_grad()
    log_p_a = policy_net(states)
    log_prob = multinomials_log_density(Variable(actions, requires_grad=False), log_p_a)
    action_loss = -Variable(advantages, requires_grad=False) * log_prob
    action_loss = action_loss.mean()

    values_ = value_net(states).squeeze()
    value_loss = (values_ - targets).pow(2).mean()
    
    loss = action_loss + 0.05 * value_loss
    
    # entropy regularization
    if args.entr > 0:
        entropy = 0
        for i in range(len(log_p_a)):
            entropy -= (log_p_a[i] * log_p_a[i].exp()).sum(1).mean()
        loss -= args.entr * entropy

    loss.backward()
    optimizer.step()

