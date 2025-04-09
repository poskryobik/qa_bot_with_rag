from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import os




class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBED_MODEL"),
            # model_name="deepvk/USER-bge-m3",
            model_kwargs={"device": "cpu"}
        )
        self.db_path = "vector_store/faiss_db"
        # self.db_path = "../vector_store/faiss_db"
        self._init_vector_store()

    def _init_vector_store(self):
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.db = FAISS.load_local(
                self.db_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            from langchain.docstore.in_memory import InMemoryDocstore
            import faiss

            len_embedd = len(self.embeddings.embed_query("Just query"))
            index = faiss.IndexFlatIP(len_embedd)
            self.db = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore= InMemoryDocstore(),
                index_to_docstore_id={}
)


    def get_merge_retrieved_docs(self, retrieved_docs):
        seen = set()
        merged = []
        for sublist in retrieved_docs:
            for item in sublist:
                item_id = item.id
                if item_id not in seen:
                    seen.add(item_id)
                    merged.append(item)
        return merged

    def search(self, query: str, k: int):
        return self.db.similarity_search(query, k=k)
    
    def batch_search(self, querys: list, k: int):
        retriever = self.db.as_retriever(
        search_type="similarity",
        score_threshold=None,)
        retriever.search_kwargs = {"k": k}
        retrieved_docs = retriever.batch(querys)
        merged_docs = self.get_merge_retrieved_docs(retrieved_docs)  
        return merged_docs

    def add_documents(self, file_paths: list):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            add_start_index=True,
            strip_whitespace=True,
            separators=["Статья", "\n\n\n", "\n\n\n\n"],
        )

        docs = []
        for path in file_paths:
            loader = UnstructuredWordDocumentLoader(path)
            documents = loader.load()
            docs.extend(text_splitter.split_documents(documents))
        
        self.db.add_documents(docs)
        self.db.save_local(self.db_path)
        return len(docs)

    def count(self):
        return self.db.index.ntotal