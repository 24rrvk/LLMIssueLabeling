import json, sys, ast, os

import transformers, torch


def prompt_template(project, title, body):
    outstring = f"""You are a project maintainer for the GitHub repository {project}.

The following is the title and body of an issue report that has been submitted to the repository's issue tracking system:

Title: '''{title}'''
Body: '''{body}'''

Your task is to assign reusable labels to this issue report. These labels should:
1. Categorize the type of issue
2. Describe its domain
3. Be reusable across similar issues -- do not use labels that are overly specific or context-bound

Strictly avoid labels that:
- Refer to hardware or platform-specific terms (e.g., 'aarch64', 'sparc32', 'aix')
- Refer to software configuration details (e.g., 'f128-support', 'nightly-build')
- Refer to versions, filenames, or environment setups
- Are status/process-related (e.g., 'needs-triage', 'help-wanted', 'duplicate')

Only output your assigned labels as a valid Python list (e.g., ['label1', 'label2', 'label3', ...]) with no extra explanation.
"""
    return outstring

def generate_output(pipeline, messages):
    outputs = pipeline(messages, max_new_tokens=256)
    return(outputs[0]["generated_text"][-1])

if __name__ == "__main__":

    MODEL_NAME = sys.argv[1]

    # LLM Implementation in this work. You can use your own.
    pipeline = transformers.pipeline(
        "text-generation",
        model=MODEL_NAME,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="cuda:2"
    )

    MODEL_NAME = MODEL_NAME.replace("/","_")

    with open(f"dataset/{MODEL_NAME}/train_set_cleaned.json", "r") as issues_file:
        data = json.load(issues_file)

    label_catalog = {}
    output = []

    num_projects = len(data)
    cur_project = 1

    for project, issue_reports in data.items():

        print(f"LABELING ISSUE REPORTS FROM PROJECT {project} ({cur_project} OF {num_projects})")
        cur_project += 1

        num_issue_reports = len(issue_reports)        

        for i in range(len(issue_reports)):

            print(f"LABELING ISSUE REPORT {i+1} of {num_issue_reports} (PROJECT {cur_project-1} OF {num_projects})")

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

            messages = [{"role": "user", "content": prompt_template(project, title, body)},]

            raw_output = generate_output(pipeline, messages)["content"]

            str_list = ""
            reading_list = False
            for char in raw_output:
                if reading_list:
                    str_list += char
                    if char == "]":
                        break
                elif char == "[" and reading_list == False:
                    reading_list = True
                    str_list += char

                
            try:
                assigned_labels_raw = ast.literal_eval(str_list)
                print("IT IS A LIST!!!")
                output.append(f"{project}/{issue_reports[i]['number']} - IT IS A LIST!!!!!")

                assigned_labels = []

                for label in assigned_labels_raw:
                    label = label.lower()
                    label = label.replace(" ", "-")
                    label = label.replace("_", "-")
                    if label in label_catalog:
                        label_catalog[label] += 1
                    else:
                        label_catalog[label] = 1
                    assigned_labels.append(label)

                print(assigned_labels)
                output.append(assigned_labels)

                data[project][i]["assigned_labels"] = assigned_labels

            except:
                print("MODEL DID NOT OUTPUT A LIST!!!!")
                print(raw_output)

                output.append(f"{project}/{issue_reports[i]['number']} - MODEL DID NOT OUTPUT A LIST!!")
                output.append(raw_output)
                data[project][i]["assigned_labels"] = []



    sorted_catalog = sorted(label_catalog.items(), key= lambda x:x[1], reverse=True)

    outfolder_path = f"label_generation_results/{MODEL_NAME}"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/label_counts.csv", "w") as outfile:
        outfile.write("Label,Count\n")
        for label, count in sorted_catalog:
            if "," not in label:
                outfile.write(f"{label},{count}\n")

    with open(f"dataset/{MODEL_NAME}/train_set_labeled.json", "w") as outfile:
        json.dump(data, outfile, indent=4)

    outfolder_path = f"output_logs/{MODEL_NAME}"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/label_generation_log.txt", "w") as outfile:
        for item in output:
            outfile.write(f"{item}\n")            