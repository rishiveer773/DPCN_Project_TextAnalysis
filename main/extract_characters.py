import json
import pandas as pd
import re
import os

# --- 1. Helper Function for Character Extraction ---
def extract_characters_from_text(text, master_character_list):
    """Finds characters from the master list present in the text."""
    found_characters = set()
    normalized_text = text.lower()
    
    for char_name in master_character_list:
        # Simple regex to ensure we match whole words (\b) and escape special chars
        escaped_name = re.escape(char_name)
        if re.search(r'\b' + escaped_name + r'\b', normalized_text, re.IGNORECASE):
            found_characters.add(char_name)
            
    return list(found_characters)

# -----------------------------------------------
# 2. Load Master Character List
# -----------------------------------------------
try:
    with open('characters.json', 'r', encoding='utf-8') as f:
        characters_data = json.load(f)
    
    # Create a master list of character names (normalized for search)
    master_char_names = [char['name'].strip().lower() for char in characters_data]
    print(f"Loaded {len(master_char_names)} unique character names.")
except FileNotFoundError:
    print("Error: 'characters.json' not found. Cannot proceed without character list.")
    exit()

# -----------------------------------------------
# 3. Data Extraction and Structuring
# -----------------------------------------------

final_dataset = []

# --- A. Process All Kanda Files ---

# Map the Kanda filename prefix to the full Kanda name for the 'Kanda' column
kanda_map = {
    'bala': 'Bala Kanda', 
    'ayodhya': 'Ayodhya Kanda', 
    'aranya': 'Aranya Kanda', 
    'kishkindha': 'Kishkindha Kanda', 
    'sundara': 'Sundara Kanda', 
    'yuddha': 'Yuddha Kanda', 
    'uttara': 'Uttara Kanda'
}

# Iterate over the directory to find relevant Kanda files
for prefix, kanda_name in kanda_map.items():
    file_name = f"{prefix}.json"
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            events = data.get('points', [])
            
            for event in events:
                topic = event.get('topic', 'N/A')
                content = event.get('content', '')
                location = event.get('location', 'N/A')
                
                text_for_search = topic + " " + content
                involved_characters = extract_characters_from_text(text_for_search, master_char_names)
                
                final_dataset.append({
                    'Kanda': kanda_name,
                    'Event_ID': f"{kanda_name.split()[0].upper()}_{event.get('no', 'N/A')}",
                    'Event_Name': topic,
                    'Location': location.capitalize() if location != 'N/A' else location,
                    'Characters_Involved': '; '.join(involved_characters),
                    'Detailed_Content': content
                })
            print(f"Successfully processed {len(events)} events from {file_name}.")
            
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    else:
        print(f"Warning: '{file_name}' not found. Skipping.")


# --- B. Process Prior Context Events (referencestory.json) ---
try:
    with open('referencestory.json', 'r', encoding='utf-8') as f:
        ref_data = json.load(f)
    
    for i, story in enumerate(ref_data):
        name = story.get('name', f"Story_{i+1}")
        about = story.get('about', '')
        
        involved_characters = extract_characters_from_text(about, master_char_names)
        
        final_dataset.append({
            'Kanda': 'Prior_Context',
            'Event_ID': f"CONTEXT_{i+1}",
            'Event_Name': name,
            'Location': 'N/A',
            'Characters_Involved': '; '.join(involved_characters),
            'Detailed_Content': about
        })
    print(f"Successfully processed {len(ref_data)} events from 'referencestory.json'.")

except FileNotFoundError:
    print("Warning: 'referencestory.json' not found. Skipping.")

# -----------------------------------------------
# 4. Save the Final Dataset to CSV
# -----------------------------------------------

output_file = 'reference_dataset.csv'
if final_dataset:
    # Ensure correct Kanda order for time series analysis
    kanda_order = ['Prior_Context', 'Bala Kanda', 'Ayodhya Kanda', 'Aranya Kanda', 'Kishkindha Kanda', 'Sundara Kanda', 'Yuddha Kanda', 'Uttara Kanda']
    
    df = pd.DataFrame(final_dataset)
    df['Kanda'] = pd.Categorical(df['Kanda'], categories=kanda_order, ordered=True)
    df = df.sort_values('Kanda').reset_index(drop=True)
    
    df.to_csv(output_file, index=False)
    print(f"\nFinal dataset saved successfully to '{output_file}' with {len(df)} total events, correctly ordered by Kanda.")
else:
    print("\nNo data was processed. Output file not created.")