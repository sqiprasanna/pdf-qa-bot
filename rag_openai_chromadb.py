from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import fitz  # PyMuPDF
import openai
import os
import json

app = Flask(__name__)
app.secret_key = 'super secret key'  # Needed to keep the session during requests

key = 'sk-proj-wMXQIZ3sI4q6fK26U9eBT3BlbkFJKJlTm1XnnVu7v18wGj4R'
# Configure OpenAI API key
openai.api_key = key
lm_client = openai.OpenAI(api_key=key)

# Placeholder for ChromaDB client setup
class ChromaDBClient:
    def __init__(self):
        self.documents = {}

    def index_document(self, text):
        # Simulating document indexing
        doc_id = len(self.documents) + 1
        self.documents[doc_id] = text
        return doc_id

    def search_documents(self, query):
        # Simple full-text search simulation
        return [text for text in self.documents.values() if query.lower() in text.lower()]

chroma_db_client = ChromaDBClient()

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = os.path.join('uploads', file.filename)
        file.save(filename)
        extracted_texts = extract_text_from_pdf(filename)
        print(extracted_texts)
        doc_ids = [chroma_db_client.index_document(text) for text in extracted_texts]
        print(doc_ids)
        session['doc_ids'] = doc_ids  # Store document IDs in session
        return jsonify({"status": "File processed", "doc_ids": doc_ids})
    return jsonify({"status": "Failed", "message": "Invalid file or upload failed"})


custom_function_1 = [
    {
        "name": "return_response",
        "description": "Function to be used to return the response to the question, and a boolean value indicating if the information given was sufficient to generate the entire answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "This should be the answer that was generated from the context, given the question",
                },
                "sufficient": {
                    "type": "boolean",
                    "description": "This should represent wether the information present in the context was sufficent to answer the question. Return True is it was, else False.",
                },
            },
            "required": ["response", "sufficient"],
        },
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    query = request.form['query']
    if 'doc_ids' in session:
        texts = [chroma_db_client.documents[doc_id] for doc_id in session['doc_ids']]
        concatenated_texts = ' '.join(texts)  # Combine all texts for simplicity
        print(concatenated_texts)
        if concatenated_texts is None:
            return "No relevant information found in the database."

        # Prepare the message to be sent to the GPT model
        system_message = "You are provided with a paragraph from a document based on your query. Use the information to answer the query effectively."
        user_message = f"Query: {query}\nContext: {concatenated_texts}\nAnswer:"
        print("--------------------- USER MESSAGE AND RETREIVED CONTEXT:- \n ------------------",user_message)
        # Compose the message structure for the OpenAI API
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]
        response = lm_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=250,
            temperature=0.5,
            functions=custom_function_1, 
            function_call='auto'
        )
        print(response)
        reply = response.choices[0].message.content
        sufficient = False
        if reply is None:
            reply = json.loads(response.choices[0].message.function_call.arguments)[
                "response"
            ]
            sufficient = json.loads(response.choices[0].message.function_call.arguments)[
                "sufficient"
            ]

        return jsonify({"response": reply})
    return jsonify({"response": "No documents loaded to respond to queries."})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text_contents = [page.get_text() for page in document]
    document.close()
    return text_contents

if __name__ == '__main__':
    app.run(debug=True)
