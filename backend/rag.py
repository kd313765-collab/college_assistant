import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config


class SyllabusRAG:
    """Chhota sa RAG. Syllabus ki txt files ko chunks mein todta hai aur TF-IDF se dhundta hai.
    Baad mein chaho to isko embeddings (sentence-transformers) se badal sakte ho."""

    def __init__(self, folder):
        self.chunks = []
        self.vec = None
        self.matrix = None
        self.load(folder)

    def load(self, folder):
        if not os.path.isdir(folder):
            return
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".txt"):
                continue
            with open(os.path.join(folder, fname), encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            if not lines:
                continue
            header = lines[0]          # SUBJECT: ... wali line
            for line in lines[1:]:
                self.chunks.append(header + " | " + line)
        if self.chunks:
            self.vec = TfidfVectorizer(stop_words="english")
            self.matrix = self.vec.fit_transform(self.chunks)

    def search(self, query, k=3):
        if not self.chunks:
            return []
        q = self.vec.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        best = scores.argsort()[::-1][:k]
        return [self.chunks[i] for i in best if scores[i] > 0]


_rag = None


def get_rag():
    global _rag
    if _rag is None:
        _rag = SyllabusRAG(config.SYLLABUS_DIR)
    return _rag
