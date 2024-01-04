import pandas as pd
import os

def clean_and_sort_csv(file_path):
    df = pd.read_csv(file_path, comment='#')
    sorted_df = df.sort_values(by=df.columns[0])
    return sorted_df

print("Current Working Directory:", os.getcwd())

# Adjust these file paths with your actual file paths
input_file = 'D:\\GitWin\\LoadCell\\log\\serial_log.csv'
output_file = 'D:\\GitWin\\LoadCell\\log\\serial_log_sorted.csv'

sorted_df = clean_and_sort_csv(input_file)
sorted_df.to_csv(output_file, index=False)

print(f"Processed file saved as '{output_file}'")