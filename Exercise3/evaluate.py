import os
import subprocess
import re
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
import pandas as pd
import sqlite3
from nltk.translate.bleu_score import sentence_bleu

def execute_test(filepath):
    _, ext = os.path.splitext(filepath)
    if ext == '.ts':
        cmd = ['npx', 'playwright', 'test', filepath]
    elif ext == '.py':
        cmd = ['python', filepath]
    try:
        subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True  # Execution successful
    except subprocess.CalledProcessError as e:
        print(f"Error executing tests for {filepath}: {e}")
        #print(f"Return code: {e.returncode}")
        #print(f"Command: {e.cmd}")
        #print(f"Output: {e.output.decode('utf-8')}")
        #print(f"Standard Error: {e.stderr.decode('utf-8')}")
        return False 

def extract_filename_and_ext_from_path(script_path):
    file_name, ext = os.path.splitext(script_path)
    file_ext = ext
    while True:
        file_name, ext = os.path.splitext(file_name)
        if ext:
            file_ext = ext + file_ext
        else:
            break
    file_name = file_name.split('/')[-1]
    return  file_name, file_ext


def modify_script(script_path, screenshot_path, file_ext):
    if file_ext == ".py":
        # Define the lines to insert  (Screenshot and Logout)
        line_to_insert = f"await page.screenshot(path='{screenshot_path}')\n"
        logout = f"    await page.get_by_role('button', name='Admin').click()\n" + f"    await page.get_by_role('menuitem', name='Abmelden').click()\n"
        pattern = r'await\s+page\.close\(\)'
        indent = '    ' # indentation of line afterwards (await page.close())
    if file_ext == ".spec.ts":
        line_to_insert = f"  await page.screenshot({{ path: '{screenshot_path}' }});\n"
        logout = f"  await page.getByRole('button', {{name:'Admin'}}).click()\n" + f"  await page.getByRole('menuitem', {{name:'Abmelden'}}).click()\n"
        pattern = r'\}\);$'
        indent = '' # indentation of line afterwards (closing brackets)
     # Read the script content
    with open(script_path, 'r') as file:
        script_content = file.read()

     # Use regular expression to find the last occurrence of "await page.close()" and insert the new line before it
    modified_script = re.sub(pattern, line_to_insert +  logout + indent + r'\g<0>', script_content, count=1, flags=re.MULTILINE)
    new_path = f"test_playwright_script{file_ext}"
    with open(new_path, 'w') as file:
        file.write(modified_script)
    return new_path, screenshot_path

def execute_tests_in_folder(folder_path, dir_name, conn):
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return
    id_list = []
    executable_list = []
    bleu_list = []
    path = os.path.join(folder_path, dir_name)
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py') or file.endswith('.ts'):
                file_path = os.path.join(root, file).replace("\\", "/")
                file_name, file_ext =  extract_filename_and_ext_from_path(file_path)
                screenshot_path = f'data/generated_screenshots/{dir_name}/{file_name}.png'
                db_id = file_name.replace("_", ".")
                id_list.append(db_id)
                modified_playwright_path, _ = modify_script(file_path,  screenshot_path, file_ext)
                executable = execute_test(modified_playwright_path)
                bleu_score = calculate_bleu_score(file_path, db_id, conn)
                bleu_list.append(bleu_score)
                executable_list.append(executable)
                print(f"Executed tests for: {file_path}: {executable}")

    return id_list, executable_list, bleu_list


def calculate_bleu_score(file_path, db_id, conn):
    item = get_item_by_id( conn=conn, item_id=db_id)
    original_script_path = os.path.join("data", item[5]).replace("\\", "/")
    generated_script_path = file_path
    with open(original_script_path, 'r') as file:
        original_script = file.read()
    with open(generated_script_path, 'r') as file:
        generated_script = file.read()
    bleu_score = sentence_bleu([clean_code(original_script).split()], clean_code(generated_script).split())
    return bleu_score


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
    print("Pixel accordance in percent ", similarity_percentage)
    return similarity_percentage

def get_item_by_id(conn, item_id):
    """Retrieve an item from the database by its id."""
    # Create a cursor object to execute queries
    cursor = conn.cursor()
    
    # SQL query to fetch an item by id
    query = "SELECT * FROM tests WHERE id = ?"
    
    # Execute the query with the id parameter
    cursor.execute(query, (item_id,))
    
    # Fetch the result (assuming only one item is expected)
    item = cursor.fetchone()
    
    return item

def calculate_pixel_accordance(df, conn, dir_name):
    for root, _, files in os.walk(f"data/generated_screenshots/{dir_name}"):
        for file in files:
            screenshot_generated = os.path.join(root, file).replace("\\", "/")
            db_id = os.path.splitext(file)[0].replace('_', '.')
            item = get_item_by_id(conn, db_id)
            original_screenshot = os.path.join("data", item[4]).replace("\\", "/")
            accordance = compare_screenshots(original_screenshot, screenshot_generated)
            df.loc[df['id'] == db_id, 'pixel_accordance'] = accordance
    return df

def clean_code(code):
    # Remove inline comments (anything after #)
    code = re.sub(r'//.*', '', code)
    
    # Remove block comments (anything between ''' and ''', or """ and """)
    code = re.sub(r"'''[\s\S]*?'''", '', code)
    code = re.sub(r'"""[\s\S]*?"""', '', code)

    # Remove new lines
    code = re.sub(r'\n', '', code)

    return code


if __name__ == "__main__":
   
    # Connect to the database
    conn = sqlite3.connect('data/playwright_script.db')
    folder_path = "data/generated_scripts/"
    for dir_name in os.listdir(folder_path):
        df = pd.DataFrame(columns=['id', 'executable', 'pixel_accordance', 'bleu_score'])
        id_list, executable_list, bleu_list = execute_tests_in_folder(folder_path, dir_name, conn)
        df['id'] = id_list
        df['executable'] = executable_list
        df['bleu_score'] = bleu_list
        df = calculate_pixel_accordance(df, conn, dir_name)
        # Create the directory if it doesn't exist
        evaluation_dir = "evaluation_results"
        if not os.path.exists(evaluation_dir ):
            os.makedirs(evaluation_dir )
        df.to_csv(f"{evaluation_dir}/evaluation_{dir_name}.csv", index=False)
  
    conn.close()