import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from dotenv import load_dotenv
load_dotenv()

# os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

# Langsmith Tracking
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "RAG Document Q&A with OPENAI, GROQ"

# Load the groq API key
groq_api_key = os.getenv('GROQ_API_KEY')

llm = ChatGroq(model="llama3-8b-8192", groq_api_key= groq_api_key)

prompt = ChatPromptTemplate.from_template(
    """
    Answer the question based on the provided context only.
    Please provide the most accurate response based on the question.
    <context>
    {context}
    <context>
    Question:{input}
    """
)


def create_vectors_embeddings(api_key):
    if "vectors" not in st.session_state:
        # st.session_state.embeddings = OllamaEmbeddings()
        st.session_state.embeddings = OpenAIEmbeddings(api_key=api_key)
        st.session_state.loader = PyPDFDirectoryLoader("research_papers")
        st.session_state.docs = st.session_state.loader.load()
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs[:50]) # top 50 docs
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)


st.title("RAG Document Q&A with GROQ and Lama3")

# Sidebar for settings
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Enter your Open AI API key:", type="password")

user_prompt = st.text_input("Enter your query from the research paper...")

if st.button("Document Embeddings"):
    create_vectors_embeddings(api_key)
    st.write("Vector Database is ready")


import time

if user_prompt:
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = st.session_state.vectors.as_retriever()
    retriever_chain = create_retrieval_chain(retriever, document_chain)
    
    start_time = time.process_time()
    response = retriever_chain.invoke({'input':user_prompt})
    print(f"Response time : {time.process_time()- start_time}")
    st.write(response['answer'])

    # With a streamlit expander
    with st.expander("Document similarity Search"):
        for i, doc in enumerate(response['context']):
            st.write(doc.page_content)
            st.write('------------------------')