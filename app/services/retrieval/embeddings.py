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


def get_embedder(name: str = "hashing") -> Embedder:
    if name == "hashing":
        return HashingEmbedder()
    raise NotImplementedError(f"Backend d'embeddings '{name}' non disponible dans cet environnement (voir technical_decisions.md D2)")
