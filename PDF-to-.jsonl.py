import fitz 
import jsonlines
import os
import re
import tkinter as tk
from tkinter import filedialog

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        cleaned_text = clean_text(text)
        text_data.append({"page_number": page_num + 1, "content": cleaned_text})
    return text_data

def clean_text(text):
    # Remove multiple spaces, newlines, and special characters
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9\s,.?!]', '', text)
    return text.strip()

def write_to_jsonl(data, output_path):
    with jsonlines.open(output_path, mode='w') as writer:
        writer.write_all(data)

def convert_pdfs_to_jsonl(pdf_paths, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for pdf_path in pdf_paths:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{pdf_name}.jsonl")
        
        # Extract text from the PDF
        text_data = extract_text_from_pdf(pdf_path)
        
        # Write structured data to a .jsonl file
        write_to_jsonl(text_data, output_path)
        print(f"Converted {pdf_path} to {output_path}")

def select_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory(title="Select PDF Directory")
    return directory

def get_all_pdf_paths(directory):
    pdf_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))
    return pdf_paths

# Example usage
pdf_directory = select_directory()
output_dir = filedialog.askdirectory(title="Select Output Directory")

if pdf_directory and output_dir:
    pdf_paths = get_all_pdf_paths(pdf_directory)
    convert_pdfs_to_jsonl(pdf_paths, output_dir)
else:
    print("No PDF directory selected or no output directory specified.")
