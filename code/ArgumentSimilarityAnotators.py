from code.utilities import *
import openpyxl
import argparse

path_root = '/projects/aidal/answers/'
folder_output = path_root + 'output_arg_similarity'
input_sheetname = 'text_'

def compute_and_save_matches(texts, ann1, ann2, threshold):

  for t in texts:

      sheetname = input_sheetname + t
      original = 'original_' + t
 
      data_original = pd.read_excel(path_root + 'arguments_' + ann1 + '.xlsx', sheet_name=original)
      data_llm = pd.read_excel(path_root + 'arguments_' + ann2 + '.xlsx', sheet_name=sheetname)

      # Convert 'arg_text' column to string type to handle potential non-string values
      data_original['arg_text'] = data_original['arg_text'].astype(str)
      data_llm['arg_text'] = data_llm['arg_text'].astype(str)


      threshold = threshold
      print(f'Getting matches for text {t} with threshold {threshold}')

      # Matches on ORIGINAL
      original_matches, original_no_matches = get_matches(threshold, data_original, data_llm)

      # Matches on LLM:
      llm_matches, llm_no_matches = get_matches(threshold, data_llm, data_original)

      export_path = f'{folder_output}/{threshold}/'
      export_path_end = '.xlsx'

      original_matches.to_excel(export_path + t + ann1 + '_' +ann2 + '_original_matches'  + export_path_end, index=False)
      original_no_matches.to_excel(export_path + t + ann1 + '_' + ann2 + '_original_no_matches'  + export_path_end, index=False)
      llm_matches.to_excel(export_path + t + ann1 + '_' + ann2 + '_llm_matches'  + export_path_end, index=False)
      llm_no_matches.to_excel(export_path + t + ann1 + '_' + ann2 + '_llm_no_matches'  + export_path_end, index=False)

      print('_____________________________________________________________________________________')

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--docs", nargs="+", type=str, help="The list of documents to calculated the similarity")
    parser.add_argument("--ann1", type=str, help="Name of model like annotator 2")
    parser.add_argument("--ann2", type=str, help="Name of model like annotator 2")
    parser.add_argument("--threshold", type=float, help="Threshold of similarity to make a match")

    args = parser.parse_args()

    compute_and_save_matches(args.docs, args.ann1, args.ann2, args.threshold)

if __name__ == "__main__":
    #try:
    main()
    #except Exception as e:
    #    print(f"Error: {e}")
