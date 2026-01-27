from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def build_vectorstore(text: str, account_id: str):
    doc = Document(
        page_content=text,
        metadata={"account_id": account_id}
    )
    return FAISS.from_documents([doc], embeddings)
