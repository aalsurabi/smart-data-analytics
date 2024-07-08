import sqlite3
import os
import pandas as pd
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTFeatureExtractor, AutoTokenizer, Seq2SeqTrainer, Seq2SeqTrainingArguments
from torch.utils.data import Dataset, DataLoader
import torch

# Step 1: Load Data from SQLite Database
db_path = '/Users/aalsurabi/Desktop/SmartDataAnalytics/smart-data-analytics/Exercise3/data/playwright_script.db'
conn = sqlite3.connect(db_path)
query = "SELECT expectation, screenshot FROM tests"
df = pd.read_sql_query(query, conn)
conn.close()

# Paths to images
base_image_path = '/Users/aalsurabi/Desktop/SmartDataAnalytics/smart-data-analytics/Exercise3/data/screenshots/'

# Add full paths to the dataframe
df['screenshot'] = df['screenshot'].apply(lambda x: os.path.join(base_image_path, os.path.basename(x)))

# Step 2: Preprocess the Data
# Tokenizer and feature extractor initialization
model_name = "your-llava-model"  # Replace with your specific model
feature_extractor = ViTFeatureExtractor.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

class WebAppScreenshotDataset(Dataset):
    def __init__(self, dataframe, feature_extractor, tokenizer, max_length=512):
        self.dataframe = dataframe
        self.feature_extractor = feature_extractor
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        image_path = row['screenshot']
        description = row['expectation']

        # Load and preprocess the image
        image = Image.open(image_path).convert("RGB")
        pixel_values = self.feature_extractor(images=image, return_tensors="pt").pixel_values

        # Tokenize the description
        inputs = self.tokenizer(description, max_length=self.max_length, padding="max_length", truncation=True, return_tensors="pt")
        input_ids = inputs.input_ids.squeeze()
        attention_mask = inputs.attention_mask.squeeze()

        return {
            "pixel_values": pixel_values.squeeze(),
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }

# Create dataset and dataloader
dataset = WebAppScreenshotDataset(df, feature_extractor, tokenizer)
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

# Step 3: Fine-tune the Model
model = VisionEncoderDecoderModel.from_pretrained(model_name)

training_args = Seq2SeqTrainingArguments(
    predict_with_generate=True,
    evaluation_strategy="epoch",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_dir='./logs',
    logging_steps=10,
    save_total_limit=2,
    num_train_epochs=3,
    output_dir="./llava-webapp-finetuned"
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    eval_dataset=dataset,
    tokenizer=tokenizer,
)

trainer.train()

# Step 4: Save the Fine-tuned Model
model.save_pretrained("./llava-webapp-finetuned")
feature_extractor.save_pretrained("./llava-webapp-finetuned")
tokenizer.save_pretrained("./llava-webapp-finetuned")

# Step 5: Evaluate the Model (Example of generating a description)
def generate_description(image_path, model, feature_extractor, tokenizer):
    image = Image.open(image_path).convert("RGB")
    pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return generated_text

# Example usage
test_image_path = "/Users/aalsurabi/Desktop/SmartDataAnalytics/smart-data-analytics/Exercise3/data/screenshots/1_1.png"
print(generate_description(test_image_path, model, feature_extractor, tokenizer))
