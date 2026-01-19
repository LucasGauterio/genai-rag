from rank_bm25 import BM25Okapi
import re


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class BM25Retriever:
    def __init__(self):
        self.documents = []
        self.tokenized_docs = []
        self.bm25 = None

    def add_documents(self, docs: list[dict]):
        """
        docs: [{"text": str, "metadata": dict}]
        """
        self.documents.extend(docs)
        self.tokenized_docs = [tokenize(d["text"]) for d in self.documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def search(
        self,
        query: str,
        k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        results = []
        for doc, score in zip(self.documents, scores):
            if metadata_filter:
                for key, value in metadata_filter.items():
                    if doc["metadata"].get(key) != value:
                        break
                    else:
                        results.append((doc, score))
            else:
                results.append((doc, score))

        ranked = sorted(results, key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked[:k]]
