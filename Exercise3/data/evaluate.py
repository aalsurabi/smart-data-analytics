import os
import subprocess
import re
from PIL import Image
import pandas as pd
import json
import argparse
from pixelmatch.contrib.PIL import pixelmatch
import time
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import nltk


# Download required NLTK data
nltk.download('punkt')

def get_id_from_file_name(file_name):
    if file_name.endswith(".ts"):
        pattern = r'^(.*?)\.spec\.ts$'
    elif file_name.endswith(".png"):
        pattern = r'^(.*?)\.png$'
    elif file_name.endswith(".html"):
        pattern = r'^(.*?)\.html$'
    else:
        pattern = ""
    match = re.match(pattern, file_name)
    name = None
    if not match:
        print(f"Error: {file_name} does not have ending .spec.ts")
    else:
        name = match.group(1).replace("_", ".")
    return name

def initial_syntax_check(code):
    """
    checks if script matches the following pattern, otherwhise executing playwright on folder stops executionl for all tests due to syntax error: 
    import { test, expect } from '@playwright/test';
        ...
        test('test', async ({ page }) => {
        ...
        });
    """
    pattern = r"import \{ test, expect \} from '@playwright\/test';[\s\S]*?test\('test', async \(\{ page \}\) => \{[\s\S]*?\}\);"
    return bool(re.search(pattern, code, re.MULTILINE))

def convert_to_filename(number):
    #  split it at the decimal point
    integer_part, fractional_part = number.split('.')
    
    # Join integer part and fractional part with an underscore
    filename = f"{integer_part}_{fractional_part}.spec.ts"
    
    return filename

def modify_scripts(script_dir, modified_scripts_dir, screenshot_dir, html_dir):
    """
    Adds lines for saving screenshot and html.
    Returns ids of scripts which don't pass initial syntax check.
    """

    if not os.path.exists(modified_scripts_dir):
        os.makedirs(modified_scripts_dir )
    if not os.path.exists(screenshot_dir ):
        os.makedirs(screenshot_dir )
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    
    modified_script_path = f"modified_scripts_dir/{leaf_dir}"
    error_scripts = []
    for root, _, files in os.walk(script_dir):
        for file_name in files:

            if file_name.endswith('.ts'):
                file_path = os.path.join(root, file_name)
                modified_script_path = f"{modified_scripts_dir}/{file_name}"
                screenshot_path = f"{screenshot_dir}/{file_name.replace('.spec.ts', '.png')}"
                html_path = f"{html_dir}/{file_name.replace('.spec.ts', '.html')}"
            
                with open(file_path, 'r') as file:
                    script_content = file.read()
                    
                initial_check_passed = initial_syntax_check(script_content)
                if not initial_check_passed:
                    db_id = get_id_from_file_name(file_name)
                    error_scripts.append(db_id)
                else: 
                    timeout = f"  await page.waitForTimeout(3000);\n" # wait for a few seconds for page to load completely
                    screenshot_line = f"  await page.screenshot({{ path: '{screenshot_path}' }});\n"
                    html_line = f"  const htmlContent = await page.content();\n"
                    html_save_line = f"  writeFileSync('{html_path}', htmlContent);\n"
                    pattern = r'\}\);$'
                    modified_script = re.sub(pattern, timeout + screenshot_line +  html_line + html_save_line +  r'\g<0>', script_content, count=1, flags=re.MULTILINE)
                    import_statement = "import { writeFileSync } from 'fs';\n"
                    if import_statement not in script_content:
                        script_content = import_statement + script_content
                    
                    with open(modified_script_path, 'w') as file:
                        file.write(modified_script)
    return error_scripts

def execute_scripts(modified_script_dir):
    print(modified_script_dir)
    cmd = f"npx playwright test  {modified_script_dir}/"
    try:
        print(f"running command: {cmd}")
        #subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:  # return code is 1 if all tests are executed but at least one fails
            print("Error executing tests")
            print(f"Return code: {e.returncode}")
            print(f"Command: {e.cmd}")


def get_test_results(file):
    """
    Extract test status from test results file.
    """
    with open(test_result_file, 'r') as file:
        data = json.load(file)

    # Initialize lists to store the extracted information
    file_names = []
    test_statuses = []

    # Iterate through the suites in the JSON data
    for suite in data['suites']:
        # Extract the file name and get the desired part of the name
        file_name = suite['file'].split('/')[-1].split('.')[0]
        file_names.append(file_name.replace("_", "."))
        
        # Extract the test status from the first result of the first test in the specs
        test_status = suite['specs'][0]['tests'][0]['results'][0]['status']
        if test_status == "passed":
            test_statuses.append(True)
        else: 
            test_statuses.append(False)
    return file_names, test_statuses


def compare_screenshots(image1_path, image2_path):
    """
    Calculates amount of pixels in percent which are the same for two images.
    """
    # Open images
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Check if images are the same size
    if image1.size != image2.size:
        raise ValueError("Images must be the same size")

    # Initialize counters
    width, height = image1.size
    total_pixels = width * height

    mismatch = pixelmatch(image1, image2)

    # Calculate similarity percentage
    similarity_percentage = (1 - (mismatch / total_pixels)) * 100
    return similarity_percentage

def calculate_screenshot_similarities(generated_screenshot_dir, original_screenshot_dir ):
    print("Calculating screenshot similarities...")
    id_list = []
    total_time = 0
    similarity_list = []
    for root, _, files in os.walk(generated_screenshot_dir):
        for file_name in files:
            if not file_name.endswith(".png"):
                print(f"Error, {file_name} doesn't end with .png")
            else:
                start_time = time.time()
                similarity = compare_screenshots(f"{generated_screenshot_dir}/{file_name}", f"{original_screenshot_dir}/{file_name}")
                end_time = time.time()
                execution_time = end_time - start_time
                total_time += execution_time
                print(f"Similarity {file_name} to original screenshot: {similarity} ({execution_time:.4f} seconds)")
                id_list.append(get_id_from_file_name(file_name))
                similarity_list.append(similarity)
    print(f"Calculating screenshot similarities finished in  {total_time:.4f} seconds")
    return id_list, similarity_list


def extract_text_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        return soup.get_text()

def compare_html_files(html_file1, html_file2):

# Extract text content from HTML files
    text1 = extract_text_from_html(html_file1)
    text2 = extract_text_from_html(html_file2)

    # Create a TF-IDF Vectorizer
    vectorizer = TfidfVectorizer()

    # Vectorize the text content
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # Calculate cosine similarity
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    cosine_sim = similarity_score[0][0]

    # Tokenize the text for BLEU score
    reference = nltk.word_tokenize(text1)
    candidate = nltk.word_tokenize(text2)
    
    # Calculate BLEU score
    smoothie = SmoothingFunction().method4
    bleu_score = sentence_bleu([reference], candidate, smoothing_function=smoothie)

    return cosine_sim, bleu_score


def calculate_html_similarities(generated_html_dir, original_html_dir ):
    print("Calculating html similarities...")
    id_list = []
    total_time = 0
    cosine_similarity_list = []
    bleu_score_list = []
    for root, _, files in os.walk(generated_html_dir):
        for file_name in files:
            if not file_name.endswith(".html"):
                print(f"Error, {file_name} doesn't end with .html")
            else:
                start_time = time.time()
                cosine_sim, bleu_score = compare_html_files(f"{generated_html_dir}/{file_name}", f"{original_html_dir}/{file_name}")
                end_time = time.time()
                execution_time = end_time - start_time
                total_time += execution_time
                print(f"Similarity {file_name} to original html file: cosine similarity: {cosine_sim}, bleu score {bleu_score} ({execution_time:.4f} seconds)")
                id_list.append(get_id_from_file_name(file_name))
                cosine_similarity_list.append(cosine_sim)
                bleu_score_list.append(bleu_score)
    print(f"Calculating html similarities finished in  {total_time:.4f} seconds")
    return id_list, cosine_similarity_list, bleu_score_list

def create_and_save_dataframe(executable_ids, executables, screenshot_ids, screenshot_similarities, html_ids, cosine_similarities, bleu_scores):
    exe_dict = dict(zip(executable_ids, executables))
    screenshot_dict = dict(zip(screenshot_ids, screenshot_similarities))
    html_dict = {
        'id': html_ids,
        'html_cosine_similarity': cosine_similarities,
        'html_bleu_score': bleu_scores
    }
    # Convert dictionaries to DataFrames
    exe_df = pd.DataFrame(list(exe_dict.items()), columns=['id', 'executable'])
    screenshot_df = pd.DataFrame(list(screenshot_dict.items()), columns=['id', 'screenshot_similarities'])
    html_df = pd.DataFrame(html_dict)
   
    # Merge the DataFrames on the 'id' column
    merged_df = pd.merge(exe_df, screenshot_df, on='id', how='outer')
    final_merged_df = pd.merge(merged_df, html_df, on='id', how='outer')

    # Save evaluation results
    evaluation_dir = "evaluation_results"
    df = final_merged_df.sort_values(by='id', ascending=True)
    if not os.path.exists(evaluation_dir):
        os.makedirs(evaluation_dir)
    csv_path = f"{evaluation_dir}/evaluation_{leaf_dir}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results at {csv_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('script_dir', help='Directory of generated scripts')
    parser.add_argument('--no-evaluate', action='store_true', help='Set for generating screenshots and html of test_script,no evaluation')
    args = parser.parse_args()
    script_dir = args.script_dir
    no_evaluate = args.no_evaluate
    
    if not os.path.isdir(script_dir):
        raise RuntimeError(f"Error: {script_dir} is not a valid directory.")
    else:
        leaf_dir = os.path.basename(script_dir)
        modified_scripts_dir = f"modified_scripts/{leaf_dir}"
        screenshots_dir = f"generated_screenshots/{leaf_dir}"
        html_dir = f"generated_html/{leaf_dir}"
        # Test executability
        error_id_list = modify_scripts(script_dir, modified_scripts_dir, screenshots_dir, f"generated_html/{leaf_dir}")
        test_result_file = f"test_results.json" # defined in playwright.config.ts
        execute_scripts(modified_scripts_dir)
        id_list, executable_list = get_test_results(test_result_file)
        error_id_executable_list = [False] * len(error_id_list)
        concatenated_id_list = error_id_list + id_list
        concatenated_executable_list = error_id_executable_list + executable_list

        if no_evaluate:
            # All test script  should be executable
            if  False in concatenated_executable_list:
                ids_error = [item for item, exe in zip(concatenated_id_list, concatenated_executable_list) if not exe]
                print(f"The following test_script files haven't been executed succesfully:   {ids_error}")
                print(f"Trying to run them again...")
                for error_id in ids_error:
                    error_id_file = convert_to_filename(error_id)
                    cmd = f"npx playwright test  {modified_scripts_dir}/{error_id_file}"
                    try:
                        print(f"running command: {cmd}")
                    #subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        subprocess.run(cmd, check=True, shell=True)
                    except subprocess.CalledProcessError as e:
                        print("Error executing test")
                        print(f"Return code: {e.returncode}")
                        print(f"Command: {e.cmd}")
        else:
            # Screenshot Similarities
            original_screenshots_dir = "generated_screenshots/test_script" 
            if not os.path.isdir(original_screenshots_dir):
                raise RuntimeError(f"Error: {original_screenshots_dir} is not a valid directory. Generate test_script screenshots first with the command:  python evaluate.py ./test_script --no-evaluate ")
            img_id_list, img_similarity_list = calculate_screenshot_similarities(screenshots_dir, original_screenshots_dir)

            # HTML similarities
            original_html_dir = "generated_html/test_script" 
            html_id_list, cosine_similarity_list, bleu_score_list = calculate_html_similarities(html_dir, original_html_dir)

            create_and_save_dataframe(concatenated_id_list, concatenated_executable_list, img_id_list, img_similarity_list, html_id_list, cosine_similarity_list, bleu_score_list)