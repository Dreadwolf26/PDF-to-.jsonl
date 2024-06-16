import os
import jsonlines
from transformers import GPT2Tokenizer

# Initialize the tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

# Function to split text into chunks
def split_into_chunks(text, max_tokens=500):
    tokens = tokenizer.tokenize(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokenizer.convert_tokens_to_string(tokens[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

# Function to generate a prompt instruction based on the text chunk
def generate_prompt_instruction():
    # Instruction for generating a prompt and response
    return "Analyze the following text and generate a relevant question (prompt) about its key features, then provide a detailed response to the generated question."

# Function to process a single JSONL file and create multiple smaller files
def process_jsonl_file(input_file, output_directory, max_chunks_per_file=10):
    with jsonlines.open(input_file) as reader:
        chunks = []
        for obj in reader:
            if 'content' not in obj:
                print(f"Skipping entry in {input_file} because 'content' key is missing: {obj}")
                continue
            text = obj['content']
            chunks.extend(split_into_chunks(text))
        
        file_count = 0
        for i in range(0, len(chunks), max_chunks_per_file):
            output_file = os.path.join(output_directory, f"chunked_{file_count}.jsonl")
            with jsonlines.open(output_file, mode='w') as writer:
                for chunk in chunks[i:i + max_chunks_per_file]:
                    writer.write({
                        "instruction": generate_prompt_instruction(),
                        "prompt": "",
                        "response": "",
                        "text": chunk
                    })
            file_count += 1

    print(f"Processed data saved to {output_directory}")

# Function to walk through the directory and process each JSONL file
def process_directory(directory_path, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.jsonl'):
                input_file = os.path.join(root, file)
                output_file_path = os.path.join(output_directory, os.path.relpath(root, directory_path))
                os.makedirs(output_file_path, exist_ok=True)
                process_jsonl_file(input_file, output_file_path)

# Specify the directory path
input_directory_path = "C:\\Users\\chris\\OneDrive\\Documents\\TradeSystem\\MachineLearningData\\JSONLData"
output_directory_path = "C:\\Users\\chris\\OneDrive\\Documents\\TradeSystem\\MachineLearningData\\JSONLData\\ChunkedData"

# Process the directory
process_directory(input_directory_path, output_directory_path)

print("All files have been processed.")
