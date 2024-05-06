from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import weaviate
import os
from werkzeug.utils import secure_filename
import fitz  # This is the import name for PyMuPDF
import PyPDF2
from sentence_transformers import SentenceTransformer

import openai
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
app.secret_key = '12345678'  # Needed for session management
openapi_key = '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'
lm_client = openai.OpenAI(api_key=openapi_key)

client = weaviate.Client(
    url="https://pdfqabot-47o5gind.weaviate.network",
    # auth_client_secret=weaviate.AuthApiKey(api_key="84uDEuxvWPgyTuhWp8bolbTPimhh77jJTMi2"),
    additional_headers={"X-OpenAI-Api-Key": openapi_key}
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def split_pdf_text_by_page(pdf_path):
    pages = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            pages.append(text)
    return pages



# Assuming you have already initialized the 'client' object as shown before
def setup_weaviate_schema(index_name):
    schema = {
        "classes": [{
            "class": index_name,
            "description": "A class to store documents",
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The text content of the document",
                    "indexInverted": True,
                },
                # {
                #     "name": "vector",
                #     "dataType": ["number[]"],
                #     "description": "The vector representation of the document",
                # },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Additional metadata about the document"
                }
            ],
            "vectorizer": "text2vec-openai",
             "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False,
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                },
             }

        }]
    }
    # If an index with the same index name already exists within Weaviate, delete it
    if client.schema.exists(index_name):
        client.schema.delete_class(index_name)
    client.schema.delete_all()
    client.schema.create(schema)



def index_document_to_weaviate(text, metadata):
    
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # vectors = [model.encode(text) for text in text_data]

    # data_object = {
    #     "content": text,
    #     # "vector": vector.tolist(),
    #     "metadata":metadata
    # }
    # client.data_object.create(data_object, index_name)
    data_object = [{"text": tx, "metadata": met}  for tx,met in zip(text, metadata)]

    client.batch.configure(batch_size=100)
    i=0
    with client.batch as batch:
        for data_obj in data_object:
            i+= 1
            if i>-1:
                print("--",i)
                batch.add_data_object(data_obj, index_name)
            else:
                print(i)
    

@app.before_request
def initialize_weaviate_schema():
    setup_weaviate_schema(index_name)


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def search_documents(query):
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # query_vector = model.encode(query)

    try:
        # result = client.query.get(index_name, ["text", "metadata"]).with_near_vector({
        #     "vector": query_vector.tolist()
        # }).with_limit(10).do()
        result = client.query.get(index_name, ["text", "metadata"]).with_near_vector({
            "concepts": query
        }).with_limit(10).do()
        print("Query Result:", result)
        if 'Get' in result['data'] and index_name in result['data']['Get']:
            return result['data']['Get'][index_name]
        else:
            print("No data found for the query.")
            return []
    except Exception as e:
        print(f"Error querying Weaviate: {e}")
        return []


def generate_pdf_qa_response(query):
    """
    Generates a response for a PDF QA bot using the context retrieved from Weaviate
    and a GPT model from OpenAI.
    """
    # First, retrieve relevant context from Weaviate
    context = search_documents(query)
    print(context)
    if context is None:
        return "No relevant information found in the database."

    # Prepare the message to be sent to the GPT model
    system_message = "You are provided with a paragraph from a document based on your query. Use the information to answer the query effectively."
    user_message = f"Query: {query}\nContext: {context}\nAnswer:"
    print("--------------------- USER MESSAGE AND RETREIVED CONTEXT:- \n ------------------",user_message)
    # Compose the message structure for the OpenAI API
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]

    # Send the composed message to OpenAI's GPT model
    try:
        response = lm_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=250,
            temperature=0.5
        )
        # Extract the text from the response
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error while generating response from GPT: {e}")
        return "Failed to generate a response."


@app.route('/', methods=['GET', 'POST'])
def index():
    answer = None
    if request.method == 'POST':
        if 'query' in request.form and request.form['query'].strip() != '':
            query = request.form['query']
            print(query)
            answer = generate_pdf_qa_response(query)
        elif 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(file_path)
            file.save(file_path)
            text = extract_text_from_pdf(file_path)
            print(text)
            index_document_to_weaviate(text, filename)
            answer = "Document uploaded and indexed successfully."
            print(answer)
    return render_template('index.html', answer=answer)

def check_data_uploaded(index_name):
    try:
        result = client.query.get(index_name, ["text", "metadata"]).with_limit(10).do()  # Adjust limit as needed
        print(f"Data in {index_name}:", result['data']['Get'][index_name])
        return result['data']['Get'][index_name]
    except Exception as e:
        print(f"Error checking data upload: {e}")
        return []



if __name__ == '__main__':
    index_name= "pdfqa"
    # check_data_uploaded(index_name)

    app.run(debug=True)
