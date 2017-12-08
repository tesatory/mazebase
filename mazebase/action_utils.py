import numpy as np
import torch
from torch.autograd import Variable


#TODO converters etc are passed
#TODO get rid of this whole file
def convert_state_to_variable(state, use_numpy):
    if type(state) == list:
        ns = []
        for i,j in enumerate(state):
            if use_numpy:
                ns.append(Variable(torch.from_numpy(j),volatile = True))
            else:
                ns.append(Variable(j, volatile = True))
        return ns
    else:
        if use_numpy:
            state = Variable(torch.from_numpy(state).unsqueeze(0), volatile = True)
        else:
            state = Variable(state.unsqueeze(0), volatile = True )
        return state

def select_action(args, policy_net, state):
    state = convert_state_to_variable(state, args.__NUMPY__)
    log_p_a = policy_net(state)
    p_a = [x.exp() for x in log_p_a]
    return [torch.multinomial(p, 1).detach() for p in p_a]

def translate_action(args, env, action):
    # environment takes discrete action
    action = [x.squeeze().data[0] for x in action]
    actual = action
    return action, actual
    
