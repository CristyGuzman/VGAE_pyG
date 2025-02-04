import os

import torch
import torch.nn as nn
from torch.optim import Adam

from torch_geometric.datasets import Planetoid
import torch_geometric.transforms as T
from torch_geometric.utils import train_test_split_edges

from model import DeepVGAE
from config.config import parse_args

torch.manual_seed(12345)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

args = parse_args()

model = DeepVGAE(args).to(device)
optimizer = Adam(model.parameters(), lr=args.lr)

os.makedirs("datasets", exist_ok=True)
transform = T.Compose([
        T.NormalizeFeatures(),
        T.ToDevice(device),
        T.RandomLinkSplit(num_val=0.05, num_test=0.1, is_undirected=True,
                          split_labels=True, add_negative_train_samples=True),
    ])
dataset = Planetoid("datasets", args.dataset, transform=transform)
data = dataset[0]
train_data, valid_data, test_data = data
all_edge_index = train_data.edge_index


for epoch in range(args.epoch):
    model.train()
    optimizer.zero_grad()
    loss = model.loss(train_data.x, train_data.pos_edge_label_index, all_edge_index)
    loss.backward()
    optimizer.step()
    if epoch % 2 == 0:
        model.eval()
        roc_auc, ap = model.single_test(train_data.x,
                                        train_data.pos_edge_label_index,
                                        test_data.pos_edge_label_index,
                                        test_data.neg_edge_label_index)
        print("Epoch {} - Loss: {} ROC_AUC: {} Precision: {}".format(epoch, loss.cpu().item(), roc_auc, ap))
