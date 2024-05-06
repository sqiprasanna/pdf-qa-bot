# import weaviate
# import docx2txt
# import os
# import glob
# import time
# from io import StringIO
# import PyPDF2

# openapi_key = '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'

# client = weaviate.Client(
#     url="https://pdfqabot-47o5gind.weaviate.network",
#     # auth_client_secret=weaviate.AuthApiKey(api_key="84uDEuxvWPgyTuhWp8bolbTPimhh77jJTMi2"),
#     additional_headers={"X-OpenAI-Api-Key": openapi_key}
#     )



# def split_pdf_text_by_page(pdf_path):
#     pages=[]
#     with open(pdf_path, 'rb') as file:
#         pdf_reader = PyPDF2.PdfReader(file)
        
#         for page_num in range(len(pdf_reader.pages)):
#             page = pdf_reader.pages[page_num]
#             text = page.extract_text()
            
#             pages.append(text)
#     return pages

# def load_documents(directory, glob_patterns):
#     documents = []
#     for glob_pattern in glob_patterns:
#         file_paths = glob.glob(os.path.join(directory, glob_pattern))
#         for fp in file_paths:
#             try:
#                 if fp.endswith('.docx'):
#                     text = docx2txt.process(fp)
#                     pages = [text]  # Treat the whole document as a single "page"
#                 elif fp.endswith('.pdf'):
#                     pages = split_pdf_text_by_page(fp)
#                 else:
#                     print(f"Warning: Unsupported file format for {fp}")
#                     continue
#                 documents.extend([(page, os.path.basename(fp), i+1) for i, page in enumerate(pages)])
#             except Exception as e:
#                 print(f"Warning: The file {fp} could not be processed. Error: {e}")
#     return documents


# def split_text(text, file_name, chunk_size, chunk_overlap):
#     start = 0
#     end = chunk_size
#     while start < len(text):
#         yield (text[start:end], file_name)
#         start += (chunk_size - chunk_overlap)
#         end = start + chunk_size

# def split_documents(documents, chunk_size, chunk_overlap):
#     texts = []
#     metadata = []
#     for doc_text, file_name, page_number in documents:
#         for chunk in split_text(doc_text, file_name, chunk_size, chunk_overlap):
#             sentence = chunk[0]
#             texts.append(sentence)
#             metadata.append(str(file_name) + " Pg: " + str(page_number))

#     return texts, metadata




# print("---STARTED----\n\n")
# class_name = "resume"


# glob_patterns = ["*.docx", "*.pdf"]
# documents = load_documents(directory, glob_patterns)

# chunk_size = 400
# chunk_overlap = 0
# texts, metadata = split_documents(documents, chunk_size, chunk_overlap)

# print("-----------------------------")
# data_objs = [{"text": tx, "metadata": met}  for tx,met in zip(texts, metadata)]
# print(len(data_objs))


# i = 0

# class_obj = {
#     "class": class_name,

#     "properties": [
#         {
#             "name": "text",
#             "dataType": ["text"],
#         },
#         {
#             "name": "metadata",
#             "dataType": ["text"],
#         },
#     ],

#     "vectorizer": "text2vec-openai",

#     "moduleConfig": {
#         "text2vec-openai": {
#             "vectorizeClassName": False,
#             "model": "ada",
#             "modelVersion": "002",
#             "type": "text"
#         },
            
#     },
# }

# print("--------*--------**")

# client.batch.configure(batch_size=100)
# with client.batch as batch:
#     for data_obj in data_objs:
#         i+= 1
#         if i>-1:
#             print("--",i)
#             batch.add_data_object(data_obj, class_name)
#         else:
#             print(i)

# res = client.query.get(
#     class_name,
#     ["text", "metadata"])\
#     .with_near_text({"concepts": "Data Scientist"})\
#     .with_limit(10)\
#     .with_additional(["distance"])\
#     .do()

# print(res)

# from weaviate.classes.query import MetadataQuery
# print(weaviate.__version__)

# res = client.collections.get(class_name)
# response = res.query.near_text(
#     query="Data Scientist",
#     distance=0.18, # max accepted distance
#     return_metadata=MetadataQuery(distance=True)
# )

# for o in response.objects:
#     print(o.properties)
#     print(o.metadata.distance)




import weaviate
import docx2txt
import os
import glob
from weaviate import Client
import PyPDF2

# Initialize the client
client = Client("https://pdfqabot-47o5gind.weaviate.network")

def split_pdf_text_by_page(pdf_path):
    pages = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text() if page.extract_text() else ""
            pages.append(text)
    return pages

def load_documents(directory, glob_patterns):
    documents = []
    for pattern in glob_patterns:
        for path in glob.glob(os.path.join(directory, pattern)):
            try:
                if path.endswith('.docx'):
                    text = docx2txt.process(path)
                    documents.extend([(text, os.path.basename(path), 1)])  # Single page docx
                elif path.endswith('.pdf'):
                    pages = split_pdf_text_by_page(path)
                    documents.extend([(page, os.path.basename(path), i+1) for i, page in enumerate(pages)])
            except Exception as e:
                print(f"Warning: The file {path} could not be processed. Error: {e}")
    return documents

def index_documents(documents, class_name):
    client.batch.configure(batch_size=100)
    with client.batch as batch:
        for text, filename, page in documents:
            batch.add_data_object({
                "text": text,
                "metadata": f"{filename} Pg: {page}"
            }, class_name)
    # batch.create_objects()

def setup_weaviate_schema(class_name):
    schema = {
        "class": class_name,
        "properties": [
            {"name": "text", "dataType": ["string"], "indexInverted": True},
            {"name": "metadata", "dataType": ["string"]}
        ]
    }
    client.schema.delete_class(class_name)  # Clean slate
    client.schema.create_class(schema)

def query_documents(class_name, query):
    result = client.query.get(class_name, ["text", "metadata"])\
        .with_near_text({"concepts": [query]})\
        .with_limit(10)\
        .do()
    return result

if __name__ == "__main__":
    directory = r"C:\Users\sai19\Desktop\others\244-AKG\RAG_QA_bot\uploads"
    class_name = "Document"
    glob_patterns = ["*.docx", "*.pdf"]

    setup_weaviate_schema(class_name)
    documents = load_documents(directory, glob_patterns)
    index_documents(documents, class_name)
    
    # Query documents
    query_result = query_documents(class_name, "Data Scientist")
    print(query_result)

