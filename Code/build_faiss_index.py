import faiss, json, sys
import numpy as np
from sentence_transformers import SentenceTransformer

if __name__ == "__main__":

    LLM = sys.argv[1]

    FOLDER = "dataset/"

    LABELS_FILE = "train_set_evaluated.json"

    print("LOADING DATA")

    with open(f"{FOLDER}{LLM}/{LABELS_FILE}", "r") as file:
        data = json.load(file)

    issue_report_map = []
    issue_report_text = []

    invalid_output_counts = {"good": 0, "bad": 0}
    invalid_output_total = 0

    for project, issue_reports in data.items():
        for i in range(len(issue_reports)):

            evaluated_good_labels = []

            for label, eval in issue_reports[i]["evaluation_of_assigned_labels_from_catalog"].items():
                if eval["evaluation"] == "1":
                    evaluated_good_labels.append(label)
                elif eval["evaluation"] == "N/A":
                    invalid_output_total += 1
                    for char in reversed(eval["reason"]):
                        if char == "1":
                            evaluated_good_labels.append(label)
                            invalid_output_counts["good"] += 1
                            break
                        elif char == "0":
                            invalid_output_counts["bad"] += 1
                            break


            issue_report_map.append((project, i, evaluated_good_labels))

            title = ""
            body = ""

            if issue_reports[i]["title"] != None:
                title = issue_reports[i]["title"]
            else:
                data[project][i]["title"] = ""

            if issue_reports[i]["body"] != None:
                body = issue_reports[i]["body"]
            else:
                data[project][i]["body"] = ""

            issue_report_text.append(f"{title} - {body}")

    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    print("DATA LOADED.. EMBEDDING DATA")

    embeddings = model.encode(issue_report_text, normalize_embeddings=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    print("DATA EMBEDDED.. SAVING EMBEDDINGS")

    faiss.write_index(index, f"{FOLDER}{LABELS_FILE[:-14]}faiss_index.bin")

    print("EMBEDDINGS SAVED.. SAVING MAPPINGS")

    with open(f"{FOLDER}{LABELS_FILE[:-14]}mappings.json" , "w") as outfile:
        json.dump(issue_report_map, outfile, indent=4)

    print("MAPPINGS SAVED.. WORK DONE!!!")
