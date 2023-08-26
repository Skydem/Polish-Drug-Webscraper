
import os
import json
import concurrent.futures
from itertools import islice
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from google.cloud import translate_v2 as translate

def setup_environment():
    """Set up necessary environment variables."""
    # In a real-world application, use environment variables or a configuration file
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    pass

def translate_text(text):
    """Translate the given text from Polish to English using Google Cloud Translate."""
    translate_client = translate.Client()
    try:
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        result = translate_client.translate(
            text, target_language="en", source_language="pl"
        )
        return result["translatedText"]
    except Exception as e:
        print(f"Error translating text: {text}. Error: {e}")
        return text  # Return original text if translation fails

def fetch_ingredients_for_chunk(chunk):
    """Helper function to fetch ingredients for a chunk of the dictionary."""
    driver = create_new_browser()
    for key in chunk:
        try:
            driver.get(chunk[key]["url"])
            drug_used = driver.find_element(By.CSS_SELECTOR, "a.color")
            drug_name = drug_used.text
            if "+" in drug_name:
                parts = drug_name.split(" + ")
                chunk[key]["ingredients_en"]["0"] = translate_text(parts[0])
                chunk[key]["ingredients_en"]["1"] = translate_text(parts[1])
                chunk[key]["ingredients_pl"]["0"] = parts[0]
                chunk[key]["ingredients_pl"]["1"] = parts[1]
            elif drug_name in ["preparat złożony", "preparat ziołowy"]:
                continue
        except Exception as e:
            print(f"Error fetching ingredients for {key}. Error: {e}")
    driver.quit()
    return chunk


def get_ingredients(part_dict):
    """Fetch ingredients for a given set of drugs using multi-threading."""
    # Create a single browser instance for the main thread to reduce overhead
    driver = create_new_browser()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Split the dictionary into smaller chunks for multi-threading
        chunk_size = len(part_dict) // 10  # This can be adjusted based on the number of threads you want
        dict_chunks = [dict(islice(part_dict.items(), i, i + chunk_size)) for i in range(0, len(part_dict), chunk_size)]
        
        # Use multi-threading to fetch ingredients for each chunk
        results = list(executor.map(fetch_ingredients_for_chunk, dict_chunks))
        
    # Merge the results back into the main dictionary
    for chunk in results:
        part_dict.update(chunk)
    driver.quit()  # Close the browser instance after finishing all operations
    return part_dict


def load_json_list(file_path):
    """Load the JSON list from the given file path with UTF-8 encoding."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data



def make_json_list():
    """Generate or update the list.json file. Placeholder logic for demonstration."""
    data = {"example": {"url": "http://example.com", "ingredients_en": {}, "ingredients_pl": {}}}
    with open("list.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    pass


    setup_environment()
    make_json_list()

    # Rest of the main method will be completed later


def create_new_browser():
    """Create a new headless Firefox browser instance."""
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    return driver

def main():
    setup_environment()
    make_json_list()
    data = load_json_list("list.json")
    get_ingredients(data)


if __name__ == "__main__":
    main()