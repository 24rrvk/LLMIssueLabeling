# Code Folder

The following are instructions on how to follow our approach to obtain your own results using the code in this folder.

Step 1: Run the following command to unzip the dataset:

```bash
unzip dataset.zip 
```

Step 2: Pre-process issue report text with clean_data.py
 - Arguments: 
    1. LLM used to summarize the issue report content

 IMPLEMENTATION OF LLM IS USING HUGGING FACE SO IT HAS TO BE A VALID HUGGING FACE MODEL

Step 3: Generate labels for issue reports with generate_labels.py
 - Arguments: 
    1. LLM used to assign labels to the issue reports.. THIS LLM  MUST BE ONE THAT HAS BEEN RUN USING clean_data.py

Step 4: CLUSTER.. FIGURE OUT WHAT TO DO FOR THIS ONE AFTER PAPER IS DONE
 - Can generate summary stats for clusters too

Step 5: Assign labels from list using assign_labels_from_list.py
 - Arguments:
    1. LLM used to assign labels to the issue reports.. THIS LLM MUST BE ONE THAT HAS BEEN RUN USING clean_data.py
    2. The file containing the label list which the LLM needs to select its labels from. the label list derived in this work can be found at [./label_list/label_list.csv](./label_list/label_list.csv).
    3. The issue reports filename in "./dataset/{LLM_NAME} that you wish to label. Ensure that the dataset has been pre-processed, i.e., select either "train_set_cleaned.json" or "test_set_cleaned.json"

Step 6: Evaluate labels 

Step 7: Build RAG DB

Step 8: Can assign labels using RAG with either RAG_labeled_issue_reports.py or RAG_labels_only.py