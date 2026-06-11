"""
StartupPilot AI — Backend Services

Contains reusable business logic for document uploads, RAG processing,
and Knowledge Wiki compilation.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from fastapi import UploadFile

from config import get_settings, ensure_directories
from rag.loaders import load_and_chunk
from rag.retrieval import get_store

logger = logging.getLogger(__name__)


def process_document_upload(
    project_id: str,
    file: UploadFile,
    startup_idea: str = "",
) -> dict:
    """Save an uploaded file, process it into the vector store, and compile wiki.

    The compilation step is the key addition — documents are immediately
    compiled into the Knowledge Wiki on upload (decision #1).

    Args:
        project_id: The project ID to associate with the document.
        file: The FastAPI UploadFile object.
        startup_idea: The startup idea for wiki context.

    Returns:
        Dict with {chunks_added, wiki_stats}.
    """
    settings = get_settings()
    ensure_directories()

    # Define destination path
    upload_path = Path(settings.upload_dir) / file.filename
    logger.info("Saving uploaded file to %s", upload_path)

    # Save the file
    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Load and chunk the document
        chunks = load_and_chunk(upload_path)
        logger.info("Created %d chunks from %s", len(chunks), file.filename)

        # Add to vector store
        vector_store = get_store()
        num_added = vector_store.add_documents(project_id, chunks)
        logger.info(
            "Successfully added %d chunks to vector store for project %s",
            num_added,
            project_id,
        )

        # ── Compile into Knowledge Wiki (immediate, on upload) ────────
        wiki_stats = {}
        if settings.wiki_auto_compile:
            try:
                from knowledge_wiki.compiler import KnowledgeCompiler

                compiler = KnowledgeCompiler()
                wiki = compiler.compile_documents(
                    project_id=project_id,
                    chunks=chunks,
                    startup_idea=startup_idea or f"Project {project_id}",
                )
                wiki_stats = wiki.get_stats()
                logger.info(
                    "Wiki compiled on upload: %d topics, %d entities",
                    len(wiki.topic_pages),
                    len(wiki.entity_pages),
                )
            except Exception as wiki_err:
                logger.warning(
                    "Wiki compilation failed (non-fatal): %s", wiki_err
                )

        return {
            "chunks_added": num_added,
            "wiki_stats": wiki_stats,
        }

    except Exception as e:
        logger.error("Failed to process uploaded file %s: %s", file.filename, e)
        # Clean up the file if it failed to process
        if upload_path.exists():
            upload_path.unlink()
        raise e
