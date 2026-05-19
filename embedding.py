from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_DIR = "knowledge/.chroma"
COLLECTION_NAME = "big_data_knowledge"


class KnowledgeIndex:
    """Manages Chroma vector index for semantic search over knowledge files."""

    def __init__(self, knowledge_dir: str = "knowledge") -> None:
        self.root = Path(knowledge_dir)
        self.chroma_path = self.root / ".chroma"
        self._model: SentenceTransformer | None = None
        self._client: chromadb.PersistentClient | None = None
        self._collection: chromadb.Collection | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    @property
    def client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(self.chroma_path))
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_markdown(self, text: str, source_file: str) -> list[dict]:
        """Split markdown by ## headings into chunks."""
        chunks: list[dict] = []
        sections = text.split("\n## ")
        title = sections[0].split("\n")[0].lstrip("# ").strip()

        for i, section in enumerate(sections):
            lines = section.strip().split("\n", 1)
            heading = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            if len(body) < 80:
                continue

            chunk_id = hashlib.md5(
                f"{source_file}:{i}".encode()
            ).hexdigest()[:12]

            chunks.append({
                "id": chunk_id,
                "text": f"# {title}\n## {heading}\n{body[:2000]}",
                "source": source_file,
                "heading": heading,
            })

        return chunks

    # ------------------------------------------------------------------
    # Build / Rebuild index
    # ------------------------------------------------------------------

    def _compute_hash(self, filepath: Path) -> str:
        return hashlib.md5(filepath.read_bytes()).hexdigest()

    def build(self, force: bool = False) -> int:
        """Build Chroma index from all knowledge markdown files. Returns chunk count."""
        md_files = sorted(self.root.glob("components/**/*.md")) + \
                   sorted(self.root.glob("projects/**/*.md")) + \
                   sorted(self.root.glob("roadmap/**/*.md")) + \
                   sorted(self.root.glob("interview/**/*.md")) + \
                   sorted(self.root.glob("cases/**/*.md"))

        try:
            existing = self.collection.count()
        except Exception:
            existing = 0

        if existing > 0 and not force:
            return existing

        # Clear and rebuild
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None

        all_chunks: list[dict] = []
        for path in md_files:
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if len(text.strip()) < 50:
                continue
            rel_path = str(path.relative_to(self.root))
            all_chunks.extend(self._chunk_markdown(text, rel_path))

        if not all_chunks:
            return 0

        texts = [c["text"] for c in all_chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False).tolist()

        self.collection.add(
            ids=[c["id"] for c in all_chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"source": c["source"], "heading": c["heading"]}
                       for c in all_chunks],
        )

        return len(all_chunks)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 3) -> list[dict]:
        """Semantic search. Returns list of {source, heading, content, score}."""
        if self.collection.count() == 0:
            return []

        query_embedding = self.model.encode([query], show_progress_bar=False).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(limit, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        output: list[dict] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) else {}
            output.append({
                "source": meta.get("source", "unknown"),
                "heading": meta.get("heading", ""),
                "content": docs[i][:1500] if i < len(docs) else "",
                "score": round(1 - min(distances[i] if i < len(distances) else 0, 1), 3),
            })

        return output
