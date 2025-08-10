#!/usr/bin/env python3
"""
Verification script for the offline RAG system.
Tests that the system works completely offline for embeddings.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_environment():
    """Check that environment variables are set for offline operation."""
    print("🔍 Checking environment variables...")
    
    offline = os.getenv("TRANSFORMERS_OFFLINE", "0")
    telemetry = os.getenv("HF_HUB_DISABLE_TELEMETRY", "0")
    
    print(f"   TRANSFORMERS_OFFLINE: {offline}")
    print(f"   HF_HUB_DISABLE_TELEMETRY: {telemetry}")
    
    if offline == "1" and telemetry == "1":
        print("✅ Environment variables set correctly for offline operation")
        return True
    else:
        print("⚠️ Environment variables not set for offline operation")
        return False

def check_files():
    """Check that all required files exist."""
    print("\n📁 Checking required files...")
    
    required_files = [
        "models/all-MiniLM-L6-v2/pytorch_model.bin",
        "models/all-MiniLM-L6-v2/config.json",
        "models/all-MiniLM-L6-v2/tokenizer.json",
        "data/healthcare.db",
        "data/faiss_index_notice_privacy/index.faiss",
        "data/faiss_index_notice_privacy/index.pkl"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            print(f"   ✅ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def test_model_loading():
    """Test that the model can be loaded offline."""
    print("\n🧪 Testing model loading...")
    
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        
        # Set environment variables for offline operation
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        
        # Test loading the local model
        embedding = HuggingFaceEmbeddings(
            model_name="models/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        embedding_result = embedding.embed_query(test_text)
        
        print(f"   ✅ Model loaded successfully!")
        print(f"   📏 Embedding dimension: {len(embedding_result)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        return False

def test_application():
    """Test the application by starting it and making requests."""
    print("\n🚀 Testing application...")
    
    # Set environment variables
    env = os.environ.copy()
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    
    # Start the application
    print("   Starting application...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the application to start
    time.sleep(10)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Application started successfully")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test database query
        print("   Testing database query...")
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": "How many patients have hypertension?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("tool") == "SQL_Agent":
                print("   ✅ Database query successful")
            else:
                print(f"   ❌ Database query failed: {data}")
                return False
        else:
            print(f"   ❌ Database query failed: {response.status_code}")
            return False
        
        # Test PDF query
        print("   Testing PDF query...")
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": "What are my privacy rights?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("tool") == "PDF_RetrievalQA":
                print("   ✅ PDF query successful")
            else:
                print(f"   ❌ PDF query failed: {data}")
                return False
        else:
            print(f"   ❌ PDF query failed: {response.status_code}")
            return False
        
        return True
        
    finally:
        # Stop the application
        process.terminate()
        process.wait()

def main():
    """Main verification function."""
    print("🔍 Offline RAG System Verification")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Check files
    files_ok = check_files()
    
    # Test model loading
    model_ok = test_model_loading()
    
    # Test application
    app_ok = test_application()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Verification Summary:")
    print(f"   Environment: {'✅' if env_ok else '❌'}")
    print(f"   Files: {'✅' if files_ok else '❌'}")
    print(f"   Model Loading: {'✅' if model_ok else '❌'}")
    print(f"   Application: {'✅' if app_ok else '❌'}")
    
    if all([env_ok, files_ok, model_ok, app_ok]):
        print("\n🎉 All tests passed! The offline RAG system is working correctly.")
        print("\n📝 The system is ready for deployment to Railway/Render.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
