import os
import subprocess
import re
from PIL import Image
import pandas as pd
import json
import argparse

def get_id_from_file_name(file_name):
    if file_name.endswith(".ts"):
        pattern = r'^(.*?)\.spec\.ts$'
    elif file_name.endswith(".png"):
        pattern = r'^(.*?)\.png$'
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

def modify_scripts(script_dir, modified_scripts_dir, screenshot_dir, html_dir):
    """
    Adds lines for saving screenshot and html, logout
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
                    screenshot_line = f"  await page.screenshot({{ path: '{screenshot_path}' }});\n"
                    logout_line = f"  await page.goto('http://localhost:8080/cadenza/logout');\n"
                    html_line = f"  const htmlContent = await page.content();\n"
                    html_save_line = f"  writeFileSync('{html_path}', htmlContent);\n"
                    pattern = r'\}\);$'
                    modified_script = re.sub(pattern, screenshot_line +  html_line + html_save_line +logout_line  +  r'\g<0>', script_content, count=1, flags=re.MULTILINE)
                    import_statement = "import { writeFileSync } from 'fs';\n"
                    if import_statement not in script_content:
                        script_content = import_statement + script_content
                    
                    with open(modified_script_path, 'w') as file:
                        file.write(modified_script)
    return error_scripts

def execute_scripts(modified_script_dir, test_result_file):
    cmd = f"npx playwright test  {modified_script_dir}"
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
    # Open images
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Check if images are the same size
    if image1.size != image2.size:
        raise ValueError("Images must be the same size")

    # Initialize counters
    width, height = image1.size
    num_pixels = width * height
    identical_pixels = 0

    # Compare pixels
    for x in range(width):
        for y in range(height):
            pixel1 = image1.getpixel((x, y))
            pixel2 = image2.getpixel((x, y))
            if pixel1 == pixel2:
                identical_pixels += 1

    # Calculate similarity percentage
    similarity_percentage = (identical_pixels / num_pixels) * 100
    return similarity_percentage

def calculate_screenshot_similarities(generated_screenshot_dir, original_screenshot_dir ):
    id_list = []
    similarity_list = []
    for root, _, files in os.walk(generated_screenshot_dir):
        for file_name in files:
            if not file_name.endswith(".png"):
                print(f"Error, {file_name} doesn't end with .png")
            else:
                similarity = compare_screenshots(f"{generated_screenshot_dir}/{file_name}", f"{original_screenshot_dir}/{file_name}")
                id_list.append(get_id_from_file_name(file_name))
                similarity_list.append(similarity)
    return id_list, similarity_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('script_dir', help='Directory of generated scripts')
    args = parser.parse_args()
    script_dir = args.script_dir
    if not os.path.isdir(script_dir):
        print(f"Error: {script_dir} is not a valid directory.")
    else:
        original_screenshots_dir = "screenshot"
        # Generate own screenshots and html (if needed) --> Then also adapt path  in calculate_screenshot_similarities
        #test_script_dir = "test_script"
        #original_screenshots_dir = f"generated_screenshots/{test_script_dir}"
        #modified_test_scripts_dir = f"modified_scripts/{test_script_dir}"
        #error_id_list_test = modify_scripts(test_script_dir, modified_test_scripts_dir, original_screenshots_dir, f"generated_html/{test_script_dir}")
        #if len(error_id_list_test) > 0:
        #    # there shouldn't be any syntax errors in test files
        #    print("Error, some of original test scripts have a Syntax Error!")
        #execute_scripts(modified_test_scripts_dir, f"test_results_{test_script_dir}.json" )

        leaf_dir = os.path.basename(script_dir)
        modified_scripts_dir = f"modified_scripts/{leaf_dir}"
        screenshots_dir = f"generated_screenshots/{leaf_dir}"
        
        # Test executability
        error_id_list = modify_scripts(script_dir, modified_scripts_dir, screenshots_dir, f"generated_html/{leaf_dir}")
        test_result_file = f"test_results.json" # defined in playwright.config.ts
        execute_scripts(modified_scripts_dir, test_result_file )
        id_list, executable_list = get_test_results(test_result_file)
        error_id_executable_list = [False] * len(error_id_list)

        # Save results in dataframe
        concatenated_id_list = error_id_list + id_list
        concatenated_executable_list = error_id_executable_list + executable_list
        df = pd.DataFrame({'id': concatenated_id_list, 'executable': concatenated_executable_list})

        # Calculate similarity scores
        img_id_list, img_similarity_list = calculate_screenshot_similarities(screenshots_dir, "screenshot")
        print(img_id_list)
        print(img_similarity_list)
        # Create a dictionary to map IDs to similarities
        similarity_dict = dict(zip(img_id_list, img_similarity_list))
        # Add a new column 'similarity' with NaN
        df['screenshot_similarity'] = None
        # Update 'similarity' column based on the dictionary
        df.loc[df['id'].isin(id_list), 'screenshot_similarity'] = df['id'].map(similarity_dict)
        # Save evaluation results
        evaluation_dir = "evaluation_results"
        df = df.sort_values(by='id', ascending=True)
        if not os.path.exists(evaluation_dir):
            os.makedirs(evaluation_dir)
        df.to_csv(f"{evaluation_dir}/evaluation_{leaf_dir}.csv", index=False)