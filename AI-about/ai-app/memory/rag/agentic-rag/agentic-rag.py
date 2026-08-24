import os
import getpass
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_core.tools import create_retriever_tool as create_lc_retriever_tool

URLS = os.getenv("URLS", "").split(",")
LOCAL_FILES = os.getenv("LOCAL_FILES", "").split(",")

def fetch_docs(from_flag: str = None) -> list:
    """Fetch documents from URLs or local files."""
    if from_flag == "urls":
        return _fetch_docs_from_urls()
    else:
        return _fetch_docs_from_local()

def _fetch_docs_from_local() -> list:
    """Fetch documents from local files."""
    docs = [TextLoader(file, encoding="utf-8").load() for file in LOCAL_FILES]
    return docs

def _fetch_docs_from_urls():
    """Fetch documents from URLs."""
    docs = [WebBaseLoader(url).load() for url in URLS]
    return docs

def split_docs(docs: list) -> list:
    """Split documents into smaller chunks."""
    docs_list = [item for sublist in docs for item in sublist]
    print(f"==== Watch split: docs_list ====")
    _watch_what_happen(docs_list)
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs_list)
    print(f"==== Watch split: chunks ====")
    _watch_what_happen(chunks)
    return chunks

def create_retriever_tool(chunks: list):
    try:
        
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        embeddings = HuggingFaceEmbeddings()

    vectorstore = InMemoryVectorStore.from_documents(
            documents=chunks, embedding=embeddings
    )
    retriever = vectorstore.as_retriever()
    retriever_tool = create_lc_retriever_tool(
        retriever,
        "retrieve_blog_posts",
        "Search and return information about Lilian Weng blog posts.",
    )
    return retriever_tool

def _watch_what_happen(list_obj: list):
    """辅助函数，用于查看列表元素"""
    print(f"==== watch_what_happen ====")
    for item in list_obj:
        print(f"this item: {item}\n")
    
def main():
    """Main function."""
    docs = fetch_docs()
    chunks = split_docs(docs)
    retriever_tool = create_retriever_tool(chunks)
    retriever_tool.invoke({"query": "types of reward hacking"})


if __name__ == "__main__":
    main()