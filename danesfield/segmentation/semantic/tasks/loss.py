###############################################################################
# Copyright Kitware Inc. and Contributors
# Distributed under the Apache License, 2.0 (apache.org/licenses/LICENSE-2.0)
# See accompanying Copyright.txt and LICENSE files for details
###############################################################################

import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.functional import binary_cross_entropy_with_logits


def dice_round(preds, trues, is_average=True):
    preds = torch.round(preds)
    return dice(preds, trues, is_average=is_average)


def dice(preds, trues, weight=None, is_average=True):
    num = preds.size(0)
#    for i in range(num):
#        predmat = preds[i,0,:,:].cpu().detach().numpy()
#        truemat = trues[i,0,:,:].cpu().detach().numpy()
#        plt.subplot(121)
#        plt.imshow(predmat)
#        plt.title('prediction')
#        plt.subplot(122)
#        plt.imshow(truemat)
#        plt.title('true')
#        plt.show()

    preds = preds.view(num, -1)
    trues = trues.view(num, -1)
    if weight is not None:
        w = torch.autograd.Variable(weight).view(num, -1)
        preds = preds * w
        trues = trues * w
    intersection = (preds * trues).sum(1)
    scores = 2. * (intersection + 1) / (preds.sum(1) + trues.sum(1) + 1)

    score = scores.sum()
    if is_average:
        score /= num
    return torch.clamp(score, 0., 1.)


class DiceLoss(nn.Module):
    def __init__(self, size_average=True):
        super().__init__()
        self.size_average = size_average

    def forward(self, input, target, weight=None):
        return 1 - dice(F.sigmoid(input), target, weight=weight, is_average=self.size_average)


class BCELoss(nn.Module):
    def __init__(self, size_average=True):
        super().__init__()
        self.size_average = size_average

    def forward(self, input, target, weight=None):
        return binary_cross_entropy_with_logits(input, target, size_average=self.size_average)


class BCELossWeighted(nn.Module):
    def __init__(self, size_average=True):
        super().__init__()
        self.size_average = size_average

    def forward(self, input, target, weight=None):
        pos_count = 0
        if target.nonzero().dim() > 0:
            pos_count = target.nonzero().size()[0]

        neg_count = 1
        if (target == 0).nonzero().dim() > 0:
            neg_count = (target == 0).nonzero().size()[0]
        w = pos_count/neg_count
        return binary_cross_entropy_with_logits(input, target, weight=w,
                                                size_average=self.size_average)


class BCEDiceLoss(nn.Module):
    def __init__(self, size_average=True):
        super().__init__()
        self.size_average = size_average

    def forward(self, input, target, weight=None):
        return (binary_cross_entropy_with_logits(input, target, size_average=self.size_average)
                + 1 - dice(F.sigmoid(input), target, is_average=self.size_average))


class BCEDiceLossWeighted(nn.Module):
    def __init__(self, size_average=True):
        super().__init__()
        self.size_average = size_average

    def forward(self, input, target, weight=None):
        return (1.5 * binary_cross_entropy_with_logits(input, target,
                size_average=self.size_average) +
                .5 * (1 - dice(F.sigmoid(input), target, is_average=self.size_average)))
