import faiss, json, csv, ast, sys, os
import numpy as np
from sentence_transformers import SentenceTransformer

import transformers, torch


def load_json_file(file_name):
    with open(file_name, "r") as file:
        data = json.load(file)
    return data

def generate_output(pipeline, messages):
    outputs = pipeline(messages, max_new_tokens=256)
    return(outputs[0]["generated_text"][-1])

if __name__ == "__main__":

    ISSUES_TO_RETRIEVE = int(sys.argv[1])
    LLM_TO_TEST = sys.argv[2]
    LLM_TO_TEST = LLM_TO_TEST.replace("/", "_")
    UNSEEN_ISSUE_REPORTS = "test_set_cleaned.json"

    FOLDER_NAME = "dataset/"

    RAG_DB = "train_set_cleaned.json"
    FAISS_INDEX = "train_set_faiss_index.bin"
    ISSUE_REPORT_MAP = "train_set_mappings.json"

    EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

    rag_db = load_json_file(f"{FOLDER_NAME}{LLM_TO_TEST}/{RAG_DB}")
    unseen_issue_reports = load_json_file(f"{FOLDER_NAME}{LLM_TO_TEST}/{UNSEEN_ISSUE_REPORTS}")
    index = faiss.read_index(f"{FOLDER_NAME}{FAISS_INDEX}")
    issue_report_map = load_json_file(f"{FOLDER_NAME}{ISSUE_REPORT_MAP}")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    LLM_TO_TEST = LLM_TO_TEST.replace("_", "/")

    # LLM Implementation in this work which can be modified
    pipeline = transformers.pipeline(
        "text-generation",
        model=LLM_TO_TEST,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="cuda:6"
    )

    prompt = "You are a helpful AI assistant for labeling GitHub issue reports.\n\n"
    system_prompt_len = len(prompt)

    num_projects = len(unseen_issue_reports)
    cur_project = 1

    output = []

    for project, issue_reports in unseen_issue_reports.items():

        print(f"LABELING ISSUE REPORTS FROM PROJECT {project} ({cur_project} OF {num_projects})")
        cur_project += 1

        num_issue_reports = len(issue_reports)

        for i in range(len(issue_reports)):

            print(f"{ISSUES_TO_RETRIEVE} (LABELS AND ISSUE REPORTS) - LABELING ISSUE REPORT {i+1} of {num_issue_reports} (PROJECT {cur_project-1} OF {num_projects})")

            prompt = prompt[:system_prompt_len]

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

            retrieved_issue_reports = []
            label_options = []
            for k, j in enumerate(indices[0]):
                retrieved_project, issue_report_index, labels = issue_report_map[j]

                retrieved_title = ""
                retrieved_body = ""

                if rag_db[retrieved_project][issue_report_index]["title"] != None:
                    retrieved_title = rag_db[retrieved_project][issue_report_index]["title"]

                if rag_db[retrieved_project][issue_report_index]["body"] != None:
                    retrieved_title = rag_db[retrieved_project][issue_report_index]["body"]
                
                retrieved_issue_reports.append((retrieved_title, retrieved_body, labels))

                for label in labels:
                    if label not in label_options:
                        label_options.append(label)

            labels_string = "["
            for label in label_options:
                labels_string += label + ", "
            labels_string = labels_string[:-2] + "]"

            prompt += "The following is a list of labels for GitHub issue reports:\n\n"
            prompt += "LABELS_LIST = " + labels_string + "\n\n"
            prompt += "Assign the most appropriate label(s) from LABELS_LIST to GitHub issue reports based on their title and body.\n\n"

            for j in range(len(retrieved_issue_reports)):

                prompt += "'''title''': '''" + retrieved_issue_reports[j][0] + "'''\n'''body''': '''" + retrieved_issue_reports[j][1] + "'''\n\n" # + "<|eot_id|>\n\n"
                prompt += "Labels: " + str(retrieved_issue_reports[j][2])

            prompt += "'''title''': '''" + issue_reports[i]['title'] + "'''\n'''body''': '''" + issue_reports[i]['body'] + "'''\n\n" # + "<|eot_id|>\n\n"
            prompt += "Labels: "

            print(label_options)
            output.append(label_options)

            if i == 0:
                print("\n\n\n\nPROMPT\n\n")
                print(prompt)
                print("\n\n\n")

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
                    if label not in label_options:
                        print(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                        output.append(f"MODEL PUT A LABEL NOT IN THE LIST: {label}")
                    else:
                        assigned_labels_cleaned.append(label)

                print(assigned_labels_cleaned)
                output.append(assigned_labels_cleaned)

                unseen_issue_reports[project][i][f"assigned_labels_from_RAG_labeled_issue_reports_k={ISSUES_TO_RETRIEVE}"] = assigned_labels_cleaned

            else:
                print("MODEL DID NOT OUTPUT A LIST!!!!")
                print(raw_output)

                output.append(f"{project}/{issue_reports[i]['number']} - MODEL DID NOT OUTPUT A LIST!!")
                output.append(raw_output)
                unseen_issue_reports[project][i][f"assigned_labels_from_RAG_labeled_issue_reports_k={ISSUES_TO_RETRIEVE}"] = []


    LLM_TO_TEST = LLM_TO_TEST.replace("/", "_")
                
    with open(f"{FOLDER_NAME}{LLM_TO_TEST}/{UNSEEN_ISSUE_REPORTS[:-12]}RAG_labeled_issue_reports.json", "w") as outfile:
        json.dump(unseen_issue_reports, outfile, indent=4)

    outfolder_path = f"output_logs/{LLM_TO_TEST}/output_logs_RAG_labeled_issue_reports"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/k={ISSUES_TO_RETRIEVE}.txt", "w") as outfile:
        for item in output:
            outfile.write(f"{item}\n")


