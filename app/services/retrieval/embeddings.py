"""Embeddings. Backend `hashing` = CPU, déterministe, NON sémantique : sert à tester la plomberie.
Les métriques de qualité de recherche doivent être mesurées avec un vrai modèle (BGE-M3, profil gpu-demo)."""
import hashlib
import math
import re
import unicodedata
from typing import Protocol

DIM = 768


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    name = "hashing-v1"
    dim = DIM

    def _features(self, text: str) -> list[str]:
        t = normalize(text)
        words = re.findall(r"[a-z0-9]+", t)
        feats = [f"w:{w}" for w in words] + [f"b:{a}_{b}" for a, b in zip(words, words[1:])]
        for w in words:
            padded = f"#{w}#"
            feats += [f"c:{padded[i:i + 4]}" for i in range(max(1, len(padded) - 3))]
        return feats

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            v = [0.0] * self.dim
            for f in self._features(text):
                h = int(hashlib.md5(f.encode()).hexdigest(), 16)
                v[h % self.dim] += 1.0 if (h >> 64) % 2 == 0 else -1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


class BgeM3Embedder:
    """BGE-M3 (BAAI/bge-m3, dense, 1024 dim) via sentence-transformers. À exécuter sur GPU (Colab) ;
    fonctionne aussi sur CPU mais lentement. Les vecteurs sont normalisés (cosinus)."""
    name = "bge-m3"
    dim = 1024

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str | None = None, batch_size: int = 32):
        from sentence_transformers import SentenceTransformer  # import tardif : dépendance optionnelle (extra `gpu`)
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device=device)
        self.model.max_seq_length = 512
        if str(self.model.device).startswith("cuda"):
            self.model.half()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True)
        return [v.astype("float32").tolist() for v in vecs]


def get_embedder(name: str = "hashing") -> Embedder:
    if name == "hashing":
        return HashingEmbedder()
    if name == "bge-m3":
        return BgeM3Embedder()
    raise NotImplementedError(f"Backend d'embeddings '{name}' non disponible dans cet environnement (voir technical_decisions.md D2)")
