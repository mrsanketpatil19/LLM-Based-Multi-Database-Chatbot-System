# LLM-Based Multi-Database Chatbot System - Offline RAG Deployment

This repository has been configured for offline RAG (Retrieval Augmented Generation) deployment with minimal footprint. The system now operates completely offline for embeddings while maintaining all existing functionality.

## 🎯 Key Features

- **Offline Embeddings**: Uses vendored `sentence-transformers/all-MiniLM-L6-v2` model (~85-95 MB)
- **No Runtime Downloads**: All models and data are pre-packaged
- **CPU-Only**: Optimized for deployment without GPU requirements
- **Docker Ready**: Multi-stage Dockerfile for efficient deployment
- **Railway/Render Compatible**: Ready for cloud deployment

## 📁 Repository Structure

```
├── models/
│   └── all-MiniLM-L6-v2/          # Vendored embedding model (~85-95 MB)
├── data/
│   ├── healthcare.db              # SQLite database with patient data
│   └── faiss_index_notice_privacy/ # FAISS vector index for PDF search
├── static/                        # CSS, JS, and static assets
├── templates/                     # HTML templates
├── csv/                          # Source CSV files for database
├── pdf/                          # Healthcare PDF documents
├── main.py                       # FastAPI application
├── setup_railway.py              # Database and FAISS setup
├── download_model.py             # Model vendoring script
├── deploy.sh                     # Deployment automation script
├── Dockerfile                    # Multi-stage Docker build
└── requirements.txt              # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/mrsanketpatil19/LLM-Based-Multi-Database-Chatbot-System.git
   cd LLM-Based-Multi-Database-Chatbot-System
   ```

2. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```
   
   This script will:
   - Download and vendor the sentence-transformers model
   - Create the SQLite database from CSV files
   - Build the FAISS index from PDF documents
   - Test the application
   - Build Docker image (if Docker is available)

3. **Set your OpenAI API key**
   ```bash
   export OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Start the application**
   ```bash
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

5. **Access the application**
   - Open http://localhost:8000 in your browser
   - Use the chatbot interface to ask questions about healthcare data and policies

## 🐳 Docker Deployment

### Build the Docker image
```bash
docker build -t llm-multidb-chatbot .
```

### Run the container
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here llm-multidb-chatbot
```

## ☁️ Cloud Deployment

### Railway Deployment

1. **Connect to Railway**
   - Fork this repository to your GitHub account
   - Connect your GitHub repository to Railway
   - Railway will automatically detect the Dockerfile

2. **Set Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Railway will automatically set `PORT`

3. **Deploy**
   - Railway will build and deploy automatically
   - No additional configuration needed

### Render Deployment

1. **Connect to Render**
   - Fork this repository to your GitHub account
   - Create a new Web Service in Render
   - Connect your GitHub repository

2. **Configure the service**
   - **Build Command**: `docker build -t llm-multidb-chatbot .`
   - **Start Command**: `docker run -p $PORT:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY llm-multidb-chatbot`
   - **Environment Variables**: Set `OPENAI_API_KEY`

3. **Deploy**
   - Render will build and deploy automatically

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

1. **Download the model**
   ```bash
   python3 download_model.py
   ```

2. **Create database and FAISS index**
   ```bash
   python3 setup_railway.py
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   export OPENAI_API_KEY=your_key_here
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 📊 System Requirements

- **Memory**: Minimum 512MB RAM (1GB recommended)
- **Storage**: ~200MB for application + model + data
- **CPU**: Any modern CPU (no GPU required)
- **Network**: Only for OpenAI API calls (not for embeddings)

## 🔍 Verification

### Offline Operation
The system operates completely offline for embeddings. You can verify this by:

1. **Check environment variables**
   ```bash
   echo $TRANSFORMERS_OFFLINE  # Should be 1
   echo $HF_HUB_DISABLE_TELEMETRY  # Should be 1
   ```

2. **Monitor startup logs**
   - No "downloading model" messages should appear
   - Application should start immediately

3. **Test functionality**
   - Ask a PDF question: "What are my privacy rights?"
   - Ask a database question: "How many patients have hypertension?"
   - Both should work without any model downloads

### Expected Output Format

**Database Query:**
```
Source: Database (SQLite: healthcare.db)
Tool Used: SQL_Agent
SQL: SELECT COUNT(DISTINCT patient_id) FROM visits WHERE LOWER(reason) LIKE '%hypertension%'
Answer: There are 256 patients who have hypertension.
```

**PDF Query:**
```
Source: PDF • Files: Notice-of-Privacy-Practice.pdf (p.5), pdf-system-patient-rights-and-responsiblities-ACB.pdf (p.5)
Tool Used: PDF_RetrievalQA
Answer: Your privacy rights include the right to access your medical records...
```

## 🛠️ Troubleshooting

### Model Loading Issues
- Ensure `models/all-MiniLM-L6-v2/` contains the model files
- Check that `pytorch_model.bin`, `config.json`, and `tokenizer.json` exist
- Verify the model size is ~85-95 MB

### Database Issues
- Ensure `data/healthcare.db` exists
- Check that CSV files are present in the `csv/` directory
- Run `python3 setup_railway.py` to recreate the database

### FAISS Index Issues
- Ensure `data/faiss_index_notice_privacy/` contains `index.faiss` and `index.pkl`
- Check that PDF files are present in the `pdf/` directory
- Run `python3 setup_railway.py` to recreate the FAISS index

### Docker Issues
- Ensure Docker is installed and running
- Check that the Dockerfile is in the root directory
- Verify that all required files are not in `.dockerignore`

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls | Yes | None |
| `TRANSFORMERS_OFFLINE` | Force offline model loading | No | 1 |
| `HF_HUB_DISABLE_TELEMETRY` | Disable HuggingFace telemetry | No | 1 |
| `PORT` | Application port | No | 8000 |

## 🔒 Security Notes

- The application runs as a non-root user in Docker
- No sensitive data is logged or transmitted
- All model files are vendored locally
- Database and FAISS index are pre-built and included

## 📈 Performance

- **Startup Time**: ~5-10 seconds (no model downloads)
- **Query Response**: ~1-3 seconds for most queries
- **Memory Usage**: ~200-300MB during operation
- **CPU Usage**: Moderate (CPU-only inference)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the deployment script
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the AI framework
- [HuggingFace](https://huggingface.co/) for the sentence-transformers model
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
