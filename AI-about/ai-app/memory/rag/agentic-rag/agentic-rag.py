import os
import getpass
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
    doc_splits = text_splitter.split_documents(docs_list)
    print(f"==== Watch split: doc_splits ====")
    _watch_what_happen(doc_splits)

def _watch_what_happen(list_obj: list):
    """辅助函数，用于查看列表元素"""
    print(f"==== watch_what_happen ====")
    for item in list_obj:
        print(f"this item: {item}")
    
def main():
    """Main function."""
    docs = fetch_docs(from_flag="urls")
    split_docs(docs)

if __name__ == "__main__":
    main()