import faiss, json, csv, ast, sys, os
import numpy as np
from sentence_transformers import SentenceTransformer

import transformers, torch


def load_json_file(file_name):
    with open(file_name, "r") as file:
        data = json.load(file)
    return data


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

    ISSUES_TO_RETRIEVE = int(sys.argv[1])
    LLM_TO_TEST = sys.argv[2]
    UNSEEN_ISSUE_REPORTS = sys.argv[3]

    FOLDER_NAME = "dataset/"
    
    FAISS_INDEX = "train_set_faiss_index.bin"
    ISSUE_REPORT_MAP = "train_set_mappings.json"

    EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"


    unseen_issue_reports = load_json_file(f"{FOLDER_NAME}{LLM_TO_TEST}/{UNSEEN_ISSUE_REPORTS}")
    index = faiss.read_index(f"{FOLDER_NAME}{FAISS_INDEX}")
    issue_report_map = load_json_file(f"{FOLDER_NAME}{ISSUE_REPORT_MAP}")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    LLM_TO_TEST = LLM_TO_TEST.replace("_", "/")

    pipeline = transformers.pipeline(
        "text-generation",
        model=LLM_TO_TEST,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="cuda:6"
    )


    num_projects = len(unseen_issue_reports)
    cur_project = 1

    output = []

    for project, issue_reports in unseen_issue_reports.items():

        print(f"LABELING ISSUE REPORTS FROM PROJECT {project} ({cur_project} OF {num_projects})")
        
        num_issue_reports = len(issue_reports)

        for i in range(len(issue_reports)):

            print(f"{ISSUES_TO_RETRIEVE} (LABELS ONLY) - LABELING ISSUE REPORT {i+1} of {num_issue_reports} (PROJECT {cur_project} OF {num_projects})")

            title = ""
            body = ""

            if issue_reports[i]["title"] != None:
                title = issue_reports[i]["title"]
            else:
                unseen_issue_reports[project][i]["title"] = ""

            if issue_reports[i]["body"] != None:
                body = issue_reports[i]["body"]
            else:
                unseen_issue_reports[project][i]["body"] = ""

            issue_report = title + " - " + body
            embedded_issue_report = model.encode([issue_report], normalize_embeddings=True)
            distances, indices = index.search(embedded_issue_report, ISSUES_TO_RETRIEVE)

            label_options = []
            for k, j in enumerate(indices[0]):
                retrieved_project, issue_report_index, labels = issue_report_map[j]

                for label in labels:
                    if label not in label_options:
                        label_options.append(label)

            print(label_options)
            output.append(label_options)
            unseen_issue_reports[project][i][f"RAG_label_options_k={ISSUES_TO_RETRIEVE}"] = label_options

            prompt = prompt_template(title, body, label_options)

            if i == 0:
                print("\n\n\n\nPROMPT\n\n")
                print(prompt)
                print("\n\n\n")

            messages = [{"role": "user", "content": prompt},]
            raw_output = generate_output(pipeline, messages)["content"]

            valid_output = False
            cleaned_output = ""
            for char in raw_output.strip():
                cleaned_output += char
                try:
                    assigned_labels_raw = ast.literal_eval(cleaned_output)
                    print("IT IS A LIST!!!!!")
                    output.append(f"{project}/{issue_reports[i]['number']} - IT IS A LIST!!!!")
                    valid_output = True
                    break
                except:
                    continue

            if valid_output:

                assigned_labels_cleaned = []

                for label in assigned_labels_raw:
                    if label not in label_options:
                        print(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                        output.append(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                    else:
                        assigned_labels_cleaned.append(label)

                print(assigned_labels_cleaned)
                output.append(assigned_labels_cleaned)

                unseen_issue_reports[project][i][f"assigned_labels_from_RAG_labels_only_k={ISSUES_TO_RETRIEVE}"] = assigned_labels_cleaned

            else:
                print("MODEL DID NOT OUTPUT A LIST!!!!")
                print(raw_output)

                output.append(f"{project}/{issue_reports[i]['number']} - MODEL DID NOT OUTPUT A LIST!!")
                output.append(raw_output)
                unseen_issue_reports[project][i][f"assigned_labels_from_RAG_labels_only_k={ISSUES_TO_RETRIEVE}"] = []

        cur_project += 1

    LLM_TO_TEST = LLM_TO_TEST.replace("/", "_")
                
    with open(f"{FOLDER_NAME}{LLM_TO_TEST}/{UNSEEN_ISSUE_REPORTS}", "w") as outfile:
        json.dump(unseen_issue_reports, outfile, indent=4)

    outfolder_path = f"output_logs/{LLM_TO_TEST}/output_logs_RAG_labels_only"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/k={ISSUES_TO_RETRIEVE}.txt", "w") as outfile:
        for item in output:
            outfile.write(f"{item}\n")

