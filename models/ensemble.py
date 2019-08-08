# implement filter-based image captioning
import torch
import torch.nn as nn
from models import resnet, transformer

import pdb

class Ensemble(nn.Module):
    def __init__(self, filter_vocab_size, tgt_vocab_size, pad_label=1):
        super(Ensemble, self).__init__()
        # output pooled feats directly without projection
        self.resnet = resnet.ResNet('resnet18', num_classes=-1)
        self.transformer = transformer.Transformer(filter_vocab_size, tgt_vocab_size, pad_label=pad_label)
        self.pad_label = pad_label
    
    def forward(self, inputs, outputs):
        # inputs(images): B x C_in x W x H
        # outputs(words): B x N_out
        # B x C_act
        activations = self.resnet(inputs)
        B, C_act = activations.size()
        assert C_act == 512
        # translate resnet activation outputs to transformer inputs
        # B x C_act(N_in)
        filter_inputs = torch.arange(C_act).unsqueeze(0).repeat(B, 1).to(activations.device)
        # B x C_act(N_in)
        pad_mask = activations <= 0.5
        # B x C_act(N_in)
        filter_inputs = filter_inputs.masked_fill(pad_mask, self.pad_label)
        # B x N_out x vocab_size
        out = self.transformer(filter_inputs, outputs)
        return out