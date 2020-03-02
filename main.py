"""

trainig Cifar-100 greayscale with Resnet18
"""
from pkgutil import get_loader

from models.resnet import ResNet18, ResNet50
from utils import *
'''Train CIFAR10 with PyTorch.'''
import torch
import torch.nn as nn
import torch.optim as optim
import torch.backends.cudnn as cudnn
from data import get_dataloader
from torch.utils.tensorboard import SummaryWriter
import os
import argparse


# --------Parameters ---------####

parser = argparse.ArgumentParser(description='PyTorch greyScale CIFAR100 Training')
parser.add_argument('--lr', default=0.1, type=float, help='learning rate')
parser.add_argument('--resume', '-r', default=False, action='store_true', help='resume from checkpoint')
# parser.add_argument('--dataset', type=str, default='cifar100', help='cifar10 | cifar100 | folder')
# parser.add_argument('--dataroot', type=str, default='./data', help='path to dataset')
parser.add_argument('--model', type=str, help='Which model to run')
parser.add_argument('--workers', type=int, default=2, help='number of data loading workers')
parser.add_argument('--batchSize', type=int, default=16, help='input batch size')
parser.add_argument('--nEpochs', type=int, default=100, help='number of epochs to train for')
parser.add_argument('--cuda', action='store_true', help='enables cuda')
parser.add_argument('--nGPU', type=int, default=1, help='number of GPUs to use')
parser.add_argument('--out', type=str, default='checkpoint', help='folder to output model checkpoint')

opt = parser.parse_args()
print(opt)

try:
    os.makedirs(opt.out)
except OSError:
    pass

device = 'cuda' if torch.cuda.is_available() else 'cpu'
best_acc = 0  # best test accuracy
start_epoch = 0  # start from epoch 0 or last checkpoint epoch

# Data
print('=====> Get dataloader ........')
train_loader, test_loader = get_dataloader()

# Model
print('=====> Building model.....')

model = ResNet18()
model = model.to(device)

if device == 'cuda':
    model = torch.nn.DataParallel(model)
    cudnn.benchmark = True


if opt.resume:
    # Load checkpoint.
    print('=====> Resuming from checkpoint <=======......')
    assert os.path.isdir('checkpoint'), 'Error: no checkpoint directory found!'
    checkpoint = torch.load('./checkpoint/ckpt.pth')
    model.load_state_dict(checkpoint['net'])
    best_acc = checkpoint['acc']
    start_epoch = checkpoint['epoch']

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')


criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=opt.lr, momentum=0.9, weight_decay=5e-4)

# TODO: Edit to write for various experiment
writer = SummaryWriter('runs/cifar10-grey')
writer.add_graph(model) # write model architecture
writer.close()


# Training
def train(epoch):
    print('\nEpoch: %d' % epoch)
    model.train()
    train_loss = 0
    correct = 0
    total = 0
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

        if batch_idx % 1000 == 999:  # every 1000 mini-batches...

            # ...log the running loss
            writer.add_scalar('training loss', train_loss / 1000, epoch * len(train_loader) + batch_idx)

            # ...log a Matplotlib Figure showing the model's predictions on a
            # random mini-batch
            writer.add_figure('predictions vs. actuals',
                              plot_classes_preds(model, inputs, targets, classes),
                              global_step=epoch * len(train_loader) + batch_idx)
            running_loss = 0.0

        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()

        progress_bar(batch_idx, len(train_loader), 'Loss: %.3f | Acc: %.3f%% (%d/%d)'
            % (train_loss/(batch_idx+1), 100.*correct/total, correct, total))


def test(epoch):
    global best_acc
    model.eval()
    test_loss = 0
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(test_loader):
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)

            test_loss += loss.item()
            if batch_idx % 1000 == 999:  # every 1000 mini-batches...

                # ...log the test loss
                writer.add_scalar('test loss', test_loss / 1000, epoch * len(test_loader) + batch_idx)
                # ...log a Matplotlib Figure showing the model's predictions on a
                # random mini-batch
                writer.add_figure('predictions vs. actuals',
                                  plot_classes_preds(model, inputs, targets, classes),
                                  global_step=epoch * len(test_loader) + batch_idx)
                running_loss = 0.0
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

            progress_bar(batch_idx, len(test_loader), 'Loss: %.3f | Acc: %.3f%% (%d/%d)'
                % (test_loss/(batch_idx+1), 100.*correct/total, correct, total))

    # Save checkpoint.
    acc = 100.*correct/total
    if acc > best_acc:
        print('Saving..')
        state = {
            'net': model.state_dict(),
            'acc': acc,
            'epoch': epoch,
        }
        if not os.path.isdir('checkpoint'):
            os.mkdir('checkpoint')
        torch.save(state, './checkpoint/ckpt.pth')
        best_acc = acc


for epoch in range(start_epoch, start_epoch+200):
    train(epoch)
    test(epoch)