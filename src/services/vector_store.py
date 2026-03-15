"""ChromaDB vector store service for RAG."""

import json
import time
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.config import settings
from src.utils.logger import get_logger
from src.utils.observability import vector_search_duration

logger = get_logger(__name__)


class VectorStoreService:
    """Manages ChromaDB vector store for Q&A retrieval."""

    def __init__(self):
        """Initialize ChromaDB client and embedding model."""
        self.embedding_model = None
        self.vector_store = None
        self.collection_name = settings.collection_name
        self.db_path = settings.chroma_db_path
        self.initialized = False

        logger.info(
            "vector_store_service_created",
            collection=self.collection_name,
            db_path=self.db_path,
        )

    def initialize(self) -> None:
        """Initialize vector store with Q&A dataset."""
        try:
            # Create embedding model
            logger.info("loading_embedding_model", model=settings.embedding_model)
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            # Load Q&A dataset
            qa_data = self._load_qa_dataset()
            logger.info("qa_dataset_loaded", num_questions=len(qa_data))

            # Convert to LangChain documents
            documents = self._create_documents(qa_data)

            # Create or load vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.db_path,
            )

            # Check if collection is empty
            collection_count = len(self.vector_store.get()["ids"])
            
            if collection_count == 0:
                logger.info("initializing_empty_collection")
                self.vector_store.add_documents(documents)
                logger.info("documents_added", count=len(documents))
            else:
                logger.info("collection_already_initialized", count=collection_count)

            self.initialized = True
            logger.info("vector_store_initialized_successfully")

        except Exception as e:
            logger.error("vector_store_initialization_error", error=str(e), exc_info=True)
            raise

    def reload(self) -> None:
        """Reload vector store with updated Q&A dataset."""
        try:
            logger.info("reloading_vector_store")

            # Load fresh Q&A data
            qa_data = self._load_qa_dataset()
            documents = self._create_documents(qa_data)

            # Delete existing collection
            if self.vector_store:
                self.vector_store.delete_collection()
                logger.info("old_collection_deleted")

            # Recreate vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.db_path,
            )

            # Add documents
            self.vector_store.add_documents(documents)
            logger.info("vector_store_reloaded", num_docs=len(documents))

        except Exception as e:
            logger.error("vector_store_reload_error", error=str(e), exc_info=True)
            raise

    def similarity_search(
        self,
        query: str,
        k: int = 3,
    ) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if not self.initialized:
            logger.error("vector_store_not_initialized")
            return []

        try:
            start_time = time.time()
            
            results = self.vector_store.similarity_search(query, k=k)
            
            duration = time.time() - start_time
            vector_search_duration.observe(duration)

            logger.info(
                "similarity_search_completed",
                query=query[:100],
                num_results=len(results),
                duration_seconds=round(duration, 3),
            )

            return results

        except Exception as e:
            logger.error("similarity_search_error", error=str(e), exc_info=True)
            return []

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 3,
    ) -> List[tuple]:
        """Search for similar documents with similarity scores.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of tuples (document, score) where score is distance (lower is better)
        """
        if not self.initialized:
            logger.error("vector_store_not_initialized")
            return []

        try:
            start_time = time.time()
            
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            duration = time.time() - start_time
            vector_search_duration.observe(duration)

            logger.info(
                "similarity_search_with_score_completed",
                query=query[:100],
                num_results=len(results),
                duration_seconds=round(duration, 3),
                top_score=round(results[0][1], 3) if results else None,
            )

            return results

        except Exception as e:
            logger.error("similarity_search_with_score_error", error=str(e), exc_info=True)
            return []

    def get_document_count(self) -> int:
        """Get number of documents in vector store.
        
        Returns:
            Document count
        """
        if not self.initialized or not self.vector_store:
            return 0

        try:
            return len(self.vector_store.get()["ids"])
        except Exception as e:
            logger.error("get_document_count_error", error=str(e))
            return 0

    def _load_qa_dataset(self) -> List[dict]:
        """Load Q&A dataset from JSON file.
        
        Returns:
            List of Q&A dictionaries
        """
        dataset_path = Path(settings.qa_dataset_path)

        if not dataset_path.exists():
            logger.error("qa_dataset_not_found", path=str(dataset_path))
            raise FileNotFoundError(f"Q&A dataset not found at {dataset_path}")

        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("questions", [])

    def _create_documents(self, qa_data: List[dict]) -> List[Document]:
        """Convert Q&A data to LangChain documents.
        
        Args:
            qa_data: List of Q&A dictionaries
            
        Returns:
            List of LangChain documents
        """
        documents = []

        for qa in qa_data:
            # Create document with Q&A format
            content = f"Question: {qa['question']}\n\nAnswer: {qa['answer']}"

            doc = Document(
                page_content=content,
                metadata={
                    "source": "qa_dataset",
                    "question": qa["question"],
                    "answer": qa["answer"],
                },
            )

            documents.append(doc)

        return documents


# Global instance (will be initialized in main.py)
vector_store_service = VectorStoreService()
