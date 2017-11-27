import numpy as np
import torch
from torch.autograd import Variable

def parse_action_args(args):
    # environment takes discrete action
    assert args.dim_actions == 1
    args.naction_heads = [args.num_actions]

def select_action(args, policy_net, state):
    state = torch.from_numpy(state).unsqueeze(0)
    state = Variable(state, volatile=True)
    log_p_a = policy_net(state)
    p_a = [x.exp() for x in log_p_a]
    return [torch.multinomial(p, 1).detach() for p in p_a]

def translate_action(args, env, action):
    # environment takes discrete action
    action = [x.squeeze().data[0] for x in action]
    actual = action
    return action, actual
    
