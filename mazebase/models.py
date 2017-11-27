import torch
import torch.autograd as autograd
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F


class Policy(nn.Module):
    def __init__(self, args, num_inputs):
        super(Policy, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 64)
        self.affine2 = nn.Linear(64, 64)
        self.heads = nn.ModuleList([nn.Linear(64, o) for o in args.naction_heads])

    def forward(self, x):
        x = F.tanh(self.affine1(x))
        x = F.tanh(self.affine2(x))
        return [F.log_softmax(head(x), 1) for head in self.heads]


class ActionValueModel(nn.Module):
    def __init__(self, args, num_inputs):
        super(ActionValueModel, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 64)
        self.affine2 = nn.Linear(64, 64)
        self.heads = nn.ModuleList([nn.Linear(64, o) for o in args.naction_heads])
        self.value_head = nn.Linear(64, 1)

    def forward(self, x):
        x = F.tanh(self.affine1(x))
        x = F.tanh(self.affine2(x))
        v = self.value_head(x)
        return v, [F.log_softmax(head(x)) for head in self.heads]


class Value(nn.Module):
    def __init__(self, num_inputs):
        super(Value, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 64)
        self.affine2 = nn.Linear(64, 64)
        self.value_head = nn.Linear(64, 1)

    def forward(self, x):
        x = F.tanh(self.affine1(x))
        x = F.tanh(self.affine2(x))
        state_values = self.value_head(x)
        return state_values
