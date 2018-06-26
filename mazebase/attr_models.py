import torch
import torch.autograd as autograd
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F

class AttrNet(nn.Module):
    def __init__(self, attr_dim, n_objs):
    '''
    Args:
        attr_dim: number of attributes for each object
        n_objs: number of objects (fixed for now)
    '''
        self.attr_dim = attr_dim
        self.act = nn.ReLU()
        self.mlps = []

        flattened_pred_input_dim = attr_dim * (n_objs - 1)
        for i in range(n_objs):
            self.mlp = self.build_mlp_layers(flattened_pred_input_dim, 64, attr_dim)
            self.mlps.append(self.mlp)

        for m in self.modules():
            if isinstance(m, nn.Linear):
                m.weight.data = init.xavier_uniform(m.weight.data, gain=nn.init.calculate_gain('relu'))
                if m.bias is not None:
                    m.bias.data = init.constant(m.bias.data, 0.0)

    def build_mlp_layers(self, pred_input_dim, pred_hidden_dims, label_dim):

        if len(pred_hidden_dims) == 0:
            pred_model = nn.Linear(pred_input_dim, label_dim)
        else:
            pred_layers = []
            for pred_dim in pred_hidden_dims:
                pred_layers.append(nn.Linear(pred_input_dim, pred_dim))
                pred_layers.append(self.act)
                pred_input_dim = pred_dim
            pred_layers.append(nn.Linear(pred_dim, label_dim))
            pred_model = nn.Sequential(*pred_layers)
        return pred_model


    def forward(self, x, target_obj):
    ''' predict target attributes given all other attributes in x
    Args:
        x: input tensor whose each column is the attributes for an object
    '''
        x = x.view(-1)
        model = self.mlps[target_obj]
        out = model(x)
        return out

    def loss(self, y_pred, y):
        return nn.MSELoss()(y_pred, y)

