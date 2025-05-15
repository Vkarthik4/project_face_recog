# models/mobilefacenet.py

import torch.nn as nn
import torch.nn.functional as F


class Flatten(nn.Module):
    def forward(self, x):
        return x.view(x.size(0), -1)


class MobileFaceNet(nn.Module):
    def __init__(self, embedding_size=128):
        super(MobileFaceNet, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 64, 3, 2, 1, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64)
        )
        self.conv2_dw = nn.Sequential(
            nn.Conv2d(64, 64, 3, 1, 1, groups=64, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64),
            nn.Conv2d(64, 64, 1, 1, 0, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64)
        )
        self.conv_23 = nn.Sequential(
            nn.Conv2d(64, 128, 3, 2, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv_3_dw = nn.Sequential(
            nn.Conv2d(128, 128, 3, 1, 1, groups=128, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128),
            nn.Conv2d(128, 128, 1, 1, 0, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv_34 = nn.Sequential(
            nn.Conv2d(128, 128, 3, 2, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv_4_dw = nn.Sequential(
            nn.Conv2d(128, 128, 3, 1, 1, groups=128, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128),
            nn.Conv2d(128, 128, 1, 1, 0, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv_45 = nn.Sequential(
            nn.Conv2d(128, 128, 3, 2, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv_5_dw = nn.Sequential(
            nn.Conv2d(128, 128, 3, 1, 1, groups=128, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128),
            nn.Conv2d(128, 128, 1, 1, 0, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.conv6_sep = nn.Sequential(
            nn.Conv2d(128, 512, 1, 1, 0, bias=False),
            nn.BatchNorm2d(512),
            nn.PReLU(512)
        )
        self.conv6_dw = nn.Sequential(
            nn.Conv2d(512, 512, 7, 1, 0, groups=512, bias=False),
            nn.BatchNorm2d(512),
            nn.PReLU(512)
        )
        self.conv6_proj = nn.Sequential(
            nn.Conv2d(512, embedding_size, 1, 1, 0, bias=False),
            nn.BatchNorm2d(embedding_size)
        )
        self.flatten = Flatten()

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2_dw(x)
        x = self.conv_23(x)
        x = self.conv_3_dw(x)
        x = self.conv_34(x)
        x = self.conv_4_dw(x)
        x = self.conv_45(x)
        x = self.conv_5_dw(x)
        x = self.conv6_sep(x)
        x = self.conv6_dw(x)
        x = self.conv6_proj(x)
        x = self.flatten(x)
        x = F.normalize(x, p=2, dim=1)
        return x
