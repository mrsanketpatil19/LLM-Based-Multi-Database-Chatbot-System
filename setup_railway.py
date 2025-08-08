#!/usr/bin/env python3
"""
Setup script for Railway deployment.
This script recreates the FAISS index and database from CSV files.
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF

def create_database():
    """Create SQLite database from CSV files."""
    print("Creating database from CSV files...")
    
    # Create database
    conn = sqlite3.connect('healthcare.db')
    
    # Read CSV files
    patients_df = pd.read_csv('csv/patients.csv')
    visits_df = pd.read_csv('csv/visits.csv')
    prescriptions_df = pd.read_csv('csv/prescriptions.csv')
    medications_df = pd.read_csv('csv/medications.csv')
    
    # Write to database
    patients_df.to_sql('patients', conn, if_exists='replace', index=False)
    visits_df.to_sql('visits', conn, if_exists='replace', index=False)
    prescriptions_df.to_sql('prescriptions', conn, if_exists='replace', index=False)
    medications_df.to_sql('medications', conn, if_exists='replace', index=False)
    
    conn.close()
    print("✅ Database created successfully!")

def create_faiss_index():
    """Create FAISS index from PDF files."""
    print("Creating FAISS index from PDF files...")
    
    # Create FAISS directory
    faiss_dir = Path("faiss_index_notice_privacy")
    faiss_dir.mkdir(exist_ok=True)
    
    # Initialize embeddings
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    # Process PDF files
    pdf_dir = Path("pdf")
    all_texts = []
    all_metadatas = []
    
    if pdf_dir.exists():
        for pdf_file in pdf_dir.glob("*.pdf"):
            print(f"Processing {pdf_file.name}...")
            
            try:
                # Open PDF
                doc = fitz.open(pdf_file)
                
                # Extract text from each page
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    if text.strip():
                        # Split text into chunks
                        chunks = text_splitter.split_text(text)
                        
                        for chunk in chunks:
                            all_texts.append(chunk)
                            all_metadatas.append({
                                "source": pdf_file.name,
                                "page": page_num + 1
                            })
                
                doc.close()
                
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {e}")
    
    if all_texts:
        # Create FAISS index
        vectorstore = FAISS.from_texts(
            texts=all_texts,
            embedding=embedding,
            metadatas=all_metadatas
        )
        
        # Save index
        vectorstore.save_local("faiss_index_notice_privacy")
        print("✅ FAISS index created successfully!")
    else:
        print("⚠️ No PDF files found or processed. FAISS index not created.")

def main():
    """Main setup function."""
    print("🚀 Starting Railway setup...")
    
    # Create database
    create_database()
    
    # Create FAISS index
    create_faiss_index()
    
    print("✅ Railway setup completed!")

if __name__ == "__main__":
    main()
