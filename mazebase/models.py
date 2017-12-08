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
        return [F.log_softmax(head(x)) for head in self.heads]


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



class Commnet(nn.Module):
    def __init__(self, args, nwords, nlayers, value_or_policy = 'policy'):
        super(Commnet, self).__init__()
        self.embedding = nn.EmbeddingBag(nwords, 64)
        self.affines = []
        self.nlayers = nlayers
        self.value_or_policy = value_or_policy
        for i in range(nlayers):
            self.affines.append(nn.Linear(2*64,64))
        if value_or_policy == 'policy':
            self.heads = nn.ModuleList([nn.Linear(64, o) for o in args.naction_heads])
        else:
            self.heads = nn.Linear(64,1)
    def forward(self, inp):
        x = inp[0]
        item_starts = inp[1]
        emb = self.embedding(x,item_starts)
        if len(inp) == 2: #nonbatched
            batch_idx = Variable(torch.LongTensor(item_starts.size(0)).zero_())
            batch_len = Variable(torch.Tensor([item_starts.size(0)]))
        else:
            batch_idx = inp[2]
            batch_len = inp[3].double()
        for i in range(self.nlayers):
            m = Variable(torch.zeros(batch_len.size(0),64))
            m.index_add_(0, batch_idx, emb)
            if i ==  self.nlayers - 1:
                emb = m
            else: 
                M = m[batch_idx] - emb
                M /= (batch_len[batch_idx].unsqueeze(1).expand_as(M) - .99999)
                emb = torch.cat([emb, M],1)
                emb = F.relu(self.affines[i](emb))

        if self.value_or_policy == 'policy':
            return [F.log_softmax(head(emb)) for head in self.heads]
        else:
            return self.heads(emb)
