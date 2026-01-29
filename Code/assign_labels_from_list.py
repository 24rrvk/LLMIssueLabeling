import json, sys, csv, ast, re, os

import transformers, torch


def four_label_prompt_template(title, body):
    prompt_template = f"""The following is the title and body of a GitHub issue report:

'''title''': '''{title}'''
'''body''': '''{body}'''

Assign this issue report the most appropriate of the following labels: bug, feature, question, documentation. Do NOT include any additional information.

"""
    return prompt_template

def find_label(text):
    keywords = ['bug', 'feature', 'question', 'documentation']
    pattern = r'\b(' + '|'.join(keywords) + r')\b'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    unique_matches = list(set(map(str.lower, matches)))
    return unique_matches

def prompt_template(title, body, labels_list):
    labels_string = "["
    for label in labels_list:
        labels_string += label + ", "
    labels_string = labels_string[:-2] + "]"

    prompt_template = f"""The following is the title and body of a GitHub issue report:

'''title''': '''{title}'''
'''body''': '''{body}'''

From ONLY the following LABELS_REFERENCE list provided to you, assign the most appropriate label(s) for this issue report in the form of a Python list (e.g. ['label1', 'label2', 'label3', ...]). Do NOT include any additional information.

LABELS_REFERENCE = {labels_string}
"""
    return prompt_template


def generate_output(pipeline, messages):
    outputs = pipeline(messages, max_new_tokens=256)
    return(outputs[0]["generated_text"][-1])

if __name__ == "__main__":

    MODEL_NAME = sys.argv[1]
    LABELS_FILENAME = sys.argv[2]
    ISSUE_REPORTS_FILE_NAME = sys.argv[3]

    # LLM Implementation in this work which can be modified
    pipeline = transformers.pipeline(
        "text-generation",
        model=MODEL_NAME,
        model_kwargs={"torch_dtype": torch.bfloat16}
    )

    MODEL_NAME = MODEL_NAME.replace("/","_")

    if "train_set" in ISSUE_REPORTS_FILE_NAME:
        OUTFILE = "train_set_labeled_from_list.json"
        OUTPUT_LOG = "label_assigning_from_list_train_set_log.txt"

    elif "test_set" in ISSUE_REPORTS_FILE_NAME:
        OUTFILE = "test_set_labeled_from_list.json"
        OUTPUT_LOG = "label_assigning_from_list_test_set_log.txt"
    
    else:
        print("MUST BE ASSIGNING LABELS TO EITHER TRAIN OR TEST SET!!")
        sys.exit(1)

    with open(f"dataset/{MODEL_NAME}/{ISSUE_REPORTS_FILE_NAME}", "r") as file:
        data = json.load(file)


    labels = []

    with open(LABELS_FILENAME, "r") as labels_file:
        labels_reader = csv.reader(labels_file)

        for line in labels_reader:
            # prompt += line[0] + "\n"
            labels.append(line[0])


    num_projects = len(data)
    cur_project = 1

    output = []
    assigned_labels_counts = {}
    assigned_one_of_four_labels_counts = {
        "bug": 0,
        "feature": 0,
        "documentation": 0,
        "question": 0
    }

    for project, issue_reports in data.items():

        print(f"LABELING ISSUE REPORTS FROM PROJECT {project} ({cur_project} OF {num_projects})")
        cur_project += 1

        num_issue_reports = len(issue_reports)

        for i in range(len(issue_reports)):

            print(f"LABELING ISSUE REPORT {i+1} of {num_issue_reports} (PROJECT {cur_project-1} OF {num_projects})")

            prompt = prompt_template(issue_reports[i]["title"], issue_reports[i]["body"], labels)

            if i == 0:
                print("\n\n\n\nPROMPT\n\n")
                print(prompt)
                print("\n\n\n")

                output.append(prompt)

            messages = [{"role": "user", "content": prompt},]
            raw_output = generate_output(pipeline, messages)["content"]

            valid_output = False
            reading_output = False
            cleaned_output = ""
            for char in raw_output.strip():
                if reading_output:
                    cleaned_output += char
                    try:
                        assigned_labels_raw = ast.literal_eval(cleaned_output)
                        if isinstance(assigned_labels_raw, list):
                            print("IT IS A LIST!!!!!")
                            output.append(f"{project}/{issue_reports[i]['number']} - IT IS A LIST!!!!")
                            valid_output = True
                            break
                    except:
                        continue
                else:
                    if char == "[":
                        cleaned_output += char
                        reading_output = True

            if valid_output:

                assigned_labels_cleaned = []

                for label in assigned_labels_raw:
                    if label not in labels:
                        print(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                        output.append(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                    else:
                        assigned_labels_cleaned.append(label)

                        if label not in assigned_labels_counts:
                            assigned_labels_counts[label] = 0
                        assigned_labels_counts[label] += 1

                print(assigned_labels_cleaned)
                output.append(assigned_labels_cleaned)

                data[project][i]["assigned_labels_from_catalog"] = assigned_labels_cleaned

            else:
                print("MODEL DID NOT OUTPUT A LIST!!!!")
                print(raw_output)

                output.append(f"{project}/{issue_reports[i]['number']} - MODEL DID NOT OUTPUT A LIST!!")
                output.append(raw_output)
                data[project][i]["assigned_labels_from_catalog"] = []

            messages = [{"role": "user", "content": four_label_prompt_template(issue_reports[i]["title"], issue_reports[i]["body"])},]
            raw_output = generate_output(pipeline, messages)["content"].strip()
            
            outputted_labels = find_label(raw_output)

            if len(outputted_labels) == 1:
                print(outputted_labels[0])
                output.append(outputted_labels[0])
                data[project][i]["assigned_one_of_four_label"] = outputted_labels[0]
                assigned_one_of_four_labels_counts[outputted_labels[0]] += 1

            else:
                print("COULD NOT FIND LABELS!!!!")
                print(raw_output)
                output.append("COULD NOT FIND LABELS!!!!!!!")
                output.append(raw_output)
                data[project][i]["assigned_one_of_four_label"] = ""

    sorted_assigned_labels = sorted(assigned_labels_counts.items(), key= lambda x:x[1], reverse=True)

    outfolder_path = f"results/{MODEL_NAME}"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/label_assignment_counts.txt", "w") as outfile:
        outfile.write("ONE OF FOUR LABEL COUNTS\n")
        for label, count in assigned_one_of_four_labels_counts.items():
            outfile.write(f"{label},{count}\n")

        outfile.write("\n\nASSIGNED LABELS FROM DERIVED LIST COUNTS\n")
        for label, count in sorted_assigned_labels:
            outfile.write(f"{label},{count}\n")

    with open(f"dataset/{MODEL_NAME}/{OUTFILE}", "w") as outfile:
        json.dump(data, outfile, indent=4)

    outfolder_path = f"output_logs/{MODEL_NAME}"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/{OUTPUT_LOG}", "w") as outfile:
        for item in output:
            outfile.write(f"{item}\n")

    
            