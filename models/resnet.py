# Implementation of resnet from scratch
# Details refer to: https://arxiv.org/pdf/1512.03385.pdf
import torch
import torch.nn as nn

class BottleneckBlock(nn.Module):
    # block with 3 conv layers: 1x1xc_out[0] -> 3x3xc_out[1] -> 1x1xc_out[2]
    # surounded by residual connection 
    def __init__(self, c_in, c_outs, stride=1):
        self.conv0 = nn.Conv2d(c_in, c_outs[0], 1, stride=stride, bias=False)
        self.bn0 = nn.BatchNorm2d(c_outs[0])
        self.conv1 = nn.Conv2d(c_outs[0], c_outs[1], 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(c_outs[1])
        self.conv2 = nn.Conv2d(c_outs[1], c_outs[2], 1, bias=False)
        self.bn2 = nn.BatchNorm2d(c_outs[2])
        # project identity to have the same dimension as the output 
        self.conv_identity = nn.Conv2d(c_in, c_outs[2], 1, stride=stride)
        self.bn_identity = nn.BatchNorm2d(c_outs[2])
        self.relu = nn.ReLU()

    def forward(self, x):
        # x: B x C x W x H 
        # B x c_outs[0] x W x H
        out = self.conv0(x)
        out = self.bn0(out)
        out = self.relu(out)

        # B x c_outs[1] x W x H
        out = self.conv1(out)
        out = self.bn1(out)
        out = self.relu(out)

        # B x c_outs[2] x W x H
        out = self.conv2(out)
        out = self.bn2(out)

        # B x c_outs[2] x W x H
        identity = self.conv_identity(x)
        identity = self.bn_identity(identity)

        # residual connection
        out = out + identity
        out = self.relu(out)

        return out

class ResNet(nn.Module):
    # type: 'resnet18', 'resnet50'
    def __init__(self, type, num_classes):
        self.conv0 = nn.Conv2d(3, 64, 7, stride=2, padding=3, bias=False)
        self.max_pool = nn.MaxPool2d(3, stride=2, padding=1)
        # populate all residual layers
        if self.type == 'resnet18':
            self.res_layers = [ 
                self._make_layer(BasicBlock, 64, [64, 64], 2),
                self._make_layer(BasicBlock, 64, [128, 128], 2),
                self._make_layer(BasicBlock, 128, [256, 256], 2),
                self._make_layer(BasicBlock, 256, [512, 512], 2)
            ]
            self.projection = nn.Linear(512, num_classes)
        elif self.type == 'resnet50':
            self.res_layers = [
                self._make_layer(BottleneckBlock, 64, [64, 64, 256], 3)
                self._make_layer(BottleneckBlock, 256, [128, 128, 512], 4)
                self._make_layer(BottleneckBlock, 512, [256, 256, 1024], 6)
                self._make_layer(BottleneckBlock, 1024, [512, 512, 2048], 3)
            ]
            self.projection = nn.Linear(2048, num_classes)
        
        self.avg_pool = nn.AvgPool2d(7)
        self.softmax = nn.Softmax(dim=1)
    
    def _make_layer(self, BlockType, channels_in, channels_out, num_layer):
        layers = []
        # first layer has a stride of 2
        layers.append(BlockType(channels_in, channels_out, stride=2))
        # rest layers have a stride of 1
        for i in range(num_layer-1):
            layers.append(BlockType(channels_in, channels_out))

        return nn.Sequential(*layers)

    def forward(self, x):
        # x: B x 3 x W x H
        out = self.conv0(x)
        out = self.max_pool(out)
        for layer in self.res_layers:
            out = layer(out)
        out = self.avg_pool(out)
        out = self.softmax(out)
        
        return out