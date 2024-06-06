import fitz  # PyMuPDF
import jsonlines
import os
import tkinter as tk
from tkinter import filedialog

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        text_data.append({"page_number": page_num + 1, "content": text})
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

def select_pdfs():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    pdf_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    return root.tk.splitlist(pdf_paths)

# Example usage
pdf_paths = select_pdfs()
output_dir = filedialog.askdirectory(title="Select Output Directory")

if pdf_paths and output_dir:
    convert_pdfs_to_jsonl(pdf_paths, output_dir)
else:
    print("No PDFs selected or no output directory specified.")
