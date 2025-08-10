#!/usr/bin/env python3
"""
Script to clean up the vendored model directory and keep only essential files.
"""

import shutil
from pathlib import Path

def cleanup_model():
    """Clean up the model directory to keep only essential files."""
    
    model_path = Path("models/all-MiniLM-L6-v2")
    
    if not model_path.exists():
        print("❌ Model directory not found!")
        return False
    
    print(f"🧹 Cleaning up model directory: {model_path}")
    
    # Files to keep (essential for PyTorch inference)
    essential_files = [
        "config.json",
        "tokenizer.json", 
        "tokenizer_config.json",
        "vocab.txt",
        "special_tokens_map.json",
        "sentence_bert_config.json",
        "config_sentence_transformers.json",
        "modules.json",
        "pytorch_model.bin"
    ]
    
    # Directories to keep
    essential_dirs = [
        "1_Pooling"
    ]
    
    # Get all files and directories
    all_items = list(model_path.rglob('*'))
    
    # Count items to be removed
    items_to_remove = []
    for item in all_items:
        if item.is_file():
            if item.name not in essential_files and not any(item.name.startswith(prefix) for prefix in essential_files):
                items_to_remove.append(item)
        elif item.is_dir() and item.name not in essential_dirs and item.name != '.cache':
            items_to_remove.append(item)
    
    print(f"📊 Found {len(items_to_remove)} items to remove")
    
    # Remove non-essential items
    for item in items_to_remove:
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"⚠️ Could not remove {item}: {e}")
    
    # Remove .cache directory if it exists
    cache_dir = model_path / ".cache"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print("🗑️ Removed .cache directory")
        except Exception as e:
            print(f"⚠️ Could not remove .cache directory: {e}")
    
    # Check final size
    final_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
    final_size_mb = final_size / (1024 * 1024)
    
    print(f"✅ Model cleanup completed!")
    print(f"📊 Final size: {final_size_mb:.1f} MB")
    
    # List remaining files
    print("\n📄 Remaining files:")
    for file in sorted(model_path.rglob('*')):
        if file.is_file():
            size_kb = file.stat().st_size / 1024
            print(f"   {file.relative_to(model_path)} ({size_kb:.1f} KB)")
    
    return True

if __name__ == "__main__":
    cleanup_model()
