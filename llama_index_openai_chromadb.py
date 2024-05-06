from flask import Flask, request, render_template, jsonify, session
import fitz  # PyMuPDF for PDF text extraction
import openai
import os
from llama_index.core import GPTVectorStoreIndex, Document, ServiceContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.storage_context import StorageContext
import chromadb
import json
import pandas as pd

import openpyxl

app = Flask(__name__)
app.secret_key = 'super secret key'

# OpenAI API Configuration
key = 'sk-proj-wMXQIZ3sI4q6fK26U9eBT3BlbkFJKJlTm1XnnVu7v18wGj4R'
openai.api_key = key

# Initialize ChromaDB client with persistent storage
db_path = "chromadb_storage"
db = chromadb.PersistentClient(path=db_path)
chroma_collection = db.get_or_create_collection("chroma_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Setup OpenAI Embedding Model
embed_model = OpenAIEmbedding(api_key=openai.api_key)
# Make a request to the GPT-4 model
lm_client = openai.OpenAI(api_key=key)
# Create Service Context without HuggingFace LLM
service_context = ServiceContext.from_defaults(
    chunk_size=1024,
    chunk_overlap=200,
    embed_model=embed_model
)

# Custom function for GPT-4
custom_function_1 = [
    {
        "name": "return_response",
        "description": "Provide a response to the question, including if the information was sufficient.",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "Answer generated from the context, given the query.",
                },
                "sufficient": {
                    "type": "boolean",
                    "description": "Indicates whether the context was sufficient to answer the query.",
                },
            },
            "required": ["response", "sufficient"],
        },
    }
]

# Initialize the LlamaIndex
index = GPTVectorStoreIndex.from_vector_store(
    vector_store=vector_store, service_context=service_context, storage_context=storage_context,
)

@app.route('/')
def index_page():
    return render_template('chat.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global index

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = os.path.join('uploads', file.filename)
        file.save(filename)

        # Extract text from the PDF
        extracted_texts = extract_text_from_pdf(filename)

        # Filter out pages with empty or null content
        non_empty_texts = [text.replace('\x00', '') for text in extracted_texts if text.strip()]

        if not non_empty_texts:
            return jsonify({"status": "Failed", "message": "No valid text found in the PDF document"})

        # Index documents with LlamaIndex
        documents = [Document(text=text) for text in non_empty_texts]
        index = GPTVectorStoreIndex.from_documents(
            documents, service_context=service_context, storage_context=storage_context
        )
        return jsonify({"status": "File processed and indexed successfully"})
    return jsonify({"status": "Failed", "message": "Invalid file or upload failed"})




# Global variable to store queries and answers during the session
session_data = {
    "query": [],
    "response": []
}

def save_session_to_excel():
    global session_data

    # Create a DataFrame from session data
    session_df = pd.DataFrame(session_data)

    # Save DataFrame to Excel file
    session_df.to_excel("session_data.xlsx", index=False)

    print("Session data saved to session_data.xlsx file.")
    
@app.route('/chat', methods=['POST'])
def chat():
    global index, session_data 

    query = request.form['query']
    if index:
        # Query the index for relevant information
        context = index.as_query_engine().query(query)
        print("Retrieved Information:- \n",context)
        if query.lower() == "end the session":
            # If user requests to end the session, save the session data to an Excel file
            save_session_to_excel()
            # Reset session data
            session_data = {"query": [], "response": []}
            return jsonify({"response": "Session ended. Session data saved to Excel file."})

        # Send the query and context to OpenAI GPT-4
        system_message = (
                "You are a knowledgeable assistant. Answer the following question clearly without using extra quotes or special characters."
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Question: {query}\nContext: {context}"}
        ]



        response = lm_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,
            temperature=0.1,
            functions=custom_function_1,
            function_call='auto'
        )

        reply = response.choices[0].message.content
        if reply is None:
            try:
                arguments = json.loads(response.choices[0].message.function_call.arguments)
                reply = arguments['response'] 
                sufficient = arguments['sufficient'] 
            except (KeyError, AttributeError, json.JSONDecodeError) as e:
                # print(response.choices[0].message.function_call["arguments"])
                print(f"Error decoding function call arguments: {e}")
                reply = "Unable to parse function call arguments."
        # Save query and response to session data
        session_data["query"].append(query)
        session_data["response"].append(reply)

        return jsonify({"response": reply})
    return jsonify({"response": "No documents loaded to respond to queries."})
# """


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text_contents = [page.get_text() for page in document]
    document.close()
    return text_contents

if __name__ == '__main__':
    app.run(debug=True)
