import base64
from PIL import Image
from io import BytesIO

image_data = base64.b64decode(base64_string)
img = Image.open(BytesIO(image_data))


### EfficientNet: Extracts flag features by averaging the spatial dimensions of the last hidden layer’s outputs, focusing on fine-grained patterns.

image_processor = AutoImageProcessor.from_pretrained("google/efficientnet-b7")
model = EfficientNetModel.from_pretrained("google/efficientnet-b7")

# prepare input image
inputs = image_processor(img, return_tensors='pt')

with torch.no_grad():
    outputs = model(**inputs, output_hidden_states=True)

embedding = outputs.hidden_states[-1]
embedding = torch.mean(embedding, dim=[2,3])


### ViT: Uses the last hidden state of the first token in its transformer architecture, capturing both local and global visual features.

# embedding = embedding[:, 0, :].squeeze(1)
# 第一个时间步的hidden state，对应于CLS token
# 1024维

image_processor = AutoImageProcessor.from_pretrained("google/vit-large-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-large-patch16-224-in21k")

# prepare input image
inputs = image_processor(img, return_tensors='pt')

with torch.no_grad():
    outputs = model(**inputs)
embedding = outputs.last_hidden_state
embedding = embedding[:, 0, :].squeeze(1)


### DINO-v2: Generates embeddings by focusing on self-supervised learning, utilizing the first token to capture object-centric details.

image_processor = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
model = AutoModel.from_pretrained('facebook/dinov2-base')

# prepare input image
inputs = image_processor(img, return_tensors='pt')

with torch.no_grad():
    outputs = model(**inputs)
embedding = outputs.last_hidden_state
embedding = embedding[:, 0, :].squeeze(1)


### CLIP

image_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

# prepare input image
inputs = image_processor(images=img, return_tensors='pt', padding=True)

with torch.no_grad():
    embedding = model.get_image_features(**inputs) 


### BLIP:  Employs a vision-language model, extracting features via its query-focused transformer (Q-Former) 
# to capture image semantics and relationships.

image_processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = Blip2Model.from_pretrained("Salesforce/blip2-opt-2.7b", torch_dtype=torch.float16)

inputs = image_processor(images=img, return_tensors='pt', padding=True)
print('input shape: ', inputs['pixel_values'].shape)

with torch.no_grad():
    outputs = model.get_qformer_features(**inputs)
embedding = outputs.last_hidden_state
embedding = embedding[:, 0, :].squeeze(1)


### SWIN

https://huggingface.co/microsoft/swinv2-large-patch4-window12-192-22k

latent_dim: 1536


### VGG16: A CNN model that outputs flag embeddings by applying a stack of convolution layers, emphasizing hierarchical image representations.

model = models.vgg16(pretrained=True) 
model.eval()  # Set the model to evaluation mode

batch_t = torch.unsqueeze(img, 0)

with torch.no_grad():
    embedding = model(batch_t)