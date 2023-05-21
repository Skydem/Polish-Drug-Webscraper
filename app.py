from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import json
from itertools import islice
import concurrent.futures
import os

# global variabls
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:/_INZYNIERKA_STUFF/testy/sellenium/inzynierka-387317-b6c75eaf8bb3.json"
complete_dict = {}

def create_new_browser():
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    return driver

def translate_text(text):
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate_client.translate(
        text, target_language="en", source_language="pl"
    )
    return result["translatedText"]

def get_ingredients(part_dict):
    # create new headless browser
    driver = create_new_browser()
    browser_pid = driver.service.process.pid
    print("## New browser with pid: {}".format(browser_pid))

    # from dict passed go to url and get ingredients
    for key in part_dict:
        print(browser_pid, "Drug: ", part_dict[key]["drug_name_pl"], key)

        # go to url
        driver.get(part_dict[key]["url"])

        # find igredients
        drug_used = driver.find_element(By.CSS_SELECTOR, "a.color")

        drug_name = drug_used.text

        # if there are more than one ingredient, split it
        if "+" in drug_name:
            parts = drug_name.split(" + ")
            part_dict[key]["ingredients_en"]["0"] = translate_text(parts[0])
            part_dict[key]["ingredients_en"]["1"] = translate_text(parts[1])
            part_dict[key]["ingredients_pl"]["0"] = parts[0]
            part_dict[key]["ingredients_pl"]["1"] = parts[1]
        elif drug_name in ["preparat złożony", "preparat ziołowy"]:
            print("passs")
        else:
            part_dict[key]["ingredients_en"]["0"] = translate_text(drug_name)
            part_dict[key]["ingredients_pl"]["0"] = drug_name

    with open("tmp/lists/list{}.json".format(browser_pid), "w") as outfile:
        outfile.write(json.dumps(part_dict, indent=4))

    # free memory
    del part_dict
    print("## End of browser with pid {}. Quitting..".format(browser_pid))
    driver.quit()

def chunks(data, size=100):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}

def get_drugs_list(letter_array):
    # create browser
    driver = create_new_browser()

    index = 0
    # iter through letters and get drug list
    for el in letter_array:
        print("-- Letter: {}".format(el))
        driver.get("https://www.mp.pl/pacjent/leki/items.html?letter={}".format(el))
        elements = driver.find_elements(By.CSS_SELECTOR, ".drug-list li a")
        for element in elements:
            result = {
                index: {
                    "drug_name_pl": element.text,
                    "url": element.get_attribute("href"),
                    "ingredients_pl": {},
                    "ingredients_en": {},
                }
            }
            complete_dict.update(result)
            index += 1
        with open("list.json", "w") as outfile:
            outfile.write(json.dumps(complete_dict, indent=2))
    driver.quit()

def make_json_list():
    letter_array = [
        2,
        4,
        5,
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "Ś",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "Ż",
    ]

    # get list of drugs
    get_drugs_list(letter_array)



def main():
    # make_json_list()

    # load already prepared json list to complete_dict
    file_path = "list.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    complete_dict = data

    # create array of dicts that are equally split
    dicts_array = []
    for item in chunks(complete_dict, 1000):
        dicts_array.append(item)

    # delete complete_dict for memory saving
    del complete_dict

    # paraller execute get_ingredients for dictonaries
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_ingredients, dictonary) for dictonary in dicts_array]
        del dicts_array
        concurrent.futures.wait(futures)

    print("##### end of wait")

    # read lists prepared from browsers
    lists_dir = "tmp/lists"
    complete_list = {}
    for filename in os.scandir(lists_dir):
        if filename.is_file():
            with open(filename, "r") as file:
                data = json.load(file)
            os.remove(filename)
            complete_list.update(data)

    # convert dictonary to json 
    json_list = json.dumps(complete_list, indent=4, sort_keys=True)
    with open("json_data.json", "w", encoding="utf-8") as json_save:
        json_save.write(json_list)
    print("Saved json to file. Quitting.")


if __name__ == "__main__":
    main()
