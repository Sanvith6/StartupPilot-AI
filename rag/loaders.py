"""
StartupPilot AI — Document Loaders

Loads and chunks PDF, DOCX, and TXT documents for the RAG pipeline.
Uses LangChain document loaders and text splitters.

LangChain components: PyPDFLoader, Docx2txtLoader, TextLoader,
                      RecursiveCharacterTextSplitter
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings

logger = logging.getLogger(__name__)

# Supported file extensions and their loaders
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_document(file_path: str | Path) -> list[Document]:
    """Load a document from file and return a list of LangChain Documents.

    Supports PDF, DOCX, TXT, and MD files.

    Args:
        file_path: Path to the document file.

    Returns:
        List of Document objects with content and metadata.

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {SUPPORTED_EXTENSIONS}"
        )

    logger.info("Loading document: %s (%s)", path.name, ext)

    try:
        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader

            loader = PyPDFLoader(str(path))
            docs = loader.load()

        elif ext == ".docx":
            from langchain_community.document_loaders import Docx2txtLoader

            loader = Docx2txtLoader(str(path))
            docs = loader.load()

        elif ext in (".txt", ".md"):
            from langchain_community.document_loaders import TextLoader

            loader = TextLoader(str(path), encoding="utf-8")
            docs = loader.load()

        else:
            raise ValueError(f"No loader for extension: {ext}")

        # Add metadata
        for doc in docs:
            doc.metadata["source_file"] = path.name
            doc.metadata["file_type"] = ext

        logger.info("Loaded %d pages/sections from %s", len(docs), path.name)
        return docs

    except Exception as e:
        logger.error("Failed to load document %s: %s", path.name, e)
        raise


def chunk_documents(
    documents: list[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[Document]:
    """Split documents into chunks for embedding.

    Uses RecursiveCharacterTextSplitter which intelligently splits on
    paragraph, sentence, and word boundaries.

    Args:
        documents: List of Document objects to split.
        chunk_size: Max characters per chunk (default from config).
        chunk_overlap: Overlap between chunks (default from config).

    Returns:
        List of chunked Document objects.
    """
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    # Add chunk index metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)

    logger.info(
        "Split %d documents into %d chunks (size=%d, overlap=%d)",
        len(documents),
        len(chunks),
        size,
        overlap,
    )

    return chunks


def load_and_chunk(
    file_path: str | Path,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[Document]:
    """Convenience function: load a document and chunk it in one step.

    Args:
        file_path: Path to the document.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        List of chunked Document objects ready for embedding.
    """
    docs = load_document(file_path)
    return chunk_documents(docs, chunk_size, chunk_overlap)
