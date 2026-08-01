### grad

https://pytorch.org/docs/stable/notes/autograd.html#locally-disabling-gradient-computation


x = torch.tensor([[1., -1.], [1., 1.]], requires_grad=True)
x.grad

torch.no_grad()禁用梯度

with torch.no_grad():
	y = x * 2

@torch.no_grad()
def doubler(x):
	return x * 2

with torch.no_grad():
	a = torch.nn.Parameter(torch.rand(10))
	a.requires_grad

# 例外：
所有工厂函数或创建新张量的函数，都不受此模式的影响
工厂函数是用于生成tensor的函数。常见的工厂函数有torch.rand、torch.randint、torch.randn、torch.eye等
pytorch觉得你是创建网络的训练权重，所以此时requires_grad的默认值是true。

# requires_grad默认是False

### load&store


x = torch.tensor([0, 1, 2, 3, 4])
torch.save(x, "tensor.pt")

torch.load("tensors.pt", weights_only=True)
torch.load("tensors.pt", map_location=torch.device("cpu"), weights_only=True)
state = torch.load("tensors.pt", map_location=torch.device("cuda:0"), weights_only=True)

model = MyNet()

torch.save(model.state_dict(), "model_weights.pth")
model.load_state_dict(state)

torch.save(model, "model.pth")
model = torch.load("model.pth", weights_only=False)

# OrderedDict([
#             ("nn1.weight", tensor([[-0.1838, -0.2477],[ 0.4845,  0.3157],[-0.5628,  0.3612]])), 
#             ("nn1.bias", tensor([-0.4328, -0.6779,  0.3845])), 
#             ("nn2.weight", tensor([[-5.0585e-01, -4.6973e-01,  1.6044e-02],[-3.4606e-01,  1.1130e-01, -2.0727e-01],
#                                     [-3.9844e-02, -4.2531e-01,  8.2558e-02],[ 3.3171e-02, -3.4334e-01,  4.5039e-01],
#                                     [-2.5320e-04, -5.2037e-01,  1.3504e-02],[-3.0776e-01,  8.9345e-02, -1.1076e-01]])),                 
#             ("nn2.bias", tensor([ 0.1229, -0.2344,  0.0568, -0.3430,  0.2715, -0.3521]))
# ])

optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

# 保存优化器
EPOCH = 5
PATH = "model.pt"
LOSS = 0.4
torch.save({
            "epoch": EPOCH,
            "model_state_dict": net.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "loss": LOSS,
            }, PATH)

# 加载优化器
model = MyModel()
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

checkpoint = torch.load(PATH, weights_only=True)
model.load_state_dict(checkpoint["model_state_dict"])
optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
epoch = checkpoint["epoch"]
loss = checkpoint["loss"]

# 跨设备保存和加载

# Save on GPU, Load on CPU
torch.save(model.state_dict(), PATH)
model = MyModel()
model.load_state_dict(torch.load(PATH, map_location=torch.device("cpu"), weights_only=True))

# Save on CPU, Load on GPU
torch.save(net.state_dict(), PATH)
model = MyModel()
model.load_state_dict(torch.load(PATH, map_location="cuda:0"))
# Make sure to call input = input.to(device) on any input tensors that you feed to the model
device = torch.device("cuda")
model.to(device)

#Save on GPU, Load on GPU
torch.save(net.state_dict(), PATH)
model = MyModel()
model.load_state_dict(torch.load(PATH))
model.to(torch.device("cuda")) 

# map_location

tensors = torch.load("tensors.pt", map_location={"cuda:1":"cuda:0"})
# 这样指定为了避免cuda:1异常导致加载到cuda:0失败

### parameter

torch.nn.parameter.Parameter(data=None, requires_grad=True)
torch.nn.parameter.UninitializedParameter(requires_grad=True, device=None, dtype=None)

# UninitializedParameter多用于lazy模块
- 根据shape、device，lazy initialize

class LinearRegressionModel(nn.Module):
    def __init__(self):
        super(LinearRegressionModel, self).__init__()
        self.weight = nn.Parameter(torch.randn(1))
        self.bias = nn.Parameter(torch.randn(1))

    def forward(self, x):
        return self.weight * x + self.bias

class CustomModule(nn.Module):
    def __init__(self):
        super(CustomModule, self).__init__()
        self.weight = torch.nn.parameter.UninitializedParameter(requires_grad=True)
        self.bias = torch.nn.parameter.UninitializedParameter(requires_grad=True)

    def forward(self, x):
        if self.weight.shape[0]!= x.shape[1]:
            self.weight.data = torch.randn(x.shape[1], requires_grad=True)
            self.bias.data = torch.randn(1, requires_grad=True)
        output = torch.matmul(self.weight, x) + self.bias
        return output


### 动态图
loss1 = z.mean()
loss2 = z.sum()
print(loss1,loss2)
loss1.backward(retain_graph=True)
loss2.backward()


### Learning Rate

LambdaLR
from torch.optim.lr_scheduler import ReduceLROnPlateau


*** 数据不均问题 —— Generic Join Context Manager

https://docs.pytorch.org/tutorials/advanced/generic_join.html

https://docs.pytorch.org/docs/stable/distributed.algorithms.join.html


### Example

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import Dataset, DataLoader

async def process_file(src_file, output_file):
  with open(src_file, 'r') as src_stream:
    data = json.load(src_stream)
  with open(output_file, 'w') as dst_stream:
    for i, item in enumerate(data):
      logging.info(f"process item {i}")
      try:
        item = await process_item(item)
        json.dump(item, dst_stream, ensure_ascii=False)
        dst_stream.write('\n')
      except Exception as e:
        logging.error(f"process item failed: {e}, {item}")
        continue
  return data


async def read_data_from_file(file,
                              feature_list: list[str],
                              select_indices=None,
                              query_recall_len=None):
  assert isinstance(feature_list, list)
  assert all(isinstance(f, str) for f in feature_list)
  assert select_indices is None or isinstance(select_indices, list)
  with open(file, 'r') as stream:
    data = [json.loads(line) for line in stream.readlines()]
    labels = []
    features = []
    query_groups = {}
    for i, item in enumerate(data):
      try:
        labels.append(item["avg"] / 100)
        feature = [item[f] for f in feature_list]
        features.append(feature)
        query = item['query']
        if query not in query_groups:
          query_groups[query] = []
        if len(query_groups[query]) < query_recall_len:
          query_groups[query].append((len(features) - 1, None))
        if i % 1000 == 0:
          logging.info(f"read data from file, item num: {i}")
      except Exception as e:
        logging.error(f"process data failed: {e}")
        continue
  features_df = pd.DataFrame(features, columns=feature_list)
  correlation_matrix = features_df.corr()

  pd.set_option('display.max_columns', None)
  pd.set_option('display.width', None)
  pd.set_option('display.max_rows', None)
  logging.info(f"correlation_matrix:\n{correlation_matrix}")
  pd.reset_option('display.max_columns')
  pd.reset_option('display.width')
  pd.reset_option('display.max_rows')

  labels = np.array(labels)
  features = np.array(features)
  if select_indices:
    features = np.take(features, select_indices, axis=-1)
  return features, labels, query_groups


class RankDataset(Dataset):

  def __init__(self, data, labels, model_name):
    self.data = data
    self.labels = labels
    self.model_name = model_name

  def __len__(self):
    return len(self.data)

  def __getitem__(self, idx):
    if FEATURE_LIST_MAP[
        self.model_name][MODEL_TYPE] == LISTWISE or FEATURE_LIST_MAP[
            self.model_name][MODEL_TYPE] == POS_LISTWISE:
      res_data = torch.tensor(self.data[idx], dtype=torch.float32)
      res_labels = self.labels[idx]
      return res_data, res_labels
    else:
      return self.data[idx], self.labels[idx]


class RankModel(nn.Module):

  def __init__(self, model_name):
    super(RankModel, self).__init__()
    self.fc1 = nn.LazyLinear(50)
    self.fc2 = nn.Linear(50, 1)
    self.fc3 = nn.Linear(50, 50)
    self.relu = nn.LeakyReLU(negative_slope=0.01)
    # self.relu = nn.ReLU()
    # self.relu = nn.PReLU()

    self._model_name = model_name
    self._model_type = FEATURE_LIST_MAP[model_name][MODEL_TYPE]
    self._rrf_strategy = FEATURE_LIST_MAP[model_name][RRF_STRATEGY]

  def forward(self, x):
    if self._rrf_strategy == BOTH or self._rrf_strategy == RR:
      if self._model_type == POINTWISE:
        rr = torch.argsort(x, dim=0, descending=True)
      else:
        rr = torch.argsort(x, dim=1, descending=True)
      rr = 1 / (torch.log((rr + 1)) + 1)
      if self._rrf_strategy == BOTH:
        x = torch.concat((x, rr), dim=-1)
    x = self.relu(self.fc1(x))
    x = self.relu(self.fc3(x))
    x = self.fc2(x)

    if self._model_type == POINTWISE:
      x = torch.sigmoid(x)
    return x.squeeze()

  def predict(self, data):
    self.eval()
    with torch.no_grad():
      data = torch.tensor(data, dtype=torch.float32)
      predictions = self(data)
    return predictions.numpy()

  def evaluate(self, inputs, targets, criterion=None):
    val_loss = 0.0
    ndcg_sum = 0.0
    inputs = inputs.clone().detach().to(torch.float32)
    targets = targets.clone().detach().to(torch.float32)
    outputs = self(inputs)
    if outputs.dim() == 1:
      outputs = outputs.unsqueeze(0)
    if targets.dim() == 1:
      targets = targets.unsqueeze(0)
    if criterion:
      if self._model_type == POS_LISTWISE:
        tmp_loss = criterion(outputs, targets, position_aware=True).item()
      else:
        tmp_loss = criterion(outputs, targets).item()
      val_loss += tmp_loss

    if self._model_type == POINTWISE:
      ndcg_sum += ndcg_score(targets, outputs)
    else:
      batch_size = targets.shape[0]
      for i in range(batch_size):
        valid_target = targets[i][targets[i] != PADDED_Y_VALUE].unsqueeze(0)
        valid_output = outputs[i][targets[i] != PADDED_Y_VALUE].unsqueeze(0)
        ndcg_sum += ndcg_score(valid_target, valid_output) / batch_size
    return val_loss, ndcg_sum


@lru_cache
def get_feature_list(model_name: str):
  feature_list = FEATURE_LIST_MAP[model_name]['feature']
  return feature_list


@lru_cache
def get_rank_model(model_name: str):
  model = get_rank_model_def(model_name)
  model.load_state_dict(
      torch.load(os.path.join(os.path.dirname(__file__), f'{model_name}.pth'),
                 weights_only=True))
  return model


def get_rank_model_def(model_name: str):
  model = RankModel(model_name)
  return model


def rank_model_predict(datas, model_name):
  scaler = joblib.load(
      os.path.join(os.path.dirname(__file__), f'{model_name}.scaler'))
  datas = [[item[f] for f in get_feature_list(model_name)] for item in datas]
  datas = np.array(datas)
  # if FEATURE_LIST_MAP[model_name][MODEL_TYPE] == POINTWISE:
  datas = scaler.transform(datas)
  if SELECT_INDICES is not None:
    datas = np.take(datas, SELECT_INDICES, axis=-1)
  model = get_rank_model(model_name)
  prediction = model.predict(datas).tolist()
  return prediction


def train_deep_learning_model(dataset_file,
                              model_name,
                              model_type,
                              load_ckpt=False):
  data, labels, query_groups = asyncio.run(
      read_data_from_file(dataset_file,
                          FEATURE_LIST_MAP[model_name]['feature'],
                          select_indices=SELECT_INDICES,
                          query_recall_len=QUERY_RECALL_LEN))

  scaler = MinMaxScaler()
  scaler.fit(data)
  joblib.dump(scaler,
              os.path.join(os.path.dirname(__file__), f'{model_name}.scaler'))
  data = scaler.transform(data)

  if model_type in [LISTWISE, POS_LISTWISE]:
    for query, group in query_groups.items():
      for i, group_tuple in enumerate(group):
        group[i] = (group_tuple[0], data[group_tuple[0]])
      # assert len(group) == QUERY_RECALL_LEN, group
    data, labels = convert_to_list_mle_samples(query_groups, labels,
                                               QUERY_RECALL_LEN)

  # logging.info(
  #     f'data shape: {len(data)}, {data[0]}, labels shape: {len(labels)}, {labels[0]}'
  # )

  X_train, X_val, y_train, y_val = train_test_split(data,
                                                    labels,
                                                    test_size=0.2,
                                                    random_state=42)

  batch_size = 5 if model_type in [LISTWISE, POS_LISTWISE] else 50
  train_dataset = RankDataset(X_train, y_train, model_name)
  train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)

  val_dataset = RankDataset(X_val, y_val, model_name)
  val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

  model = get_rank_model_def(model_name)

  if load_ckpt:
    model.load_state_dict(
        torch.load(os.path.join(os.path.dirname(__file__), f'{model_name}.pth'),
                   weights_only=True))

  if model_type in [LISTWISE, POS_LISTWISE]:
    criterion = listMLE
  else:
    criterion = nn.SmoothL1Loss(reduction='mean', beta=0.1)
  # criterion = nn.L1Loss()
  # criterion = nn.MSELoss()

  if model_type in [LISTWISE, POS_LISTWISE]:
    init_lr = 0.006
  else:
    init_lr = 0.01
  if load_ckpt:
    init_lr *= 0.2

  optimizer = optim.Adam(model.parameters(), lr=init_lr)  # weight_decay=0.001

  if model_type in [LISTWISE, POS_LISTWISE]:
    patience = 40
  else:
    patience = 100
  scheduler = ReduceLROnPlateau(optimizer,
                                mode='max',
                                factor=0.6,
                                patience=patience,
                                min_lr=0.001)
  no_improvement_threshold = 100 if model_type in [LISTWISE, POS_LISTWISE
                                                  ] else 180
  loss_no_improvement_count = 0
  ndcg_no_improvement_count = 0
  best_loss_epoch = 0
  best_ndcg_epoch = 0
  best_loss = float('inf')
  best_ndcg = 0.0

  for epoch in range(1000):
    model.train()
    running_loss = 0.0
    for inputs, targets in train_loader:
      # logging.error(f'inputs: {inputs},\n targets: {targets}')
      if model_type == POINTWISE:
        inputs = inputs.clone().detach().to(torch.float32)
        targets = targets.clone().detach().to(torch.float32)
      optimizer.zero_grad()
      outputs = model(inputs)
      if outputs.dim() == 1:
        outputs = outputs.unsqueeze(0)
      if targets.dim() == 1:
        targets = targets.unsqueeze(0)

      if model_type == POS_LISTWISE:
        loss = criterion(outputs, targets, position_aware=True)
      else:
        loss = criterion(outputs, targets)
      loss.backward()
      optimizer.step()

      running_loss += loss.item()

    epoch_loss = running_loss / len(train_loader)
    current_lr = optimizer.param_groups[0]['lr']

    model.eval()
    with torch.no_grad():
      for inputs, targets in val_loader:
        val_loss, ndcg_sum = model.evaluate(inputs, targets, criterion)
      val_epoch_loss = val_loss / len(val_loader)
      val_epoch_ndcg = ndcg_sum / len(val_loader)
      scheduler.step(val_epoch_ndcg)
    logging.info(
        f'Epoch {epoch}/{500}, Loss: {epoch_loss:.4f}, Eval Loss: {val_epoch_loss:.4f}, NDCG: {val_epoch_ndcg:.4f}, lr: {current_lr:.6f}'
    )

    if val_epoch_loss < best_loss:
      best_loss = val_epoch_loss
      best_loss_epoch = epoch
      loss_no_improvement_count = 0
      # torch.save(
      #     model.state_dict(),
      #     os.path.join(os.path.dirname(__file__),
      #                  f'output_{model_name}_loss_{epoch}.pth'))
    else:
      loss_no_improvement_count += 1
      # if loss_no_improvement_count >= no_improvement_threshold:
      #   logging.info(f'Early stopping at epoch {epoch}')
      #   break

    if val_epoch_ndcg > best_ndcg:
      best_ndcg = val_epoch_ndcg
      best_ndcg_epoch = epoch
      ndcg_no_improvement_count = 0
      torch.save(
          model.state_dict(),
          os.path.join(os.path.dirname(__file__),
                       f'output_{model_name}_ndcg_{epoch}.pth'))
    else:
      ndcg_no_improvement_count += 1
      if ndcg_no_improvement_count >= no_improvement_threshold:
        logging.info(f'Early stopping at epoch {epoch}')
        break

  logging.info(
      f'Best Loss Epoch: {best_loss_epoch}, Best Eval Loss: {best_loss:.4f}')
  logging.info(
      f'Best NDCG Epoch: {best_ndcg_epoch}, Best NDCG: {best_ndcg:.4f}')


def eval_deep_learning_model(dataset_file, model_name, model_type):
  data, labels, query_groups = asyncio.run(
      read_data_from_file(dataset_file,
                          FEATURE_LIST_MAP[model_name]['feature'],
                          select_indices=SELECT_INDICES,
                          query_recall_len=QUERY_RECALL_LEN))
  scaler = joblib.load(
      os.path.join(os.path.dirname(__file__), f'{model_name}.scaler'))
  data = scaler.transform(data)

  if model_type in [LISTWISE, POS_LISTWISE]:
    for query, group in query_groups.items():
      for i, group_tuple in enumerate(group):
        group[i] = (group_tuple[0], data[group_tuple[0]])
      # assert len(group) == QUERY_RECALL_LEN, group
    data, labels = convert_to_list_mle_samples(query_groups, labels,
                                               QUERY_RECALL_LEN)

  X_train, X_val, y_train, y_val = train_test_split(
      data,
      labels,
      test_size=0.5,
  )
  # random_state=42)

  batch_size = 5 if model_type in [LISTWISE, POS_LISTWISE] else 50

  val_dataset = RankDataset(X_val, y_val, model_name)
  val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

  model = get_rank_model_def(model_name)

  model.load_state_dict(
      torch.load(os.path.join(os.path.dirname(__file__), f'{model_name}.pth'),
                 weights_only=True))
  model.eval()
  ndcg_sum = 0.0
  with torch.no_grad():
    for inputs, targets in val_loader:
      _, ndcg_sum = model.evaluate(inputs, targets, None)
    val_epoch_ndcg = ndcg_sum / len(val_loader)
  logging.info(
      f'Eval {model_name}, Dataset: {dataset_file} NDCG: {val_epoch_ndcg:.4f}')