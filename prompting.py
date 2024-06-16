import os
import spacy
import pandas as pd
import json
import time
import requests
from transformers import pipeline, set_seed

# Load the spaCy model for Named Entity Recognition
nlp = spacy.load("en_core_web_sm")

# Function to start NeMo inference server
def start_nemo_server():
    model_path = "<PATH_TO_MODEL>"
    web_port = 1424

    script = f"""
    NEMO_FILE={model_path}
    WEB_PORT={web_port}

    depends_on () {{
        HOST=$1
        PORT=$2
        STATUS=$(curl -X PUT http://$HOST:$PORT >/dev/null 2>/dev/null; echo $?)
        while [ $STATUS -ne 0 ]
        do
            echo "waiting for server ($HOST:$PORT) to be up"
            sleep 10
            STATUS=$(curl -X PUT http://$HOST:$PORT >/dev/null 2>/dev/null; echo $?)
        done
        echo "server ($HOST:$PORT) is up running"
    }}

    /usr/bin/python3 /opt/NeMo/examples/nlp/language_modeling/megatron_gpt_eval.py \
        gpt_model_file=$NEMO_FILE \
        pipeline_model_parallel_split_rank=0 \
        server=True tensor_model_parallel_size=8 \
        trainer.precision=bf16 pipeline_model_parallel_size=2 \
        trainer.devices=8 \
        trainer.num_nodes=2 \
        web_server=False \
        port=${web_port} &
    SERVER_PID=$!

    readonly local_rank="${{LOCAL_RANK:=${{SLURM_LOCALID:=${{OMPI_COMM_WORLD_LOCAL_RANK:-}}}}}}"
    if [ $SLURM_NODEID -eq 0 ] && [ $local_rank -eq 0 ]; then
        depends_on "0.0.0.0" ${web_port}

        echo "start get json"
        sleep 5

        echo "SLURM_NODEID: $SLURM_NODEID"
        echo "local_rank: $local_rank"
        /usr/bin/python3 /scripts/call_server.py
        echo "clean up dameons: $$"
        kill -9 $SERVER_PID
        pkill python
    fi
    wait
    """

    with open("nemo_inference.sh", "w") as file:
        file.write(script)

    os.system("bash nemo_inference.sh")

# Define the function to make requests to the inference server
def text_generation(data, ip='localhost', port=1424):
    headers = {"Content-Type": "application/json"}
    resp = requests.put(f'http://{ip}:{port}/generate', data=json.dumps(data), headers=headers)
    return resp.json()

def get_generation(prompt, greedy, add_BOS, token_to_gen, min_tokens, temp, top_p, top_k, repetition, batch=False):
    data = {
        "sentences": [prompt] if not batch else prompt,
        "tokens_to_generate": int(token_to_gen),
        "temperature": temp,
        "add_BOS": add_BOS,
        "top_k": top_k,
        "top_p": top_p,
        "greedy": greedy,
        "all_probs": False,
        "repetition_penalty": repetition,
        "min_tokens_to_generate": int(min_tokens),
        "end_strings": ["", "<extra_id_1>", "\x11", "<extra_id_1>User"],
    }
    sentences = text_generation(data, port=1424)['sentences']
    return sentences[0] if not batch else sentences

# Function to generate specific prompts and responses
def generate_specific_prompts_and_responses(text):
    doc = nlp(text)
    entities = [ent.text for ent in doc.ents]
    
    if entities:
        # Create a prompt based on identified entities
        entity = entities[0]
        prompt = f"What are the key points about {entity}?"
        
        # Generate a response using the inference server
        formatted_prompt = f"The key points about {entity} are:"
        generated_response = get_generation(formatted_prompt, greedy=True, add_BOS=False, token_to_gen=100, min_tokens=1, temp=1.0, top_p=1.0, top_k=0, repetition=1.0, batch=False)
        response = generated_response
    else:
        # Fallback prompt and response
        prompt = "What specific topics are covered in this section?"
        response = f"The specific topics covered in this section include: {text[:150]}..."
    
    return prompt, response

def process_jsonl_file(file_path):
    start_time = time.time()
    
    def read_jsonl(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
        data = [json.loads(line) for line in lines]
        return pd.DataFrame(data)

    # Read the JSONL file into a DataFrame
    df = read_jsonl(file_path)

    # Apply the function to each row to generate specific prompts and responses
    prompts = []
    responses = []
    for idx, row in df.iterrows():
        prompt, response = generate_specific_prompts_and_responses(row['text'])
        prompts.append(prompt)
        responses.append(response)
        
        # Print every 100th prompt and response
        if idx % 100 == 0:
            print(f"Prompt {idx}: {prompt}")
            print(f"Response {idx}: {response}")
            print()
    
    df['prompt'] = prompts
    df['response'] = responses

    # Convert the updated DataFrame back to JSONL format
    output_jsonl = df.to_json(orient='records', lines=True)

    end_time = time.time()
    print(f"Processed {file_path} in {end_time - start_time:.2f} seconds")
    
    return output_jsonl

# Function to process all JSONL files in a directory
def process_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            input_file_path = os.path.join(input_dir, filename)
            output_file_path = os.path.join(output_dir, filename)

            # Process the file and get the updated JSONL content
            updated_jsonl_content = process_jsonl_file(input_file_path)

            # Save the updated JSONL content to the output file
            with open(output_file_path, 'w') as file:
                file.write(updated_jsonl_content)

# Define the input and output directories
input_directory = "C:\\Users\\chris\\OneDrive\\Documents\\TradeSystem\\MachineLearningData\\JSONLData\\ChunkedData"
output_directory = "C:\\Users\\chris\\OneDrive\\Documents\\TradeSystem\\MachineLearningData\\JSONLData\\ChunkedDataPRT"

# Start the inference server
start_nemo_server()

# Process all JSONL files in the input directory
process_directory(input_directory, output_directory)
