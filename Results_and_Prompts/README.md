# Results and Prompts Folder

This folder contains the dataset, prompts, and generated results of this work which is described in depth below:


NEED TO EXPLAIN evaluator_validation/repr_subset_evals.csv

## "raw_dataset.zip" 

When unzipped, this folder contains three files. Two of them, "train_set_raw.json" and "test_set_raw.json", provide the raw train and test sets respectively. These datasets are organized in the following manner:

```json
{
    "REPOSITORY_NAME_1": [ // an array containing objects representing each issue report from this repository
        {
            // Object with information regarding the first issue report from this repository
            "number": "issue number, type=Number",
            "created_at": "date issue report was created, type=String",
            "labels": "array of original labels assigned to the issue report, type=array of Strings",
            "title": "issue report's title, type=String",
            "body": "issue report's body, type=String",
            "closing_commits": [ // an array containing objects representing each commit involved in closing the issue report
                {
                    "commit_url": "commit url, type=String",
                    "patches": [ // an array of patches associated with this commit
                        "patch 1, type=String",
                        "patch 2, type=String",
                        ...
                    ]
                }
            ]
        },
        {
            // Object with information regarding the second issue report from this repository
            ...
        },
        ...
    ],
    "REPOSITORY_NAME_2": [
        ...
    ],
    ...
}
```

The third file, "dataset_info.txt", contains a breakdown of the number of issue reports in the train and test set respectively from each of the 30 repositories in the dataset.

## "labeled_datasets.zip"

When unzipped, this folder contains 3 folders named after each label assigner LLM used in this work. Inside each of these folders is a file called "train_set_labeled.json" which is based on "train_set_raw.json" with the following modifications:

 - Each issue report's body has been cleaned in the following manner:
    - All null characters, i.e., "\0" were removed as they can cause issues when processing strings.

    - All URLs were replaced with the placeholder keyword "\<URL>".

    - All content enclosed by Markdown comment tags, i.e., opening tag "\<!--" and closing tag "\-->", was removed as this content is not rendered when opening the issue report in the GitHub web interface, therefore human labelers do not see this content when manually reviewing issue reports.

    - Code snippets, shell scripts, and output logs were summarized by the label assigner LLM using the prompts in the folder [prompts/technical_summarization_prompts](./prompts/technical_summarization_prompts/).

 - The addition of the field "assigned_labels" to each issue report object, which is an array of labels assigned by the label assigner LLM to the issue report using the prompt in [prompts/label_generation_prompt.txt](./prompts/label_generation_prompt.txt). 
    - NOTE: These assigned labels were used to derive our list of labels. For how this was achieved, see the ["label_generation_results" folder](#label_generation_results-folder), ["clusters" folder](#clusters-folder), and ["label_list" folder](#label_list-folder) sections.

 - The addition of the field "assigned_labels_from_catalog" to each issue report object, which is an array of labels assigned by the label assigner LLM to the issue report from our derived label list (see list in the file [label_list/label_list.csv](./label_list/label_list.csv)) using the prompt in [prompts/assign_labels_from_list_prompt.txt](./prompts/assign_labels_from_list_prompt.txt).

 - The addition of the field "assigned_one_of_four_label" to each issue report object, which is a single label out of "bug", "feature", "documentation", or "question" assigned by the label assigner LLM to the issue report using the prompt in [prompts/assign_one_of_four_label_prompt.txt](./prompts/assign_one_of_four_label_prompt.txt).

 - The addition of the fields "labels_sims", "assigned_labels_sims", and "assigned_labels_from_catalog_sims" to each issue report object, which are arrays of the corresponding cosine similarity values between the embedded labels and embedded issue report text for the labels in the fields "labels", "assigned_labels", and "assigned_labels_from_catalog" respectively.

 - The addition of the field "assigned_one_of_four_label_sim" to each issue report object, which is a single number representing the cosine similarity value between the embedding of the label in "assigned_one_of_four_label" and the embedded issue report text.

Given that the embeddings of the labels assigned by "Qwen2.5-7B-Instruct" from our derived list (i.e., the labels in the field "assigned_labels_from_catalog" in the file "labeled_datasets/Qwen_Qwen2.5-7B-Instruct/train_set_labeled.json") exhibited the highest average cosine similarity to the embedded issue report text, these labels were evaluated by a label evaluator LLM, namely "deepseek-r1:70b" using the prompt in [prompts/label_evaluation_prompt.txt](./prompts/label_evaluation_prompt.txt). The resulting evaluations are stored in the file "labeled_datasets/Qwen_Qwen2.5-7B-Instruct/train_set_evaluated.json", where each issue report object includes the field "evaluation_of_assigned_labels_from_catalog" structured as follows:

```json
    "evaluation_of_assigned_labels_from_catalog": {
        "ASSIGNED_LABEL_1": {
            "evaluation": "'1' if the evaluator LLM adjudicated the label to accurately reflect the issue report, otherwise '0'",
            "reason": "the actual output of the evaluator LLM"
        },
        "ASSIGNED_LABEL_2": {
            ...
        }
        ...
    }
```

Note that the fields "labels_sims", "assigned_labels_sims", "assigned_labels_from_catalog_sims", and "assigned_one_of_four_label_sim" are not present in "labeled_datasets/Qwen_Qwen2.5-7B-Instruct/train_set_evaluated.json" but all other fields in "labeled_datasets/Qwen_Qwen2.5-7B-Instruct/train_set_labeled.json" are preserved. Additionally, the issue report bodies have been cleaned as described in this section.

Again, because the labels assigned by "Qwen2.5-7B-Instruct" from our derived list achieved the highest average cosine similarity to the embedded issue report text, this model was the sole label assigner used for the test set. There are 3 labeled test set ".json" files in "labeled_datasets/Qwen2.5-7B-Instruct", namely "test_set_labeled_w_RAG_sims.json", "test_set_labeled_w_non_RAG_sims.json", and "test_set_evaluated.json". These files are based on "test_set_raw.json". The following are modifications to "test_set_raw.json" that are present in all 3 files:

 - The issue report bodies have been cleaned in the same manner described above.

 - The addition of the field "assigned_labels_from_catalog" to each issue report object which, as in "train_set_labeled.json", is an array of labels assigned by the label assigner LLM to the issue report from our derived label list (see list in the file [label_list/label_list.csv](./label_list/label_list.csv)) using the prompt in [prompts/assign_labels_from_list_prompt.txt](./prompts/assign_labels_from_list_prompt.txt).

 - The addition of the field "assigned_one_of_four_label" to each issue report object which, as in "train_set_labeled.json", is a single label out of "bug", "feature", "documentation", or "question" assigned by the label assigner LLM to the issue report using the prompt in [prompts/assign_one_of_four_label_prompt.txt](./prompts/assign_one_of_four_label_prompt.txt)

 - The addition of the fields "RAG_label_options_k=x", where x ranges from 1 to 30, to each issue report object. This is an array of labels assigned by "Qwen2.5-7B-Instruct" that were adjudicated to accurately reflect the issue report by the evaluator LLM to the k issue reports in the training set who's embedded text is most similar to the issue report in the test set. 

 - The addition of the fields "assigned_labels_from_RAG_labels_only_k=x", where x ranges from 1 to 30, to each issue report object. This is an array of labels assigned by the label assigner LLM to the issue report from "RAG_label_options_k=x" using the prompt in [prompts/RAG_labels_only_prompt.txt](./prompts/RAG_labels_only_prompt.txt).

 - The addition of the fields "assigned_labels_from_RAG_labeled_issue_reports_k=x", where x ranges from 1 to 30, to each issue report object. This is an array of labels assigned by the label assigner LLM to the issue report from "RAG_label_options_k=x" using the prompt in [prompts/RAG_labeled_issue_reports_prompt.txt](./prompts/RAG_labeled_issue_reports_prompt.txt).

There are some fields that are present in the issue report objects of only one of the labeled test set files. The following are these fields:

### Fields only present in "test_set_labeled_w_non_RAG_sims.json"

 - "labels_sims" and "assigned_labels_from_catalog_sims" which, as in "train_set_labeled.json", are arrays of the corresponding cosine similarity values between the embedded labels and embedded issue report text for the labels in the fields "labels" and "assigned_labels_from_catalog".
 
 - "assigned_one_of_four_label_sim" which, as in "train_set_labeled.json", is a single number representing the cosine similarity value between the embedding of the label in "assigned_one_of_four_label" and the embedded issue report text.


### Fields only present in "test_set_labeled_w_RAG_sims.json"

 - "assigned_labels_from_RAG_labels_only_k=x_sims", where x ranges from 1 to 30, which are arrays of the corresponding cosine similarity values between the embedded labels and embedded issue report text for the labels in the fields "assigned_labels_from_RAG_labels_only_k=x".

 - "assigned_labels_from_RAG_labeled_issue_reports_k=x_sims", where x ranges from 1 to 30, which are arrays of the corresponding cosine similarity values between the embedded labels and embedded issue report text for the labels in the fields "assigned_labels_from_RAG_labeled_issue_reports_k=x".

### Fields only present in "test_set_evaluated.json"

 - "combined_assigned_labels" and "new_combined_assigned_labels", which are arrays of labels containing those assigned by the highest performing k values (based on average cosine similarity between embedded assigned labels and embedded issue report text) for both the "labels only" and "labeled_issue_reports" prompts (k = 3 in both cases) as well as those in "assigned_labels_from_catalog". These labels were merged to avoid duplicate evaluations given the high cost of employing "deepseek-r1:70b" as the evaluator LLM. Specifically, if a label appeared in at least two of  "assigned_labels_from_RAG_labels_only_k=3", "assigned_labels_from_RAG_labeled_issue_reports_k=3", and "assigned_labels_from_catalog", it is included only once in either "combined_assigned_labels" or "new_combined_assigned_labels". Constructing these arrays facilitated systematic iteration that ensured the evaluator LLM did not evaluate the same label for a given issue report more than once.

 - "evaluation_of_combined_assigned_labels", "evaluation_of_new_combined_assigned_labels", "evaluation_of_original_labels", and "evaluation_of_assigned_one_of_four_label", which contain the evaluations of the labels in "combined_assigned_labels", "new_combined_assigned_labels", "labels", and assigned_one_of_four_label" in the same format of "evaluation_of_assigned_labels_from_catalog" in "train_set_evaluated.json"
   - Note that oftentimes "evaluation_of_assigned_one_of_four_label" is an empty object. When this is the case, it is because the "assigned_one_of_four_label" was present in either "combined_assigned_labels" or "new_combined_assigned_labels", therefore it was not necessary to conduct another evaluation of the same label on the same issue report.


## ["label_generation_results" Folder](./label_generation_results)

This folder contains 3 files containing the aggregation of labels generated by each label assigner LLM to all 13,210 issue reports in the training set using the prompt in [prompts/label_generation_prompt.txt](./prompts/label_generation_prompt.txt). Note that post-processing of these generated labels was conducted to prevent duplicates. This included converting all text to lowercase and replacing dashes and underscores with spaces (e.g., "Feature request", "feature_request", and "Feature-Request" all become "feature request"). After this post-processing, there were 5,925, 8,020, and 7,552 unique labels assigned by "gemma-2-9b-it", "Llama-3.1-8B-Instruct", and "Qwen2.5-7B-Instruct" respectively. The files themselves list all the uniquely generated labels by the LLM along with the number of the 13,210 issue reports from which the LLM generated this label from.

## ["clusters" Folder](./clusters/)

The 5,925, 8,020, and 7,552 unique labels assigned by "gemma-2-9b-it", "Llama-3.1-8B-Instruct", and "Qwen2.5-7B-Instruct" respectively generated from all 13,210 issue reports in the training set using the prompt in [prompts/label_generation_prompt.txt](./prompts/label_generation_prompt.txt) were combined, forming a total of 14,960 unique labels (this total is less than the sum of the individual counts because many labels were generated by more than one model). We then filtered out labels that were generated by only one LLM from a single issue report as such labels are not helpful for broader issue report categorization. This filtering removed 8,788 labels, leaving a set of 6,172. These labels were then fed to Agglomerative Clustering to group labels with similar meanings. 

Each folder in the ["clusters" folder](./clusters/) is named after the text embedding model ("all-mpnet-base-v2", "fastText", "Qwen_Qwen3-Embedding-8B", or "word2vec"), distance metric ("euc" or "cos") and linkage criteria ("average", "complete", "single", or "ward") used to generate the resultant clusterings within the folder. 

Inside the folder is "clustering_summary_stats.csv" which contains the summary statistics for the tested clusterings, and files "SIM_THRESHOLD=XX.csv" which contains the clusterings generated using the settings in the folder name at this distance threshold. 

Each line in the "SIM_THRESHOLD=XX.csv" represents a cluster and contains the following fields:

 - "representative_label_by_embedding": the label who's embedding is closest to the centre of the cluster in vector space.
 - "count": the sum of the number of issue reports "representative_label_by_embedding" was generated from of each LLM.
   - e.g., the label "bug" was generated from 2008, 8937, and 3705 issue reports from "gemma-2-9b-it", "Llama-3.1-8B-Instruct", and "Qwen2.5-7B-Instruct" respectively so its "count" would be 14650.
 - "representative_label_by_count: the label in the cluster who's sum of the number of issue reports it was generated from is the highest.
 - "count": the sum of the number of issue reports "representative_label_by_count" was generated from of each LLM.
 - "total_count": the total number of issue reports all labels in the cluster were generated from.
 - "cluster": all the labels in the cluster.


## ["label_list" Folder](./label_list/)

The optimal clustering was [clusters/all-mpnet-base-v2_metric=cos_link=avg/SIM_THRESHOLD=0.3](./clusters/all-mpnet-base-v2_metric=cos_link=avg/SIM_THRESHOLD=0.3.csv). We selected the representative labels for each cluster to be "representative_label_by_count". We then had 2 authors evaluate each representative label to determine if they should be included in the list of labels. The results of this are in the file [label_list/evaluation_of_repr_labels.csv](./label_list/evaluation_of_repr_labels.csv). Each row in the file contains the following fields:

 - "Label": A representative label for a cluster in the file [clusters/all-mpnet-base-v2_metric=cos_link=avg/SIM_THRESHOLD=0.3](./clusters/all-mpnet-base-v2_metric=cos_link=avg/SIM_THRESHOLD=0.3.csv).
 - "LJ Include?": If the author "LJ" deemed the label should be included in the list, the value of this field is "1". Otherwise the value of this field is "0".
 - "LJ Reason": If the author "LJ" deemed the label should be included in the final list, this field was left empty. Otherwise, this field contained the reason why the author "LJ" deemed the label should not be included in the list.
 - "MRM include": If the author "MRM" deemed the label should be included in the list, the value of this field is "1". Otherwise the value of this field is "0".
 - "MRM comments": General comments the author "MRM" had regarding the labeling decision.
 - "LJ Comments": Comments added to the file by the author "LJ" after "LJ" and "MRM" had a discussion regarding discrepencies in their judgement of inclusion for the label in the final list.
 - "Final Decision": If both authors agreed on the decision whether to include the label in the final list, this field was left empty. Otherwise, this field is marked "1" to include the label in the list or "0" to exclude the label from the list based on the discussion between authors "LJ" and "MRM".

The final label list based on the evaluation of authors "LJ" and "MRM" is in the file [label_list/label_list.csv](./label_list/label_list.csv).