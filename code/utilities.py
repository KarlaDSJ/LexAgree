import pandas as pd
from transformers import AutoTokenizer, AutoModel
import torch
import os
from huggingface_hub import login
import torch.nn.functional as F


login(token=os.environ["HF_TOKEN"])
# model for similarity score
similarity_model = 'sentence-transformers/all-MiniLM-L6-v2'
similarity_model = 'BAAI/bge-m3'
# Load model from HuggingFace Hub
tokenizer = AutoTokenizer.from_pretrained(similarity_model)
model = AutoModel.from_pretrained(similarity_model)


#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):

    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def get_sentence_similarity(sentence1, sentence2):

    # Sentences we want sentence embeddings for
    sentences = [sentence1, sentence2]

    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    cos = torch.nn.CosineSimilarity(dim=0)
    sim = cos(sentence_embeddings[0], sentence_embeddings[1])

    return sim.item()

def get_matches(sim_threshold, base_data, matched_data):

  df_matches = pd.DataFrame(columns=['arg_num', 'arg_text', 'matched_num', 'matched_text'])
  df_no_matches = pd.DataFrame(columns=['arg_num', 'arg_text'])

  for index_base, row_base in base_data.iterrows():

      one_match = False
      for index_matched, row_matched in matched_data.iterrows():

          sim_score = get_sentence_similarity(row_base['arg_text'], row_matched['arg_text'])

          if sim_score >= sim_threshold:
              print(f"Base arg {row_base['arg_num']} has a similarity of {sim_score} with LLM arg {row_matched['arg_num']}")
              df_matches = pd.concat([df_matches, pd.DataFrame([{'arg_num': row_base['arg_num'],
                                                                 'arg_text': row_base['arg_text'],
                                                                 'matched_num': row_matched['arg_num'],
                                                                 'matched_text': row_matched['arg_text'],
                                                                 'similarity': sim_score}])],
                                     ignore_index=True)
              one_match = True

      if one_match == False:
        print(f"Base arg {row_base['arg_num']} has no match with a similarity score >= {sim_threshold}")
        df_no_matches = pd.concat([df_no_matches, pd.DataFrame([{'arg_num': row_base['arg_num'],
                                                                 'arg_text': row_base['arg_text']}])],
                                  ignore_index=True)

  return df_matches, df_no_matches
