#!/usr/bin/env python3
"""
Script to download and vendor the sentence-transformers/all-MiniLM-L6-v2 model
for offline use in the LLM-Based Multi-Database Chatbot System.
"""

import os
import shutil
import sys
from pathlib import Path

def download_and_vendor_model():
    """Download the model and copy it to the models directory."""
    
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    local_model_path = Path("models/all-MiniLM-L6-v2")
    
    print(f"🔄 Downloading and vendoring {model_name}...")
    
    # Create models directory if it doesn't exist
    local_model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing model directory if it exists
    if local_model_path.exists():
        print(f"🗑️  Removing existing model directory: {local_model_path}")
        shutil.rmtree(local_model_path)
    
    try:
        # Use huggingface_hub Python API to download the model
        print(f"📥 Downloading {model_name}...")
        from huggingface_hub import snapshot_download
        
        snapshot_download(
            repo_id=model_name,
            local_dir=str(local_model_path),
            local_dir_use_symlinks=False
        )
        
        # Verify the model was downloaded correctly
        required_files = ["config.json", "tokenizer.json", "pytorch_model.bin"]
        missing_files = []
        
        for file in required_files:
            if not (local_model_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required model files: {missing_files}")
            return False
        
        # Check model size
        model_size = sum(f.stat().st_size for f in local_model_path.rglob('*') if f.is_file())
        model_size_mb = model_size / (1024 * 1024)
        
        print(f"✅ Model downloaded successfully!")
        print(f"📁 Location: {local_model_path.absolute()}")
        print(f"📊 Size: {model_size_mb:.1f} MB")
        print(f"📋 Files: {len(list(local_model_path.rglob('*')))}")
        
        # List the files
        print("\n📄 Model files:")
        for file in sorted(local_model_path.rglob('*')):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                print(f"   {file.relative_to(local_model_path)} ({size_kb:.1f} KB)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error: huggingface_hub not installed. Please install it first:")
        print(f"   pip install huggingface-hub")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_model_loading():
    """Test that the vendored model can be loaded correctly."""
    
    print("\n🧪 Testing model loading...")
    
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        
        # Test loading the local model
        embedding = HuggingFaceEmbeddings(
            model_name="models/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        embedding_result = embedding.embed_query(test_text)
        
        print(f"✅ Model loaded successfully!")
        print(f"📏 Embedding dimension: {len(embedding_result)}")
        print(f"🔢 Sample embedding values: {embedding_result[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting model download and vendoring process...")
    print("=" * 60)
    
    success = download_and_vendor_model()
    
    if success:
        print("\n" + "=" * 60)
        test_success = test_model_loading()
        
        if test_success:
            print("\n🎉 Model vendoring completed successfully!")
            print("\n📝 Next steps:")
            print("1. Update main.py to use the local model path")
            print("2. Test the application with offline mode")
            print("3. Build and deploy the Docker container")
        else:
            print("\n❌ Model testing failed!")
            sys.exit(1)
    else:
        print("\n❌ Model download failed!")
        sys.exit(1)
