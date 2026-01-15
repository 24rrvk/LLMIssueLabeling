import requests, json, re, os, sys

if __name__ == "__main__":
    EVALUATOR_URL = "http://localhost:11434/api/generate"

    LLM_TO_EVALUATE = sys.argv[1]
    LABELS_TO_EVALUATE = sys.argv[2]
    LABELS_TO_EVALUATE_KEY = sys.argv[3]
    EVALUATION_RESULT_KEY = "evaluation_of_" + LABELS_TO_EVALUATE_KEY

    if "train_set" in LABELS_TO_EVALUATE:
        RAW_ISSUE_REPORTS = "train_set_raw.json"
        EVAL_OUTFILE = "train_set_evaluated.json"
        STATS_OUTFILE = f"train_set_{EVALUATION_RESULT_KEY}_stats.json"

    elif "test_set" in LABELS_TO_EVALUATE:
        RAW_ISSUE_REPORTS = "test_set_raw.json"
        EVAL_OUTFILE = "test_set_evaluated.json"
        STATS_OUTFILE = f"test_set_{EVALUATION_RESULT_KEY}_stats.json"

    else:
        print("MUST BE EVALUATING LABELS ASSIGNED TO EITHER THE TRAIN OR TEST SET")
        sys.exit(1)


    with open(f"dataset/{LLM_TO_EVALUATE}/{LABELS_TO_EVALUATE}", "r") as file:
        data = json.load(file)

    with open(f"dataset/{RAW_ISSUE_REPORTS}", "r") as file:
        raw_data = json.load(file) 

    prompt = "You are a helpful AI assistant that evaluates if labels accurately reflect a GitHub issue report based on it's title, body, and patches made to the repository to resolve the issue.\n\n"
    system_prompt_len = len(prompt)

    num_projects = len(data)
    cur_project = 1
    cur_issue_report = 0

    num_good_labels = 0
    num_bad_labels = 0
    num_invalid_outputs = 0

    

    for project, issue_reports in data.items():

        print(f"EVALUATING LABELINGS OF ISSUE REPORT FROM PROJECT {project} ({cur_project} OF {num_projects})")
        cur_project += 1

        num_issue_reports = len(issue_reports)

        for i in range(len(issue_reports)):

            cur_issue_report += 1
            if cur_issue_report > 0:
                print(f"EVALUATING LABELS FROM ISSUE REPORT {i + 1} OF {num_issue_reports} (PROJECT {cur_project} OF {num_projects})")

                title = ""
                body = ""

                if raw_data[project][i]["title"] != None:
                    title = raw_data[project][i]["title"]

                if raw_data[project][i]["body"] != None:
                    body = raw_data[project][i]["body"]

                prompt = prompt[:system_prompt_len]
                prompt += "The following is the title and body of the issue report: \n\n"
                prompt += "'''title''': '''" + title + "'''\n'''body''': '''" + body + "'''\n\n"
                prompt += "The following were the patches that resolved this issue: \n\n"

                for closing_commit in issue_reports[i]["closing_commits"]:
                    for j in range(len(closing_commit["patches"])):
                        prompt += f"Patch {j+1}\n" + closing_commit["patches"][j] + "\n\n"

                issue_report_prompt_len = len(prompt)

                evaluation_of_assigned_labels_from_catalog = {}

                for label in issue_reports[i][LABELS_TO_EVALUATE_KEY]:

                    # num_labels_eval += 1
                    # print(f"EVALUATION LABEL {num_labels_eval} OF {total_labels_to_eval}")

                    prompt = prompt[:issue_report_prompt_len]

                    prompt += "The following label was assigned to this issue report: " + label + "\n\n"
                    prompt += "Does this label accurately reflect this issue report based on its title, body, and patches made to the repository to resolve this issue? "
                    prompt += "If yes, output 1. If no, output 0."

                    request = {
                        "model": "deepseek-r1:70b",
                        "prompt": prompt,
                        "stream": False
                    }

                    response = requests.post(EVALUATOR_URL, json=request)

                    if response.json()["response"][-1] == "0":
                        num_bad_labels += 1
                        print(f"{label} IS NOT A GOOD LABEL FOR ISSUE REPORT {project}/{issue_reports[i]['number']}")
                        evaluation_of_assigned_labels_from_catalog[label] = {
                            "evaluation" : "0",
                            "reason": response.json()["response"]
                        }
                    elif response.json()["response"][-1] == "1":
                        num_good_labels += 1
                        print(f"{label} IS A GOOD LABEL FOR ISSUE REPORT {project}/{issue_reports[i]['number']}")
                        evaluation_of_assigned_labels_from_catalog[label] = {
                            "evaluation" : "1",
                            "reason": response.json()["response"]
                        }
                    else:
                        print("INVALID OUTPUT")
                        output = re.search(r"</think>\s*(.*)", response.json()["response"], re.DOTALL)
                        if output:
                            print(output.group(1).strip())
                        else:
                            print(response.json()["response"])
                        num_invalid_outputs += 1
                        evaluation_of_assigned_labels_from_catalog[label] = {
                            "evaluation" : "N/A",
                            "reason": response.json()["response"]
                        }

                data[project][i][EVALUATION_RESULT_KEY] = evaluation_of_assigned_labels_from_catalog

                with open(f"dataset/{LLM_TO_EVALUATE}/{EVAL_OUTFILE}", "w") as outfile:
                    json.dump(data, outfile, indent=4)

                if num_good_labels + num_bad_labels != 0:
                    with open(f"results/{LLM_TO_EVALUATE}/{STATS_OUTFILE}", "w") as outfile:
                        accuracy = num_good_labels / (num_good_labels + num_bad_labels)
                        outfile.write(f"NUM GOOD LABELS: {num_good_labels}\n")
                        outfile.write(f"NUM BAD LABELS: {num_bad_labels}\n")
                        outfile.write(f"NUM INVALID OUTPUTS: {num_invalid_outputs}\n")
                        outfile.write(f"ACCURACY: {accuracy}")