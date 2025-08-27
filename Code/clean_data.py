import json, re, sys, os
import torch, transformers


def get_content_to_summarize_type(text):
    outstring = f"""Is the following a code snippet, shell script, or output log:
    
    ```{text}```

    Respond **only** with a single number:
    - **1** if it is a code snippet
    - **2** if it is a shell script
    - **3** if it is an output log

    Do **not** provide any explanation or additional information.
    """
    return outstring

def summarize_shell_script_prompt_template(shell_script):
    outstring = f"""Concisely summarize the following shell script: 
    
    ```{shell_script}```
    
    Do **not** provide any suggestions for modifications or improvements."""

    return outstring


def summarize_output_log_prompt_template(output_log):
    outstring = f"""Concisely summarize the following output log: 
    
    ```{output_log}```
    
    Do **not** suggest solutions, fixes, or workarounds. Only summarize what is observed in the log."""

    return outstring

def summarize_code_snippet_prompt_template(code_snippet):

    outstring = f"""Concisely summarize the following code snippet: 
    
    ```{code_snippet}```

    Do **not** provide any suggestions for fixing, optimizing, or improving the code."""

    return outstring

def generate_output(pipeline, messages):
    outputs = pipeline(messages, max_new_tokens=256)
    return(outputs[0]["generated_text"][-1])



def clean_file(file_name, pipeline, llm):

    with open(file_name, "r") as file:
        data = json.load(file)

    num_projects = len(data)
    cur_project = 1

    didnt_find_content_to_summarize_type_count = 0

    for project, issue_reports in data.items():

        print(f"CLEANING ISSUE REPORTS FROM PROJECT {cur_project} OF {num_projects} (project name: {project})")
        cur_project += 1

        num_issue_reports = len(issue_reports)

        for i in range(len(issue_reports)):

            print(f"CLEANING ISSUE REPORT {i+1} of {num_issue_reports} (PROJECT {cur_project} OF {num_projects})")


            # REMOVE NULL CHARACTERS
            if issue_reports[i]["title"] != None:
                data[project][i]["title"] = issue_reports[i]["title"].replace('\0', '')

            if issue_reports[i]["body"] != None:
                data[project][i]["body"] = issue_reports[i]["body"].replace('\0', '')

                # REPLACE URLs
                data[project][i]["body"] = re.sub(r'https?://\S+|www\.S+', '<URL>', data[project][i]["body"])

                # REMOVE TEXT NOT RENDERED IN ISSUE REPORT
                open_tag = ""
                close_tag = ""
                body_without_comments = ""
                is_comment = False

                for char in data[project][i]["body"]:
                    if is_comment:
                        if char == "-" and close_tag == "":
                            close_tag = char
                        elif char == "-" and close_tag == "-":
                            close_tag += char
                        elif char == ">" and close_tag == "--":
                            close_tag = ""
                            is_comment = False
                        else:
                            close_tag = ""
                
                    else:
                        if char == "<" and open_tag == "":
                            open_tag = char

                        elif char == "!" and open_tag == "<":
                            open_tag += char

                        elif char == "-" and len(open_tag) >= 2:
                            open_tag += char
                            if open_tag == "<!--":
                                is_comment = True
                                open_tag = ""

                        else:
                            if open_tag != "":
                                body_without_comments += open_tag
                                open_tag = ""
                            body_without_comments += char

                data[project][i]["body"] = body_without_comments

                # SUMMARIZE CODE SNIPPETS, SHELL SCRIPTS, AND OUTPUT LOGS
                updated_body = ""
                content_to_summarize = ""
                reading_content_to_summarize = False
                backticks = ""

                if "```" in data[project][i]["body"]:
                    for char in data[project][i]["body"]:
                        if char == "`":
                            backticks += "`"
                            if backticks == "```":
                                if reading_content_to_summarize:
                                    # print(content_to_summarize)
                                    messages = [{"role": "user", "content": get_content_to_summarize_type(content_to_summarize)},]
                                    # updated_body += "```" + generate_output(pipeline, messages)["content"] + "```"
                                    content_to_summarize_type = re.sub(r"[^123]", "", generate_output(pipeline, messages)["content"])
                                    # print(content_to_summarize_type)

                                    if content_to_summarize_type == "1":
                                        messages = [{"role": "user", "content": summarize_code_snippet_prompt_template(content_to_summarize)},]
                                        output = generate_output(pipeline, messages)["content"]
                                        # print(output)
                                        updated_body += "```" + output + "```"

                                    elif content_to_summarize_type == "2":
                                        messages = [{"role": "user", "content": summarize_shell_script_prompt_template(content_to_summarize)},]
                                        output = generate_output(pipeline, messages)["content"]
                                        # print(output)
                                        updated_body += "```" + output + "```"

                                    elif content_to_summarize_type == "3":
                                        messages = [{"role": "user", "content": summarize_output_log_prompt_template(content_to_summarize)},]
                                        output = generate_output(pipeline, messages)["content"]
                                        # print(output)
                                        updated_body += "```" + output + "```"

                                    else:
                                        print(content_to_summarize_type)
                                        updated_body += content_to_summarize
                                        didnt_find_content_to_summarize_type_count += 1
                                        print("DIDNT FIND CONTENT TO SUMMARIZE COUNT:", didnt_find_content_to_summarize_type_count)

                                    
                                    content_to_summarize = ""
                                    reading_content_to_summarize = False
                                else:
                                    reading_content_to_summarize = True
                                backticks = ""
                                
                        else:
                            if backticks != "":
                                updated_body += backticks
                                backticks = ""
                            if reading_content_to_summarize:
                                content_to_summarize += char
                            else:
                                updated_body += char            

                    data[project][i]["body"] = updated_body
        
                else:
                    print("NO CODE SNIPPETS, OUTPUT LOGS, OR SHELL SCRIPTS FOUND IN THIS ISSUE REPORT!")


    llm = llm.replace("/", "_")

    outfolder_path = f"dataset/{llm}"
    os.makedirs(outfolder_path, exist_ok=True)

    with open(outfolder_path + f"/{file_name[8:-8]}cleaned.json", "w") as outfile:
        json.dump(data, outfile, indent=4)


if __name__ == "__main__":


    MODEL_NAME = sys.argv[1]

    # LLM Implementation in this work. You can use your own.
    pipeline = transformers.pipeline(
        "text-generation",
        model=MODEL_NAME,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="cuda:2"
    )

    print("CLEANING TRAIN SET!!!!!!!!!!!!")

    clean_file("dataset/train_set_raw.json", pipeline, MODEL_NAME)

    print("CLEANING TEST SET!!!!!!!!!!")

    clean_file("dataset/test_set_raw.json", pipeline, MODEL_NAME)

