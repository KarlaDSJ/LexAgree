import copy
import gc
import torch
from transformers import GenerationConfig
from clean import clean_llm_response

def ask_to_llm(messages, text, pipeline_model, temperature=0.3, top_p=0.9, max_new_tokens=300):
    """Sends a prompt + text to an LLM and returns its response as a string.

    :param messages: base prompt, chat format (list of dictionaries {“role”, “content”}).
                      Copied before being modified
    :param text: the text segment to be analyzed.
    :param pipeline_model: HF pipeline already loaded for this LLM.
    """
    local_messages = copy.deepcopy(messages)
    local_messages[0]['content'] += text

    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        use_cache=True,
        pad_token_id=pipeline_model.tokenizer.eos_token_id,
    )

    with torch.inference_mode():
        outputs = pipeline_model(local_messages, generation_config=gen_config)

    return outputs[0]["generated_text"][-1]['content']

def apply_prompt(
    inputs,
    prompt,
    pipeline_model,
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_new_tokens: int = 300,
    empty_cache_every: int = 20,
):
    """Applies prompt to each element of inputs and returns a list of responses
    :param empty_cache_every: how many iterations to wait before freeing CUDA memory
    """
    answers = []
    for i, input_text in enumerate(inputs):
        answer = ask_to_llm(
                prompt, input_text, pipeline_model,
                temperature=temperature, top_p=top_p, max_new_tokens=max_new_tokens,
        )

        answers.append(clean_llm_response(answer))
        if empty_cache_every and i % empty_cache_every == 0:
            _free_cuda_memory()

    _free_cuda_memory()


def _free_cuda_memory():
    """Free CUDA memory if a GPU is available"""
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
    gc.collect()