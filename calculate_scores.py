import pandas as pd
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

def calculate_bleu(reference, hypothesis):
    """Calculate the BLEU score."""
    print(reference,hypothesis)
    reference = [reference.split()]  # NLTK expects a list of lists
    hypothesis = hypothesis.split()
    smoothie = SmoothingFunction().method4  # Use smoothing to handle zero counts
    return sentence_bleu(reference, hypothesis, smoothing_function=smoothie)

def calculate_rouge(reference, hypothesis):
    """Calculate ROUGE scores."""
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores

def process_excel_data(file_path):
    """Process data from an Excel file and calculate BLEU and ROUGE scores."""
    # Read data from Excel file
    data = pd.read_excel(file_path)

    # Initialize lists to store scores
    bleu_scores = []
    rouge_scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}
    # Iterate over each row in the Excel data
    for index, row in data.iterrows():
        question = row['query']
        reference_response = row['reference']
        generated_response = row['response']
        print(row)
        # Calculate BLEU Score
        bleu_score = calculate_bleu(reference_response, generated_response)
        bleu_scores.append(bleu_score)

        # Calculate ROUGE Scores
        rouge_scores_row = calculate_rouge(reference_response, generated_response)
        for metric, score in rouge_scores_row.items():
            rouge_scores[metric].append(score.fmeasure)

    # Add scores to DataFrame
    data['BLEU Score'] = bleu_scores
    for metric, scores_list in rouge_scores.items():
        data[f'ROUGE {metric}'] = scores_list

    # Save DataFrame to Excel with scores
    data.to_excel("scores.xlsx", index=False)

    print("Scores calculated and saved to scores.xlsx")

# Example usage
file_path = "./session_data_with_reference.xlsx"  # Provide the path to your Excel file
process_excel_data(file_path)
