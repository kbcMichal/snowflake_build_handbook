import pandas as pd
import json
import re
from datetime import datetime

# Input file paths
INPUT_FILE = 'in/tables/processed_reviews.csv'
OUTPUT_FILE_PARSED = 'out/tables/reviews_parsed.csv'
OUTPUT_FILE_KEYWORDS = 'out/tables/keyword_counts.csv'

# Load the data
data = pd.read_csv(INPUT_FILE)

# Function to extract JSON from the "result_value" column
def extract_json_from_text(row):
    try:
        # Remove the static prompt
        cleaned_row = re.sub(
            r'^Process the below text in 3 ways:.*?Return the JSON only, do not append with the word "json".', 
            '', 
            row, 
            flags=re.DOTALL
        ).strip()
        
        # Extract the JSON block using regex
        json_match = re.search(r'\{.*\}', cleaned_row, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())  # Parse JSON into a dictionary
        return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e} in row: {row}")
        return None

# Function to convert ISO 8601 date to 'YYYY-MM-DD'
def convert_date(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None  # Return None if the date parsing fails

# Function to categorize sentiment based on score
def categorize_sentiment(score):
    if score < -0.2:
        return 'Negative'
    elif -0.2 <= score <= 0.2:
        return 'Neutral'
    else:
        return 'Positive'

# Extract JSON from the "result_value" column
data['parsed_json'] = data['result_value'].apply(extract_json_from_text)

# Extract individual fields from the parsed JSON
data['text_in_english'] = data['parsed_json'].apply(lambda x: x.get('text_in_english') if x else None)
data['parsed_date'] = data['publishedAtDate'].apply(convert_date)
data['keywords'] = data['parsed_json'].apply(lambda x: ', '.join(x.get('keywords', [])) if x else None)
data['sentiment'] = data['parsed_json'].apply(lambda x: x.get('sentiment') if x else None)

# Ensure sentiment is numeric, handle NaN, and round to 1 decimal place
data['sentiment'] = pd.to_numeric(data['sentiment'], errors='coerce')
data['sentiment'] = data['sentiment'].round(1)

# Categorize sentiment into 'Positive', 'Neutral', 'Negative'
data['sentiment_category'] = data['sentiment'].apply(categorize_sentiment)

# Remove rows where parsing failed (e.g., missing sentiment)
data = data.dropna(subset=['sentiment'])

# Process keywords: explode into individual rows
df_keywords = data.copy()
df_keywords['keywords'] = df_keywords['keywords'].str.split(', ')
df_exploded = df_keywords.explode('keywords')

# Aggregate keyword counts by sentiment, keyword, and parsed date
keyword_counts = (
    df_exploded.groupby(['sentiment', 'keywords', 'parsed_date'])
    .size()
    .reset_index(name='counts')
)

# Save the processed data and keyword counts
data.to_csv(OUTPUT_FILE_PARSED, index=False)
keyword_counts.to_csv(OUTPUT_FILE_KEYWORDS, index=False)

print(f"Parsed reviews saved to: {OUTPUT_FILE_PARSED}")
print(f"Keyword counts saved to: {OUTPUT_FILE_KEYWORDS}")