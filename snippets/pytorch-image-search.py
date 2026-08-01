https://github.com/huggingface/notebooks/blob/main/examples/image_similarity.ipynb

% pip install transformers datasets -q 

import torch
import torchvision.transforms as T
from datasets import load_dataset
from transformers import AutoFeatureExtractor, AutoModel
from tqdm.auto import tqdm
import numpy as np
import matplotlib.pyplot as plt

model_ckpt = "nateraw/vit-base-beans"
extractor = AutoFeatureExtractor.from_pretrained(model_ckpt)
model = AutoModel.from_pretrained(model_ckpt)
hidden_dim = model.config.hidden_size



dataset = load_dataset("beans")
# Check a sample image.
dataset["train"][0]["image"]
dataset["train"].features

labels = dataset["train"].features["labels"].names
label2id, id2label = dict(), dict()

for i, label in enumerate(labels):
    label2id[label] = i
    id2label[i] = label

num_samples = 100
seed = 42
candidate_subset = dataset["train"].shuffle(seed=seed).select(range(num_samples))

# Data transformation chain.
transformation_chain = T.Compose(
    [
        # We first resize the input image to 256x256 and then we take center crop.
        T.Resize(int((256 / 224) * extractor.size["height"])),
        T.CenterCrop(extractor.size["height"]),
        T.ToTensor(),
        T.Normalize(mean=extractor.image_mean, std=extractor.image_std),
    ]
)

def extract_embeddings(model: torch.nn.Module):
    """Utility to compute embeddings."""
    device = model.device

    def pp(batch):
        images = batch["image"]
        image_batch_transformed = torch.stack(
            [transformation_chain(image) for image in images]
        )
        new_batch = {"pixel_values": image_batch_transformed.to(device)}
        with torch.no_grad():
            embeddings = model(**new_batch).last_hidden_state[:, 0].cpu()
        return {"embeddings": embeddings}

    return pp


# Here, we map embedding extraction utility on our subset of candidate images.
batch_size = 24
device = "cuda" if torch.cuda.is_available() else "cpu"
extract_fn = extract_embeddings(model.to(device))
candidate_subset_emb = candidate_subset.map(extract_fn, batched=True, batch_size=24)


candidate_ids = []

for id in tqdm(range(len(candidate_subset_emb))):
    label = candidate_subset_emb[id]["labels"]

    # Create a unique indentifier.
    entry = str(id) + "_" + str(label)

    candidate_ids.append(entry)

all_candidate_embeddings = np.array(candidate_subset_emb["embeddings"])
all_candidate_embeddings = torch.from_numpy(all_candidate_embeddings)

def compute_scores(emb_one, emb_two):
    """Computes cosine similarity between two vectors."""
    scores = torch.nn.functional.cosine_similarity(emb_one, emb_two)
    return scores.numpy().tolist()


def fetch_similar(image, top_k=5):
    """Fetches the `top_k` similar images with `image` as the query."""
    # Prepare the input query image for embedding computation.
    image_transformed = transformation_chain(image).unsqueeze(0)
    new_batch = {"pixel_values": image_transformed.to(device)}

    # Comute the embedding.
    with torch.no_grad():
        query_embeddings = model(**new_batch).last_hidden_state[:, 0].cpu()

    # Compute similarity scores with all the candidate images at one go.
    # We also create a mapping between the candidate image identifiers
    # and their similarity scores with the query image.
    sim_scores = compute_scores(all_candidate_embeddings, query_embeddings)
    similarity_mapping = dict(zip(candidate_ids, sim_scores))
 
    # Sort the mapping dictionary and return `top_k` candidates.
    similarity_mapping_sorted = dict(
        sorted(similarity_mapping.items(), key=lambda x: x[1], reverse=True)
    )
    id_entries = list(similarity_mapping_sorted.keys())[:top_k]

    ids = list(map(lambda x: int(x.split("_")[0]), id_entries))
    labels = list(map(lambda x: int(x.split("_")[-1]), id_entries))
    return ids, labels

test_idx = np.random.choice(len(dataset["test"]))
test_sample = dataset["test"][test_idx]["image"]
test_label = dataset["test"][test_idx]["labels"]

sim_ids, sim_labels = fetch_similar(test_sample)
print(f"Query label: {test_label}")
print(f"Top 5 candidate labels: {sim_labels}")

def plot_images(images, labels):
    if not isinstance(labels, list):
        labels = labels.tolist()

    plt.figure(figsize=(20, 10))
    columns = 6
    for (i, image) in enumerate(images):
        label_id = int(labels[i])
        ax = plt.subplot(len(images) / columns + 1, columns, i + 1)
        if i == 0:
            ax.set_title("Query Image\n" + "Label: {}".format(id2label[label_id]))
        else:
            ax.set_title(
                "Similar Image # " + str(i) + "\nLabel: {}".format(id2label[label_id])
            )
        plt.imshow(np.array(image).astype("int"))
        plt.axis("off")


images = []
labels = []

for id, label in zip(sim_ids, sim_labels):
    images.append(candidate_subset_emb[id]["image"])
    labels.append(candidate_subset_emb[id]["labels"])

images.insert(0, test_sample)
labels.insert(0, test_label)
plot_images(images, labels)


### LSH
# Random projection and locality-sensitive hashing (LSH)
# using Jaccard index to quantify the similarity between the query image and the candidate images. As per Scikit Learn's documentation:

# it is defined as the size of the intersection divided by the size of the union of two label sets.

# https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html


from typing import Union, List
from PIL import Image
import datasets

hash_size = 8
np.random.seed(seed)


# Define random vectors to project with.
random_vectors = np.random.randn(hash_size, hidden_dim).T

device = "cuda" if torch.cuda.is_available() else "cpu"


def hash_func(embedding, random_vectors=random_vectors):
    """Randomly projects the embeddings and then computes bit-wise hashes."""
    if not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)
    if len(embedding.shape) < 2:
        embedding = np.expand_dims(embedding, 0)

    # Random projection.
    bools = np.dot(embedding, random_vectors) > 0
    return [bool2int(bool_vec) for bool_vec in bools]


def bool2int(x):
    y = 0
    for i, j in enumerate(x):
        if j:
            y += 1 << i
    return 

def compute_hash(model: Union[torch.nn.Module, str]):
    """Computes hash on a given dataset."""
    device = model.device

    def pp(example_batch):
        # Prepare the input images for the model.
        image_batch = example_batch["image"]
        image_batch_transformed = torch.stack(
            [transformation_chain(image) for image in image_batch]
        )
        new_batch = {"pixel_values": image_batch_transformed.to(device)}

        # Compute embeddings and pool them i.e., take the representations from the [CLS]
        # token.
        with torch.no_grad():
            embeddings = model(**new_batch).last_hidden_state[:, 0].cpu().numpy()

        # Compute hashes for the batch of images.
        hashes = [hash_func(embeddings[i]) for i in range(len(embeddings))]
        example_batch["hashes"] = hashes
        return example_batch

    return pp

class Table:
    def __init__(self, hash_size: int):
        self.table = {}
        self.hash_size = hash_size

    def add(self, id: int, hashes: List[int], label: int):
        # Create a unique indentifier.
        entry = {"id_label": str(id) + "_" + str(label)}

        # Add the hash values to the current table.
        for h in hashes:
            if h in self.table:
                self.table[h].append(entry)
            else:
                self.table[h] = [entry]

    def query(self, hashes: List[int]):
        results = []

        # Loop over the query hashes and determine if they exist in
        # the current table.
        for h in hashes:
            if h in self.table:
                results.extend(self.table[h])
        return results

class BuildLSHTable:
    def __init__(
        self,
        model: Union[torch.nn.Module, None],
        batch_size: int = 48,
        hash_size: int = hash_size,
        dim: int = hidden_dim,
        num_tables: int = 10,
    ):
        self.hash_size = hash_size
        self.dim = dim
        self.num_tables = num_tables
        self.lsh = LSH(self.hash_size, self.num_tables)

        self.batch_size = batch_size
        self.hash_fn = compute_hash(model.to(device))

    def build(self, ds: datasets.DatasetDict):
        dataset_hashed = ds.map(self.hash_fn, batched=True, batch_size=self.batch_size)

        for id in tqdm(range(len(dataset_hashed))):
            hash, label = dataset_hashed[id]["hashes"], dataset_hashed[id]["labels"]
            self.lsh.add(id, hash, label)

    def query(self, image, verbose=True):
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")

        # Compute the hashes of the query image and fetch the results.
        example_batch = dict(image=[image])
        hashes = self.hash_fn(example_batch)["hashes"][0]

        results = self.lsh.query(hashes)
        if verbose:
            print("Matches:", len(results))

        # Calculate Jaccard index to quantify the similarity.
        counts = {}
        for r in results:
            if r["id_label"] in counts:
                counts[r["id_label"]] += 1
            else:
                counts[r["id_label"]] = 1
        for k in counts:
            counts[k] = float(counts[k]) / self.dim
        return counts

lsh_builder = BuildLSHTable(model)
lsh_builder.build(dataset["train"].shuffle(seed=seed))

idx = 0
for hash, entry in lsh_builder.lsh.tables[0].table.items():
    if idx == 5:
        break
    if len(entry) < 5:
        print(f"Hash: {hash}, entries: {entry}")
        idx += 1
candidate_dataset = dataset["train"].shuffle(seed=seed)


def visualize_lsh(lsh_class: BuildLSHTable, top_k: int = 5):
    idx = np.random.choice(len(dataset["test"]))

    image = dataset["test"][idx]["image"]
    label = dataset["test"][idx]["labels"]
    results = lsh_class.query(image)

    candidates = []
    labels = []
    overlaps = []

    for idx, r in enumerate(sorted(results, key=results.get, reverse=True)):
        if idx == top_k:
            break
        image_id, label = r.split("_")[0], r.split("_")[1]
        candidates.append(candidate_dataset[int(image_id)]["image"])
        labels.append(label)
        overlaps.append(results[r])

    candidates.insert(0, image)
    labels.insert(0, label)

    plot_images(candidates, labels)

for _ in range(5):
    visualize_lsh(lsh_builder)

import pickle

with open("lsh.pickle", "wb") as handle:
    pickle.dump(lsh_builder.lsh, handle, protocol=pickle.HIGHEST_PROTOCOL)
After this, we can use it like so:

with open("lsh.pickle", "wb") as handle:
    lsh_cls = pickle.load(handle)

lsh_builder = BuildLSHTable(model)
lsh_builder.lsh = lsh_cls
