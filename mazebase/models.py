import torch
import torch.autograd as autograd
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F

def build_nonlin(nonlin):
    if nonlin == 'elu':
        return  nn.ELU(inplace = True)
    elif nonlin == 'tanh':
        return nn.Tanh()
#    elif nonlin == 'celu':
#        return celu()
    else:
        return nn.ReLU(inplace = True)

class Policy(nn.Module):
    def __init__(self, args, num_inputs, act=nn.ReLU):
        super(Policy, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 256)
        self.affine2 = nn.Linear(256, 128)
        self.heads = nn.ModuleList([nn.Linear(128, o) for o in args.naction_heads])
        self.act = act()

    def forward(self, x):
        '''
        Args:
            x: [batch_size x feature]
        '''
        batch_size = x.size()[0]
        x = x.view(batch_size, -1)
        x = self.act(self.affine1(x))
        x = self.affine2(x)
        return [F.log_softmax(head(x), dim=-1) for head in self.heads]

class Conv(nn.Module):
    def __init__(self, num_input_channels, num_output_channels, hiddens=[], act=nn.ReLU, kernel_size=3):
        super(Conv, self).__init__()
        self.act = act()
        padding = (kernel_size - 1) / 2
        if len(hiddens) == 0:
            self.conv = nn.Conv2d(num_input_channels, num_output_channels, kernel_size, stride=1, padding=padding)
        else:
            conv_layers = []
            in_dim = num_input_channels
            for hdim in hiddens:
                self.clayer = nn.Conv2d(in_dim, hdim, kernel_size, stride=1, padding=padding)
                conv_layers.append(self.clayer)
                conv_layers.append(self.act)
                in_dim = hdim
            self.clayer = nn.Conv2d(hdim, num_output_channels, kernel_size, stride=1, padding=padding)
            conv_layers.append(self.clayer)
            #conv_layers.append(self.act)
            self.conv = nn.Sequential(*conv_layers)

    def forward(self, x):
        x = torch.transpose(x, 1, 3)
        x = torch.transpose(x, 2, 3)
        x = self.conv(x)
        return x


class ConvPolicy(Policy):
    def __init__(self, args, num_input_channels, num_output_channels, W, H, act=nn.ReLU):
        super(ConvPolicy, self).__init__(args, num_output_channels * W * H)
        self.conv = Conv(num_input_channels, num_output_channels, [24])
        self.act = act()

    def forward(self, x):
        batch_size = x.size()[0]
        x = self.conv(x)
        x = x.view(batch_size, -1)
        x = self.act(self.affine1(x))
        x = self.affine2(x)
        return [F.log_softmax(head(x), dim=-1) for head in self.heads]

class ActionValueModel(nn.Module):
    def __init__(self, args, num_inputs, act=nn.ReLU):
        super(ActionValueModel, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 256)
        self.affine2 = nn.Linear(128, 128)
        self.heads = nn.ModuleList([nn.Linear(128, o) for o in args.naction_heads])
        self.value_head = nn.Linear(128, 1)

        self.act = act()

    def forward(self, x):
        batch_size = x.size()[0]
        x = x.view(batch_size, -1)
        x = self.act(self.affine1(x))
        x = self.act(self.affine2(x))
        v = self.value_head(x)
        return v, [F.log_softmax(head(x), dim=-1) for head in self.heads]


class Value(nn.Module):
    def __init__(self, num_inputs):
        super(Value, self).__init__()
        self.affine1 = nn.Linear(num_inputs, 256)
        self.affine2 = nn.Linear(256, 128)
        self.value_head = nn.Linear(128, 1)

    def forward(self, x):
        batch_size = x.size()[0]
        x = x.view(batch_size, -1)
        x = F.tanh(self.affine1(x))
        x = F.tanh(self.affine2(x))
        state_values = self.value_head(x)
        return state_values

###############################################################################
#commnet
###############################################################################
#todo: skip connections
class Commnet(nn.Module):
    def __init__(self, args, nwords, nlayers, value_or_policy = 'policy'):
        super(Commnet, self).__init__()
        self.edim = args.edim
        self.embedding = nn.EmbeddingBag(nwords, self.edim)
        self.affines = []
        self.nlayers = nlayers
        self.value_or_policy = value_or_policy
        self.nonlin = build_nonlin(args.nonlin)
        for i in range(nlayers):
            self.affines.append(nn.Linear(2*self.edim,self.edim))
        if value_or_policy == 'policy':
            self.heads = nn.ModuleList([nn.Linear(self.edim, o) for o in args.naction_heads])
        else:
            self.heads = nn.Linear(self.edim, 1)
    def forward(self, inp):
        x = inp[0]
        item_starts = inp[1]
        emb = self.embedding(x, item_starts)
        if len(inp) == 2: #nonbatched
            batch_idx = Variable(torch.LongTensor(item_starts.size(0)).zero_())
            batch_len = Variable(torch.Tensor([item_starts.size(0)]))
        else:
            batch_idx = inp[2]
            batch_len = inp[3].double()
        for i in range(self.nlayers):
            m = Variable(torch.zeros(batch_len.size(0), self.edim))
            m.index_add_(0, batch_idx, emb)
            if i == self.nlayers - 1:
                emb = m
            else:
                M = m[batch_idx] - emb
                M /= (batch_len[batch_idx].unsqueeze(1).expand_as(M) - .99999)
                cemb = torch.cat([emb, M], 1)
                emb = self.nonlin(self.affines[i](cemb))

        if self.value_or_policy == 'policy':
            return [F.log_softmax(head(emb)) for head in self.heads]
        else:
            return self.heads(emb)

###############################################################################
#memnet
###############################################################################

def batched_attention(q, input_embedding, output_embedding, batch_idx, batch_len):
    # N is total number of items, grouped in B batches
    # q is Bxd
    # input_embedding and output_embedding is Nxd
    # batch_id idx is N, indexes into q
    B = q.size(0)
    d = q.size(1)
    N = input_embedding.size(0)
    Q = q[batch_idx]
    p = (Q*input_embedding).sum(1)
    #FIXME .  do softmax not stupid.
    #this part for a little stability:
    u = p.data.new().resize_(B).zero_()
    pp = p.data.clone()
    pp[pp<0] = 0
    u.index_add_(0, batch_idx.data, pp)
    u /= batch_len.data
    p -= Variable(u[batch_idx.data])
    # and now back to bad softmax computation:
    p = torch.exp(p)
    partition = Variable(p.data.new().resize_(B).zero_())
    partition.index_add_(0, batch_idx, p)
    p /= partition[batch_idx]
    weighted_oe = output_embedding*p.unsqueeze(1).expand_as(output_embedding)
    output = Variable(q.data.new().resize_(q.size()).zero_())
    output.index_add(0, batch_idx, weighted_oe)
    return output

class Memnet(nn.Module):
    def __init__(self, args, nwords, nhops, value_or_policy = 'policy'):
        super(Memnet, self).__init__()
        self.edim = args.edim
        self.embeddingQ = nn.EmbeddingBag(nwords, self.edim)
        Q = self.embeddingQ.weight.data
        Q.div_(Q.norm(2,1).unsqueeze(1).expand_as(Q))
        self.embeddingA = nn.EmbeddingBag(nwords, self.edim)
        A = self.embeddingA.weight.data
        A.div_(A.norm(2,1).unsqueeze(1).expand_as(A))
        self.embeddingC = nn.EmbeddingBag(nwords, self.edim)
        C = self.embeddingC.weight.data
        C.div_(C.norm(2,1).unsqueeze(1).expand_as(C))
        self.affine = nn.Linear(self.edim,self.edim)
        self.nhops = nhops
        self.value_or_policy = value_or_policy
        self.nonlin = build_nonlin(args.nonlin)

        if value_or_policy == 'policy':
            self.heads = nn.ModuleList([nn.Linear(self.edim, o) for o in args.naction_heads])
        else:
            self.heads = nn.Linear(self.edim, 1)
    def forward(self, inp):
        x = inp[0]
        item_starts = inp[1]
#        embQ = self.embeddingQ(x, item_starts)
        embA = self.embeddingA(x, item_starts)
        embC = self.embeddingC(x, item_starts)
        if len(inp) == 2: #nonbatched
            batch_idx = Variable(torch.LongTensor(item_starts.size(0)).zero_())
            batch_len = Variable(torch.Tensor([item_starts.size(0)]))
        else:
            batch_idx = inp[2]
            batch_len = inp[3].double()
        B = batch_len.size(0)
        u = Variable(embC.data.new().resize_(B, self.edim).zero_())
#        u = Variable(embQ.data.new().resize_(B, self.edim).zero_())
#        u.index_add_(0, batch_idx, embQ)
        u.index_add_(0, batch_idx, embC)

        for i in range(self.nhops):
            o = batched_attention(u, embA, embC, batch_idx, batch_len)
            u = self.nonlin(u + o)
#            u = self.nonlin(self.affine(u) + o)


        if self.value_or_policy == 'policy':
            return [F.log_softmax(head(u)) for head in self.heads]
        else:
            return self.heads(u)
