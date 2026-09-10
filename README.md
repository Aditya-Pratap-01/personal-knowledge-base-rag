The LLM receives only the retrieved chunks and is instructed to answer using those sources.

🛠️ Tech Stack
Technology	Purpose
Python	Core programming language
Streamlit	Web interface
ChromaDB	Vector database
Sentence Transformers	Local text embeddings
all-MiniLM-L6-v2	Embedding model
Groq	LLM inference
openai/gpt-oss-120b	LLM model
pypdf	PDF text extraction
python-dotenv	Environment variable management
📁 Project Structure
RAG Project/
│
├── app.py
├── rag.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── notes/
│
└── chroma_db/
Main files

app.py

Contains the Streamlit user interface, file upload, chat interface, Groq integration, citations, and knowledge-base controls.

rag.py

Contains document processing, chunking, embeddings, ChromaDB storage, semantic search, and knowledge-base management.

requirements.txt

Contains the Python dependencies required to run the project.

⚙️ Setup
1. Clone the repository
git clone https://github.com/Aditya-Pratap-01/personal-knowledge-base-rag.git

Move into the project directory:

cd personal-knowledge-base-rag
2. Create a virtual environment
python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Add your Groq API key

Create a file named:

.env

Add:

GROQ_API_KEY=your_groq_api_key_here

Do not commit the .env file to GitHub.

5. Run the application
streamlit run app.py

The application will open in your browser.

💬 Example Usage

Upload your notes and click:

Index uploaded notes

Then ask questions related to your notes.

For example:

How long does a typical sleep cycle last according to the notes?

The assistant retrieves the relevant chunk and generates an answer with a citation:

A typical sleep cycle lasts about 90 minutes. [SOURCE 1]

The application also shows the exact source chunk used to generate the answer.

🚫 Grounded Answering

A key goal of this project is to avoid hallucination.

If the uploaded notes do not contain enough information, the assistant responds:

I couldn't find enough information in your notes to answer that.

It does not intentionally fill the gap using outside knowledge.

For unsupported questions, the application also does not display unrelated retrieved chunks as "Exact chunks used."

🔄 Document Re-indexing

If a document is updated and uploaded again, the application removes the older chunks belonging to that file before inserting the new chunks.

This prevents outdated information from remaining in the vector database.

🧪 Testing

The application was tested for:

Successful PDF ingestion
Markdown ingestion
Semantic question retrieval
Grounded answers
Source citations
Unsupported questions
Re-indexing updated documents
Stale chunk removal
Knowledge-base clearing
Hiding retrieved chunks when an answer cannot be supported 

📌 Current Limitations
Embeddings are generated locally on the machine.
PDF extraction depends on the PDF containing extractable text.
Retrieval quality depends on the quality and structure of the uploaded notes.
The application currently uses a simple character-based chunking strategy.
The vector database is local and persistent rather than hosted remotely.
🔮 Possible Improvements

With more development time, the project could be extended with:

Better semantic chunking
Reranking of retrieved documents
Metadata filtering
Conversation-aware retrieval
More advanced citation handling
Multiple knowledge bases
Authentication
Cloud-hosted vector database
Cloud deployment
Improved document parsing
Streaming LLM responses
👨‍💻 Author

Aditya Pratap

GitHub:

https://github.com/Aditya-Pratap-01

⭐ Project Goal

The goal of this project is to build a simple but practical personal knowledge assistant that demonstrates the core concepts of Retrieval-Augmented Generation:

Documents → Chunks → Embeddings → Vector Search → Retrieved Context → LLM → Grounded Answer