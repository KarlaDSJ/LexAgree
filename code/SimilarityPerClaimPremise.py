from code.utilities import *
import argparse

path_root = '/projects/aidal/answers/'
folder_output = path_root + 'output_arg_similarity'

def convert_to_percent_str(value):
  rounded = round(value * 100, 4)
  return str(rounded) + '%'

def get_sentences(row, type_adu):
    sentence1 = row['arg_text']
    sentence2 = row['matched_text']

    claim_sim = 0.0
    premise_sim = 0.0

    # Calculate claim similarity if needed or not specified
    if type_adu == '' or type_adu == 'claims':
        claim_sentence1 = sentence1.split('\n')[-1] if '\n' in sentence1 else sentence1
        claim_sentence2 = sentence2.split('\n')[-1] if '\n' in sentence2 else sentence2
        if claim_sentence1 and claim_sentence2:
            claim_sim = get_sentence_similarity(claim_sentence1, claim_sentence2)

    # Calculate premises similarity if needed or not specified
    if type_adu == '' or type_adu == 'premises':
        premise_sentence1 = sentence1[:sentence1.rindex('\n')] if '\n' in sentence1 else ""
        premise_sentence2 = sentence2[:sentence2.rindex('\n')] if '\n' in sentence2 else ""
        if premise_sentence1 and premise_sentence2:
            premise_sim = get_sentence_similarity(premise_sentence1, premise_sentence2)

    return claim_sim, premise_sim

def get_similarity_alpha(claim_sim, premise_sim, alpha):
  return alpha * premise_sim + (1 - alpha) * claim_sim


def get_similarity_alpha_all(texts, llm_sheets, threshold, alphas, type_adu, ann2):

  for t in texts:
    print(" ----------------")
    print(f'Text: {t}')

    for llm_sheet in llm_sheets:

      #print(f'LLM sheet: {llm_sheet}')
      sheetname_llm = llm_sheet + t
      #data_llm = pd.read_excel(path_input, sheet_name=sheetname_llm)

      output_path = f'{folder_output}/{threshold}/'
      export_path_end = '.xlsx'
      type_comp = '_original'#'_original  _llm'

      llm_matches = pd.read_excel(output_path + t +  ann2 + type_comp + '_matches'  + export_path_end)
      #llm_matches = llm_matches[llm_matches['similarity'] >= 0.75]
      llm_matches[['claim', 'premise']] = llm_matches.apply(lambda x: get_sentences(x, type_adu), axis=1, result_type='expand')

      for i in alphas:
        llm_matches[f'similarity_alpha_{i}'] = llm_matches.apply(lambda x: get_similarity_alpha(x['claim'], x['premise'], i), axis=1)
        grupo = llm_matches.groupby('arg_num')[f'similarity_alpha_{i}'].idxmax()
        llm_matches_unique = llm_matches.loc[grupo].reset_index(drop=True)
        print(f'Mean: {convert_to_percent_str(llm_matches_unique[f"similarity_alpha_{i}"].mean())}')
  
      llm_matches_unique.to_excel(output_path + t + type_comp +  ann2 + '_matches_unique' + export_path_end, index=False)
      #return llm_matches_unique


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--docs", nargs="+", type=str, help="The list of documents to calculated the similarity")
    parser.add_argument("--ann1", type=str, help="Name of combination")

    args = parser.parse_args()
    get_similarity_alpha_all(args.docs, ['text_'], 0.75, [0.7], "", args.ann1)

if __name__ == "__main__":
    #try:
    main()
    #except Exception as e:
    #    print(f"Error: {e}")
