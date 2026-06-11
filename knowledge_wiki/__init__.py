"""
StartupPilot AI — Knowledge Wiki

A structured knowledge compilation layer that transforms raw documents
and agent outputs into navigable Topic Pages, Entity Pages, and Indexes.

Replaces raw chunk retrieval with intelligent, agent-navigable knowledge.

Interview talking point:
    "Instead of raw RAG chunks, I built a Knowledge Compiler Agent that
     pre-processes documents into a structured wiki. Entities and topics
     get their own pages with cross-references. Agents navigate the wiki
     to assemble exactly the context they need — like an internal
     Wikipedia for the analysis."
"""

from knowledge_wiki.models import (
    TopicPage,
    EntityPage,
    WikiIndex,
    KnowledgeWiki,
)
from knowledge_wiki.compiler import KnowledgeCompiler
from knowledge_wiki.navigator import WikiNavigator
from knowledge_wiki.context_assembler import ContextAssembler

__all__ = [
    "TopicPage",
    "EntityPage",
    "WikiIndex",
    "KnowledgeWiki",
    "KnowledgeCompiler",
    "WikiNavigator",
    "ContextAssembler",
]
