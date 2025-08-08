# LLM-Based Multi-Database Chatbot System

A comprehensive conversational AI system that combines multiple data sources and intelligent routing to provide comprehensive answers to healthcare-related queries. The system seamlessly integrates SQL database queries with PDF document retrieval, using a sophisticated routing mechanism to determine the most appropriate data source for each question.

## Features

- **Multi-Source Integration**: Combines SQL database queries with PDF document retrieval
- **Intelligent Routing**: Uses LangChain agents to route queries to appropriate data sources
- **Real-time Chat Interface**: Modern web interface with typing indicators and responsive design
- **Healthcare Focus**: Specialized for healthcare data and policy documents
- **Vector Search**: FAISS-based document retrieval for semantic search

## System Architecture

### Components
- **User Interface**: Modern web interface built with HTML5, CSS3, and JavaScript
- **Backend API**: FastAPI-based REST API handling chat requests and agent coordination
- **Router Agent**: Intelligent agent that analyzes queries and routes to appropriate tools
- **SQL Agent**: LangChain SQL agent for structured database queries
- **PDF RAG**: Retrieval Augmented Generation system using FAISS vector store

### Technologies Used
- **Language Model**: OpenAI GPT-3.5-turbo
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Web Framework**: FastAPI
- **Frontend**: HTML5, CSS3, JavaScript

## Data Sources

### SQL Database
- **Patients**: Patient demographics and information
- **Visits**: Medical visit records with reasons
- **Prescriptions**: Medication prescriptions
- **Medications**: Medication catalog with categories

### PDF Documents
- Privacy policies and patient rights
- Healthcare coverage information
- User guides and documentation

## Local Development

### Prerequisites
- Python 3.9+
- OpenAI API key

### Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```
5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Deployment

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
3. Deploy automatically from GitHub

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access
- `PORT`: Automatically set by Railway

## API Endpoints

- `GET /`: Home page
- `GET /chatbot`: Chat interface
- `GET /about`: About page
- `POST /chat`: Chat endpoint for AI responses
- `GET /health`: Health check endpoint

## Project Structure

```
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Procfile               # Railway deployment config
├── runtime.txt            # Python version specification
├── static/                # Static files (CSS, JS)
├── templates/             # HTML templates
├── csv/                   # CSV data files
├── pdf/                   # PDF documents
├── faiss_index_notice_privacy/  # FAISS vector index
└── healthcare.db          # SQLite database
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
