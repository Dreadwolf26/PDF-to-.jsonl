import fitz  # PyMuPDF
import jsonlines
import os
import re
import tkinter as tk
from tkinter import filedialog

def clean_text(text):
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E]+', ' ', text)
    # Additional cleaning steps can be added here
    return text

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        cleaned_text = clean_text(text)
        text_data.append({"page_number": page_num + 1, "content": cleaned_text})
    return text_data

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

def get_all_pdfs(directory):
    pdf_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))
    return pdf_paths

def select_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory(title="Select Directory of PDFs")
    return directory

# Example usage
pdf_directory = select_directory()
output_dir = filedialog.askdirectory(title="Select Output Directory")

if pdf_directory and output_dir:
    pdf_paths = get_all_pdfs(pdf_directory)
    if pdf_paths:
        convert_pdfs_to_jsonl(pdf_paths, output_dir)
    else:
        print("No PDFs found in the selected directory.")
else:
    print("No directory selected or no output directory specified.")
