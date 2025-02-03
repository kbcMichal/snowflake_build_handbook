# Keboola - Snowflake Build hands-on lab - User Guide
[Youtube Video Walkthrough](https://www.youtube.com/watch?v=JKD8BhJ7KJg)

## Getting Started

### Access Your Keboola Project
By following the instructions shared at Snowflake Build class you should receive the email invitation to access your project, which will be named **Snowflake Build #X**.

---

## London Eye Review Analysis Pipeline

This guide will walk you through the creation of a data pipeline to:
1. Collect Google Reviews of the London Eye stored in a MySQL database.
2. Process these reviews using Snowflake SQL transformations.
3. Enrich the data using a HuggingFace LLM model.
4. Parse the LLM response using Python Transformation.
5. Deploy a Streamlit data app to visualize the data.
6. Automate everything.

---

## Step 1: Data Extraction

1. **Login** to your Keboola project, you'll land at the Dashboard page.
   ![Keboola Dashboard](images/keboola_dashboard.png)
2. Click `Components` > `Components` and search for `MySQL`. Click **ADD COMPONENT**.
   ![Menu - Components](images/menu_components.png)
   ![Components - MySQL](images/comp_mysql.png)

3. Click **CONNECT TO MY DATA** and name the configuration: `[build] Reviews` and click **CREATE CONFIGURATION**.
![Connect to my data](images/mysql_mydata.png)
![Configuration name](images/mysql_config.png)

4. Click **SETUP CREDENTIALS** and enter the following credentials:
   - Hostname: `34.46.66.107`
   - Port: `3306`
   - Username: `build_read`
   - Password: https://share.1password.com/s#YNlsZtKpHKh7ObCsPOLPDfAicyIuYFtOcN6JjRH0Wi8
   - Database: `build`
   - Transaction Isolation Level: Default

    ![Setup credentials](images/setup_creds.png)

5. Test the connection and save the configuration.
    ![Save credentials](images/save_creds.png)

### Fetch the Table
1. Click **Select tables to copy** and select the `apify_reviews` table.
    - The table is named apify_reviews because the data was originally scraped from Google Maps using the Apify service. However, to simplify this exercise, the scraped data was preloaded into a MySQL database instead of running the scraper at scale.

    ![Select table](images/select_tables.png)

2. Click **CREATE TABLE** 
    ![Create table](images/create_table.png)
    - Keboola automatically creates a `configuration row` for each selected table. Click the row to enter the row configuration details.
        ![Configuration row](images/config_row.png)
    - In the detailed settings we can configure incremental fetching as well as loading to Keboola, primary keys or even use the “advanced mode” to enter a SQL statement instead. This statement will be executed by Keboola in the source MySQL database, and the result will then be processed and stored in Keboola. We’ll keep the settings default, as it is. 

3. Click **RUN** to execute the connector job to fetch the data into Keboola's backend (Snowflake).
    ![Run extractor](images/run_extractor.png)

    Click RUN again in the dialog popup.

    ![Run extractor dialog](images/run_dialog.png)

4. We executed a **JOB**. Navigate to **Jobs** from the main menu to see a list of jobs.
    ![Jobs](images/jobs.png)
    Click the job to enter its detail.

5. Navigate to **Storage** from the main menu.
    - The Storage UI is an explorer of the objects that are stored in the Snowflake backend behind Keboola. 
    - After the executed Job finishes successfully we'll see a new data bucket (Snowflake Schema) there.
        - Expand the bucket  to see the tables. Then click the Table to view its details:
        ![Storage](images/storage.png)
        ![Storage table](images/storage_table.png)
    - At the `Overview` tab we can see all the table's metadata. 
        ![Table detail](images/table_detail1.png)
    
    - At the `Data Sample` we can study and filter the extracted data. We can see that some of the reviews are empty - at the moment we are not interested in those. Let’s create a SQL transformation to process and clean the extracted data.
        ![Table detail](images/table_detail2.png)
---

## Step 2: Data Transformation


### Create a Transformation
1. Navigate to `Transformations` > `CREATE TRANSFORMATION`.
    ![Transformations](images/transformations.png)
2. Choose `Snowflake SQL Transformation` 

    ![Snowflake SQL](images/snowflakesql.png)

    Name it `[build][01] Data Cleaning` and click `CREATE TRANSFORMATION`
    ![Snowflake SQL 1](images/snowflakesql1.png)

3. Add the SQL code:

    There are many things we can configure on the Transformation detail page. At the moment we’ll keep it simple. Click `Add new code`.
    ![Snowflake transformation](images/tr_newcode.png)
    
    Enter the following statement and click `SAVE`.

    ```sql
    CREATE OR REPLACE TABLE "aggregated_reviews" AS
    SELECT
        "url",
        "publishedAtDate",
        "stars",
        "name",
        "text",
        'Google Places' AS "reviewSource"
    FROM "apify_reviews"
    WHERE "text" IS NOT NULL AND "text" <> '' AND "text" <> 'text'
    LIMIT 500;
    ```

    ![Snowflake transformation 1](images/tr_code.png)


4. Configure the input and output mappings:
    - The statement reads the table named “apify_reviews” we extracted in the first step and creates a table named “aggregated_reviews”. In Keboola transformation this code is executed in a temporary Transformation schema every time the Transformation is executed. In order to propagate the query results to the main Storage we need to configure an Output Mapping. 

    - The output mapping (together with the input mapping which we’ll configure later, too) provides several functionalities users can use to define incremental processing etc. 

    Click `New Table Output`

    ![Output mapping](images/om1.png)

    Enter `aggregated_reviews` as a Table name. Type `reviews-data-cleaning` to destination bucket name and click `Create new bucket "reviews-data-cleaning"`. Keep other settings unchanged and click `ADD OUTPUT`
    ![Output mapping 2](images/om2a.png)

    Now, because we haven’t used an absolute path to our source table in the query (path that would include the bucket (schema) name) we need to use the Table Input Mapping, too. Click `New Table Input`, select `apify_reviews` as a source and click **ADD INPUT**.
    ![Input mapping](images/im.png)

5. Run the transformation.

    ![run Transformation](images/tr_runa.png)

    After the job is successfully executed you will see new table in the Storage explorer.
    ![Transformation result](images/tr_resulta.png)

---

## Step 3: AI Enrichment
We can see that the “text” of the reviews is in varying language and format. We’ll use Keboola’s Generative AI component to translate the text and process a sentiment analysis and keyword extraction. 

### Step 3 Alternative Route
> The Generative AI Token (provided below) won't be active if you're following this tutorial outside of the Snowflake Build event. In such case - or simply to speed up the process - navigate to **Data Catalogue** and link data with already processed datasets.

![Catalog1](images/catalog1.png)

Locate the shared bucket and click `USE THIS`.

![Catalog2](images/catalog2.png)

Click `LINK`.

![Catalog3](images/catalog3.png)

Now the shared bucket will appear in the storage. **You can continue to Step 4**.

### Standard route - Set Up the Generative AI Component
1. Navigate to `Components` > `Components` > `ADD COMPONENT` and search for `Generative AI` and click `ADD COMPONENT` .
    ![Add component](images/comps_add.png)
2. Enter `[build] Sentiment analysis, Keyword extraction` as a name and click `CREATE CONFIGURATION`
    ![Add component GenAI](images/add_genai.png)

3. Configure the component:
    Click `Open Data Source Configuration settings`
    ![AI 1](images/ai1.png)
    
    Enter the following and click `SAVE`
   - AI Service Provider: Hugging Face
   - API Key: https://share.1password.com/s#bpJveYemf8cIBu2-huue7DaxVjBF4f3dkVAjDeXlg44

    ![AI 2](images/ai2.png)

4. Add a configuration row named `Sentiment and Keywords`.
    
    Click `Add Row` to add a component configuration row.
    ![AI 3](images/ai3.png)

    Enter `Sentiment and Keywords` as a name and click `CREATE`

    ![AI 4](images/ai4.png)

    Now we will configure the component. Lets start with selecting the table we want to work with. Click `New Table Input` and select the `aggregated_reviews` table we created in the previous step. Click `ADD INPUT`.
    ![AI 5](images/ai5a.png)


    Under `Configuration Parameters` click `LIST MODELS`. Keboola will use the previously entered API key to list all models available in the Hugging Face.
    
    Select `Custom Model` and enter the following:
   - Model Endpoint: `https://pnf9wg1qophxwyrh.us-east-1.aws.endpoints.huggingface.cloud`
   - Enter 500 to `Max Tokens`, keep other parameters unchanged.
    ![AI 6](images/ai6.png)
    

#### Configure the Prompt
Scroll down to Prompt Options. In here we enter a prompt which Keboola will call with content from the Input Table. It will be called for every single row from the input table. Use this prompt:
```
Process the below text in 3 ways: 1) If it is not in English, translate it 2) Extract any key words or phrases from the text (maximum 5) 3) Score the sentiment of the translated text on a scale of -1.00 (very negative) to 1.00 (very positive). For example, 'I love this!' should be close to 1.00 and 'I hate this.' should be close to -1.00. Ensure the score accurately reflects the sentiment. Give me response in JSON using the following structure: {"text_in_english": text in english, "keywords": [keywords], "sentiment": calculated score}. Return the JSON only, do not append with the word "json".

Text: """
[[text]] 
"""
```

Notice the `[[text]]` placeholder—this instructs Keboola to replace the placeholder with the value of the `text` column from the input table. 

We can click `TEST PROMPT` to see what the model would return for first couple of rows from our Input Table.

![AI 7](images/ai7.png)

If we are happy with the results we’ll enter `processed_reviews` as a `Destination Storage Table Name`, scroll up and click `SAVE` and then `RUN COMPONENT` to exectue the component job. 

![AI 8](images/ai8.png)
![AI 9](images/ai9a.png)

Keboola will use the selected input table and process each row with the entered prompt using the Hugging Face model. 

It will store the results into a Storage table named processed_reviews which we’ll find in Storage after the Job is successfully executed. This job might take around 10 minutes to complete.

## Step 4: Process LLM response
Navigating to `Storage` we can view the data sample of our new `processed_reviews` table. 
![Python 1](images/python1.png)

We can see the `result_value` is formatted as `Prompt text: {response json}`. We need to parse the individual values from that response json. We'll use Python transformation for that.

### Create a Python Transformation
1. Navigate to `Transformations`, click `CREATE TRANSFORMATION` and select `Python Transformation`
    ![Python 2](images/python2.png)

2. Enter `[build][02] Processed reviews parsing` as a name and click `CREATE TRANSFORMATION`
    ![Python 3](images/python3.png)

3. Click `New Table Input` to add the `processed_reviews` table to the input mapping. 

    ![Python 4](images/python4.png)

    ![Python 5](images/python5.png)

4. Scroll down and click `Add New Code`

    ![Python 6](images/python6.png)

5. Add the following code and click `SAVE`
    ```python
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
    ```

    ![Python 7](images/python7.png)
        
6. Configure **OUTPUT MAPPING**

    The script reads the input table as a CSV file. It also creates two new CSV files - one with parsed sentiment of the review and another that aggregates the counts of each keyword. We need to configure the `output mapping` to make sure the tables are loaded to `Storage` when the Transformation is executed.

    Click `New Table Output`, enter `reviews_parsed.csv` as a **File name**. This is how we named it in our Transformation Code. Select our existing `reviews-data-cleaning` bucket as a Destination bucket. Click `ADD OUTPUT`.
    
    ![Python 8](images/python8a.png)

    Repeat the same for **file name** `keyword_counts.csv`. The Table Output Mapping should now look like this:

    ![Python 10](images/python10a.png)

7. Click **Run Transformation** to execute the job    

    ![Python 11](images/python11.png)

    After the Job finishes successfully we'll see two new tables in our Storage.

    ![Python 12](images/python12.png)

    ![Python 13](images/python13b.png)


## Step 5: Deploy Streamlit Data App
To interact with the data we will use a Streamlit data app. We'll deploy and host that app in Keboola so that we can later share it with our colleagues, too.

1. Navigate to `Components` > `Data Apps` and click `CREATE DATA APP`

    ![App 1](images/app1.png)

    ![App 2](images/app2.png)

2. Enter `London Eye Reviews Analysis` as a Name and click `CREATE DATA APP`

    ![App 3](images/app3.png)

    The app configuration supports many features such as various Authentication options or custom secrets. 
    You can read more about Keboola's data apps here https://help.keboola.com/components/data-apps

3. Configure **Deployment**
    We'll keep it simple now. We'll use an existing app's code that is already available in Github. Enter the following URL to a **Project URL** under Deployment and click `Load Branches`

    URL: `https://github.com/kbcMichal/london_eye_app.git`

    ![App 4](images/app4.png)    

    Keboola automatically loads available branches from the Github repository. Select the `main` branch, `app.py` as a **main entry point** and click `SAVE`.

    ![App 5](images/app5.png)    

4. Deploy the app
    Now we can click `DEPLOY DATA APP`. Keboola will spin a machine, install all the required tools and packages and deploy our Streamlit app. 

    ![App 6](images/app6.png)

    ![App 7](images/app7.png)

    This executed a deployment job. After the job successfully finishes we'll see a new `OPEN DATA APP` button. 

    ![App 8](images/app8.png)

    Your app has a unique URL which is accessible to anyone at the moment because we haven't set any authentication. The app will be set to sleep after 15 minutes of inactivity but will re-deploy anytime someone accessess it again (the re-deploy process takes around one minute). Feel free to share your app to showcase your results!

    ![App 9](images/app9.png)    

## Bonus step: Automate it with a Flow!
To automate the enitre pipeline we have just built we will configure a Flow.

1. Navigate to **Flow**
    ![Flow 1](images/flow1.png) 

2. Click **CREATE FLOW**
    ![Flow 2](images/flow2.png)  

3. Enter `[build] Extract, enrich, deploy app` as a name and click **CREATE FLOW**
    ![Flow 3](images/flow3.png)  

4. Click `Select first step`
    ![Flow 4](images/flow4.png)  

5. First, we'll be executing the extraction of fresh data from our data source. Select the `MySQL` component.
    ![Flow 5](images/flow5.png)  

6. Then select the configuration we created before.
    ![Flow 6](images/flow6.png)  
    ![Flow 7](images/flow7.png)  

7. Click the PLUS icon to add another task to our Flow    
    ![Flow 8](images/flow8.png)  

8. Another step is data transformation. Click `Transformations` and select `SQL Transformation`.
    ![Flow 9](images/flow9.png)  

9. Select the SQL transformation we created.

    ![Flow 10](images/flow10.png)  

    ![Flow 11](images/flow11.png)  

10. Continue adding other steps to build a Flow looking like this:

    ![Flow 12](images/flow12.png)  

11. Click **SAVE**
    
    ![Flow 13](images/flow13.png)  

12. To execute this Flow automatically, we will assign it a **Schedule**. Click `Schedules` and then `CREATE SCHEDULE`     
    
    ![Flow 14](images/flow14.png) 

13. Configure the schedule to execute daily at 8am UTC and click `SET UP SCHEDULE`
    ![Flow 15](images/flow15.png) 

---

Congratulations! You have successfully built and automated your data pipeline on Keboola.


