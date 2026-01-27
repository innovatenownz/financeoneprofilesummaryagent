from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def build_vectorstore(text: str, account_id: str):
    """
    Build a vector store from account text.
    
    Note: With a single document, similarity_search returns the entire context.
    This function is kept for future enhancements (e.g., chunking text into multiple documents).
    """
    if not text or not text.strip():
        # Return empty document if text is missing
        print(" Warning: Empty text provided to vectorstore")
        doc = Document(
            page_content="No data available",
            metadata={"account_id": account_id}
        )
    else:
        doc = Document(
            page_content=text,
            metadata={"account_id": account_id}
        )
    return FAISS.from_documents([doc], embeddings)
