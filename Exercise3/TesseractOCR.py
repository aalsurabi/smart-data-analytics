import pytesseract
from PIL import Image
import glob 
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the screenshot folder
screenshot_dir = os.path.join(script_dir, "data", "screenshot")
pattern = os.path.join(screenshot_dir, "*")

# Create a new folder for extracted text files
folder_name = os.path.join(script_dir, "OCR_text_files")
os.makedirs(folder_name, exist_ok=True)

# Get list of files in the directory
screenshots = glob.glob(pattern)

# Debug: Check if any files are found
if not screenshots:
    print(f"No files found in directory: {screenshot_dir}")
else:
    print(f"Found {len(screenshots)} files in directory: {screenshot_dir}")

# Process each file
for screenshot_path in screenshots:
    if os.path.isfile(screenshot_path):
        try:
            print(f"Processing file: {screenshot_path}")  # Debug: Check file being processed
            image = Image.open(screenshot_path)
            # Perform OCR on the image
            text = pytesseract.image_to_string(image)
            
            # Get the base name of the file and create a new file name for the OCR text
            base_name = os.path.basename(screenshot_path)
            file_name = f"OCR_text_{os.path.splitext(base_name)[0]}.txt"
            file_path = os.path.join(folder_name, file_name)
        
            # Write the extracted text to the new file
            with open(file_path, 'w') as file:
                file.write(text)
                
            print(f"Saved OCR text to: {file_path}")
        except Exception as e:
            print(f"Failed to process {screenshot_path}: {e}")
