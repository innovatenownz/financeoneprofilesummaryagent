"""
FAISS vectorstore creation and management for RAG.
Creates temporary vectorstores for record context.
"""
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document


def create_vectorstore(texts: List[str], metadata: Optional[List[dict]] = None) -> FAISS:
    """
    Creates a FAISS vectorstore from text chunks.
    
    Args:
        texts: List of text strings to vectorize
        metadata: Optional list of metadata dictionaries for each text
    
    Returns:
        FAISS vectorstore instance
    """
    # Use HuggingFace embeddings (lightweight, no API key needed)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Create documents with metadata if provided
    if metadata:
        documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadata)
        ]
    else:
        documents = [Document(page_content=text) for text in texts]
    
    # Create and return FAISS vectorstore
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore


def add_documents_to_vectorstore(
    vectorstore: FAISS,
    texts: List[str],
    metadata: Optional[List[dict]] = None
) -> FAISS:
    """
    Adds new documents to an existing vectorstore.
    
    Args:
        vectorstore: Existing FAISS vectorstore
        texts: List of text strings to add
        metadata: Optional list of metadata dictionaries
    
    Returns:
        Updated FAISS vectorstore
    """
    if metadata:
        documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadata)
        ]
    else:
        documents = [Document(page_content=text) for text in texts]
    
    vectorstore.add_documents(documents)
    return vectorstore
