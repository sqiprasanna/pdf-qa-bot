# PDF Question-Answering Chat Application

This repository contains a PDF Question-Answering chat application that extracts information from uploaded PDF files and answers user queries based on the document content. It uses LlamaIndex, ChromaDB, and OpenAI's GPT-4 to provide accurate answers to questions related to the uploaded documents.

## Features

- **PDF Upload**: Allows users to upload PDF files via a web interface.
- **Information Extraction**: Extracts text from uploaded PDF files using the PyMuPDF library.
- **Document Indexing**: Indexes document contents using LlamaIndex and ChromaDB.
- **Query Response**: Answers user queries with relevant information from the indexed documents using OpenAI's GPT-4 model.
- **Custom Function**: Uses OpenAI function calling to return custom-formatted responses.
- **Evaluation Metrics**: Calculates BLEU and ROUGE scores for generated vs. actual responses.

## Prerequisites

- Python 3.8 or higher
- OpenAI GPT-4 API Key

## Installation

1. **Clone the Repository**:
    ```bash
    git clone <repository-url>
    ```
    Replace `<repository-url>` with your repository URL.

2. **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/MacOS
    venv\Scripts\activate  # On Windows
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    The `requirements.txt` should include:
    - `Flask`
    - `PyMuPDF`
    - `openai`
    - `llama-index`
    - `chromadb`
    - `nltk`
    - `rouge-score`

## Configuration

- **OpenAI API Key**:
  Set up your OpenAI API key in the application by replacing `<your-openai-api-key>` with your actual API key in the script.

- **Database Configuration**:
  ChromaDB storage is used to keep document embeddings persistently. Ensure that the `db_path` is writable and secure.

## Usage

1. **Start the Flask Server**:
    ```bash
    python app.py
    ```

2. **Access the Web App**:
   Open a web browser and navigate to `http://127.0.0.1:5000`.

3. **Upload a PDF**:
   Use the "Upload" feature to upload your desired PDF file. The application will automatically index its content.

4. **Query the Document**:
   After uploading, enter a question in the query box, and the application will fetch the relevant information.

5. **Evaluate with BLEU/ROUGE**:
   You can also calculate BLEU and ROUGE scores to evaluate the quality of generated responses against actual responses.

## Project Structure

- `app.py`: The main server script that contains all Flask endpoints.
- `templates/`: Contains HTML files for rendering the frontend.
- `static/`: Includes static files like CSS and JavaScript for the UI.
- `uploads/`: Stores temporarily uploaded PDF files.
- `chromadb_storage/`: Stores ChromaDB data.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contribution

Feel free to contribute to this project by opening issues or submitting pull requests. Your feedback and suggestions are always welcome!

## References

- [OpenAI GPT-4 API](https://platform.openai.com/docs/models/gpt-4)
- [LlamaIndex](https://llamaindex.ai/)
- [ChromaDB](https://docs.trychroma.com/)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

