import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticSearch:

    def __init__(self, model_name, data_path):

        self.model = SentenceTransformer(model_name)

        self.data_path = Path(data_path)

        self.chunks = []
        self.embeddings = np.empty((0, 384))

        self.load_documents()

    def load_documents(self):

        self.chunks = []

        if not self.data_path.exists():
            return

        with open(
            self.data_path,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if line.strip():

                    self.chunks.append(
                        json.loads(line)
                    )

        if not self.chunks:
            self.embeddings = np.empty((0, 384))
            return

        texts = [
            chunk["text"]
            for chunk in self.chunks
        ]

        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def search(
        self,
        query,
        top_k=5,
        doc_type=None,
        source=None,
        min_score=0.0
    ):

        if not self.chunks:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        scores = np.dot(
            self.embeddings,
            query_embedding
        )

        results = []

        for index, score in enumerate(scores):

            chunk = self.chunks[index]

            if doc_type:
                if chunk.get("doc_type", "").lower() != doc_type.lower():
                    continue

            if source:
                if chunk.get("source", "").lower() != source.lower():
                    continue

            if float(score) < min_score:
                continue

            results.append({
                "source": chunk.get("source", "unknown"),
                "page": chunk.get("page", 0),
                "section": chunk.get("section", "Unknown"),
                "score": round(float(score), 4),
                "text": chunk["text"]
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:top_k]
    def refresh(self):
        self.load_documents()

    def get_documents(self):

        documents = {}

        for chunk in self.chunks:

            source = chunk.get("source", "unknown")

            if source not in documents:

                documents[source] = {
                    "source": source,
                    "doc_type": chunk.get("doc_type", "unknown"),
                    "chunks": 0
                }

            documents[source]["chunks"] += 1

        return list(documents.values())