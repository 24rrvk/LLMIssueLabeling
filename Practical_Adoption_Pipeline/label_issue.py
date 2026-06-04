import requests, re, csv, ast

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

def preprocess_issue_text(title, body, llm_url, llm):

    if title != None:
        title = title.replace('\0', '')

    if body != None:
        body = body.replace('\0', '')

        # REPLACE URLs
        body = re.sub(r'https?://\S+|www\.S+', '<URL>', body)

        # REMOVE TEXT NOT RENDERED IN ISSSUE REPORT
        open_tag = ""
        close_tag = ""
        body_without_comments = ""
        is_comment = False

        for char in body:
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

        body = body_without_comments

        # SUMMARIZE CODE SNIPPETS, SHELL SCRIPTS, AND OUTPUT LOGS
        updated_body = ""
        content_to_summarize = ""
        reading_content_to_summarize = False
        backticks = ""

        if "```" in body:
            for char in body:
                if char == "`":
                    backticks += "`"
                    if backticks == "```":
                        if reading_content_to_summarize:
                            request = {
                                "model": llm,
                                "prompt": get_content_to_summarize_type(content_to_summarize),
                                "stream": False
                            }
                            # updated_body += "```" + generate_output(pipeline, messages)["content"] + "```"
                            content_to_summarize_type = re.sub(r"[^123]", "", requests.post(llm_url, json=request).json()["response"])
                            # print(content_to_summarize_type)

                            if content_to_summarize_type == "1":
                                request = {
                                    "model": llm,
                                    "prompt": summarize_code_snippet_prompt_template(content_to_summarize),
                                    "stream": False
                                }
                                output = requests.post(llm_url, json=request).json()["response"]
                                # print(output)
                                updated_body += "```" + output + "```"

                            elif content_to_summarize_type == "2":
                                request = {
                                    "model": llm,
                                    "prompt": summarize_shell_script_prompt_template(content_to_summarize),
                                    "stream": False
                                }
                                output = requests.post(llm_url, json=request).json()["response"]
                                # print(output)
                                updated_body += "```" + output + "```"

                            elif content_to_summarize_type == "3":
                                request = {
                                    "model": llm,
                                    "prompt": summarize_output_log_prompt_template(content_to_summarize),
                                    "stream": False
                                }
                                output = requests.post(llm_url, json=request).json()["response"]
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

            body = updated_body

    return title, body

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


def label_issue(issue_number, title, body, needs_processing, attempt_count):

    attempt_count += 1
    
    LLM_URL = "http://localhost:11435/api/generate"
    LLM = "qwen2.5:7b"

    if needs_processing:
        processed_title, processed_body = preprocess_issue_text(title, body, LLM_URL, LLM)
    else:
        processed_title = title
        processed_body = body


    with open("label_list.csv", "r") as labels_file:
        labels_reader = csv.reader(labels_file)
        labels = []
        for line in labels_reader:
            labels.append(line[0])

    request = {
        "model": LLM,
        "prompt": prompt_template(processed_title, processed_body, labels),
        "stream": False
    }
    raw_output = requests.post(LLM_URL, json=request).json()["response"]

    # LLM needs to output labels in a valid Python list so they can be processed
    valid_output = False
    reading_output = False
    cleaned_output = ""
    for char in raw_output.strip():
        if reading_output:
            cleaned_output += char
            try:
                assigned_labels_raw = ast.literal_eval(cleaned_output)
                if isinstance(assigned_labels_raw, list):
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

        # ONLY SAVE LLM-ASSIGNED LABELS IF THEY ARE IN THE LIST
        for label in assigned_labels_raw:
            if label in labels:
                assigned_labels_cleaned.append(label)

        """
        Here, you can either:

        1. Implement adding the labels in assigned_labels_cleaned to the issue report
           on GitHub using its issue number.
        2. Send a notification to a project contributor of the issue report details and 
           the assigned labels so they can validate the label assignments.
        """

    else:
        if attempt_count <= 5:
            # If the LLM does not generate valid output, try again for a maximum of 5 tries
            label_issue(issue_number, processed_title, processed_body, False, attempt_count)




