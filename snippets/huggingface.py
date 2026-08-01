*** Installation
https://huggingface.co/docs/transformers/installation

# download file
https://huggingface.co/docs/huggingface_hub/en/guides/download


from huggingface_hub import snapshot_download, hf_hub_download
# snapshot_download(repo_id="google/vit-large-patch16-224-in21k", cache_dir="./vit-large-patch16-224-in21k")
for f in ["config.json", "pytorch_model.bin", "preprocessor_config.json"]:
  hf_hub_download(repo_id='facebook/dinov2-base', filename=f, cache_dir="./vit-large-patch16-224-in21k")


*** tokenizer

tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
token_ids = tokenizer.encode("Once upon a time")
tokens = tokenizer.convert_ids_to_tokens(token_ids)

print(token_ids)
print(tokens)


*** load ckpt

from typing import Optional, Any
from pydantic import BaseModel

import logging, time, asyncio
import torchvision.transforms as T
import torch
from transformers import AutoImageProcessor, AutoModel
from PIL import Image
import io, os
from autoops import config
from autoops.utils import Timer
from autoops.object_storage import TosClient

import base64
from PIL import Image
from io import BytesIO

MODEL_NAME_ALIAS = {
    'vit': 'google/vit-large-patch16-224-in21k',
    'swin': 'microsoft/swinv2-large-patch4-window12-192-22k',
    'dinov2': 'facebook/dinov2-base'
}


class EmbeddingModel(BaseModel):
  model_name: str
  model: Optional[Any] = None
  image_processor: Optional[Any] = None
  hidden_dim: Optional[int] = None

  class Config:
    extra = 'forbid'
    use_enum_values = True
    protected_namespaces = ()


class EmbeddingModelStore:

  def __init__(self, model_names: Optional[list[str]] = []):
    self._model_stores = {}
    self._tos_client = TosClient()
    for model_name in model_names + config.emb_models:
      self._load_model(model_name)

  def _load_model(self, model_name: str):
    assert model_name in MODEL_NAME_ALIAS
    if model_name in self._model_stores:
      return
    real_model_name = MODEL_NAME_ALIAS[model_name]
    dir_name = os.path.join(os.path.dirname(__file__), real_model_name)
    model_writedone_file = os.path.join(os.path.dirname(__file__),
                                        real_model_name + ".write.done")
    if not os.path.exists(dir_name):
      os.makedirs(dir_name)
      assert not os.path.exists(model_writedone_file)
      files = self._tos_client.list_objects("model-store", real_model_name)
      logging.info(f"downloading {real_model_name} from tos, files: {files}")
      for file in files:
        self._tos_client.get_object_to_file("model-store", file,
                                            os.path.dirname(__file__))
      with open(model_writedone_file, "w") as f:
        f.write("")
    else:
      if not os.path.exists(model_writedone_file):
        while True:
          logging.info(
              f"model {real_model_name} is not writedone, waiting for 10s")
          time.sleep(10)
          if os.path.exists(model_writedone_file):
            break

    model_ckpt_file = os.path.join(os.path.dirname(__file__), real_model_name)
    model = AutoModel.from_pretrained(model_ckpt_file, local_files_only=True)
    use_fast = True
    if model_name == 'dinov2':
      use_fast = False
    image_processor = AutoImageProcessor.from_pretrained(model_ckpt_file,
                                                         local_files_only=True,
                                                         use_fast=use_fast)
    self._model_stores[model_name] = EmbeddingModel(
        model_name=model_name,
        model=model,
        image_processor=image_processor,
        hidden_dim=model.config.hidden_size)
    logging.info(f"successfully load model {model_name}")

  def get_embeddings(self, images: str | list[str], model_name):
    return asyncio.run(self.async_get_embeddings(images, model_name))

  async def async_get_embeddings(self, images: str | list[str], model_name):
    assert isinstance(images, list) or isinstance(images, str), images
    single_image = False
    if isinstance(images, str):
      images = [images]
      single_image = True
    if model_name not in self._model_stores:
      self._load_model(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = self._model_stores[model_name]
    images = [
        Image.open(BytesIO(base64.b64decode(base64_string)))
        for base64_string in images
    ]
    with Timer(f'{model_name}_get_embeddings', force=True):
      image_batch_transformed = model.image_processor(
          images, return_tensors='pt')['pixel_values'].to(device)
      new_batch = {"pixel_values": image_batch_transformed.to(device)}
      with torch.no_grad():
        if model_name == 'swin':
          embeddings = model.model.to(device)(**new_batch).pooler_output
        else:
          embeddings = model.model.to(device)(**new_batch).last_hidden_state
          embeddings = embeddings[:, 0].cpu()
    if single_image:
      embeddings = embeddings[0]
    return embeddings.tolist()

