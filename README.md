
# LLM Issue Labeling Replication Package

Welcome to the replication package for our work on GitHub issue report labeling using LLMs! This replication package is split into two folders, [Code](./Code/) and [Results_and_Prompts](./Results_and_Prompts/). The former contains the implementation of our approach and instructions on how to use the implementation to obtain results. The latter contains the results we obtained through following our approach. Further details regarding each folder can be found in their respective "README.md" files: [Code/README.md](./Code/README.md) and [Results_and_Prompts/README.md](./Results_and_Prompts/README.md)

## Cloning Instructions

The "Results_and_Prompts/labeled_datasets.zip" file is stored using Git Large File Storage (LFS) because it exceeds GitHub's file size limit of 100.00 MB. As a result, if cloning the repo for the first time, you need to first install Git LFS to correctly download this file:

```bash
# Install Git LFS (one-time setup)
git lfs install

# Clone the repository (normal git clone works)
git clone https://github.com/24rrvk/LLMIssueLabeling.git

# Pull LFS-tracked files
git lfs pull
```

Without Git LFS, the large files will appear as small text pointer files instead of the actual data.