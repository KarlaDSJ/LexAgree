import pandas as pd
import numpy as np
from pathlib import Path
import re
import argparse
from huggingface_hub import login
import os
import typing
from transformers import AutoTokenizer, AutoModel, pipeline, GenerationConfig
import torch, gc
import torch.nn.functional as F
from code.prompts import prompts_messages

temperature = 0.5 # optional
max_tokens = 1024
top_p = 0.7 # optional
CHAR_COUNT = 2500
OVERLAP = round(CHAR_COUNT * 0.2)

def clean_data(text):
    text = text.replace('\n', '').strip()
    return re.sub(r'\s+', ' ', text)
        

def get_windows(text_filename, char_count, overlap):
    """
    Split the text in windows

    :param text_filename: path to the file to read.
    :param char_count: window size.
    :param overlap: indicates the number of overlapping characters between windows.

    :return Str list of the windows.
    """
    with open(text_filename, 'r') as file:
      text = clean_data(file.read())

    text_windows = []
    start = 0
    end = char_count

    while start < len(text):

        window = text[start:end]
        text_windows.append(window)

        start = round(end - overlap)
        end = round(start + char_count)

    return text_windows

def ask_to_llm(messages, text, pipeline_model):
    """
    Ask the prompt to LLM 

    :param pipeline: Path to the folder to read.
    :param messages: the prompt to ask to LLM.
    :param text: the input of the prompt.

    :return str the answers of the prompt
    """
    messages = messages
    messages[0]['content'] += text

    with torch.inference_mode():
        gen_config = GenerationConfig(
            max_new_tokens=300,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            use_cache=False,
            pad_token_id=pipeline_model.tokenizer.eos_token_id
        )

        outputs = pipeline_model(
            messages,
            generation_config=gen_config
        )

    return outputs[0]["generated_text"][-1]['content']

def apply_prompt(inputs, prompt, pipeline_model, path_answers):
    """
    Apply a prompt for every input

    :param inputs: list of the inputs to test
    :param prompt: the prompt to ask to LLM
    :param text: path to the folder for save the answers.
    """
    with open(path_answers, 'a', encoding='utf-8') as file:
        for i, input_text in enumerate(inputs):
            answer = ask_to_llm(prompt, input_text, pipeline_model)
            print(f"arg {i}")
            file.write(f"{i}### {answer}###\n")
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        gc.collect()

def do_argument_mining(path, prompt, path_answers, pipeline_model, type_file=['.txt']):
    """
    Reads all files in a folder, cleans them, and applies the prompt.

    :param path: Path to the folder to read.
    :param type: List of allowed file extensions (e.g., ['.txt', '.md'])
    """
    folder = Path(path)
    type_file = [ext.lower() for ext in type_file]
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"The path: '{path}' is not valid.")

    for file in folder.iterdir():
        if file.is_file():
            if type_file is None or file.suffix.lower() in type_file:
                try:
                    name = str(file)
                    print(str(path_answers)+str(name[-7:]))
                    text_windows = get_windows(name, CHAR_COUNT, OVERLAP)
                    apply_prompt(text_windows, prompt, pipeline_model, str(path_answers)+str(name[-7:]))
                except Exception as e:
                    print(f"⚠ The file could not be read '{file.name}': {e}")

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data", type=str, help="The path where the data is located")
    parser.add_argument("--prompt", type=str, help="The name of the prompt to use")
    parser.add_argument("--model", type=str, help="The LLM model")
    parser.add_argument("--path_answers", type=str, help="¨Path where the answers are saved")

    args = parser.parse_args()

    login(token=os.environ["HF_TOKEN"])
    print('loading model')
    pipeline_model = pipeline(
        "text-generation",
        model = args.model,
        device_map="auto",
        dtype=torch.float16,
    )
    print('model ok')
    prompt = prompts_messages[args.prompt]
    print(prompt)
    print('identify arguments')
    if args.prompt == 'identify_arguments':
        #do_argument_mining(args.data, prompt, args.path_answers, pipeline_model)
        print(args.data)
        text_windows = get_windows(args.data, CHAR_COUNT, OVERLAP)
        apply_prompt(text_windows, prompt, pipeline_model, args.path_answers)


        

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")