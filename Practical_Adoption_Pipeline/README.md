# Practical_Adoption_Pipeline Folder

This folder contains an example of how our automated labeling pipeline can be implemented in real-world issue triaging workflows.

The first step is to run the commands in the file [ollama_server_setup_commands.md](./ollama_server_setup_commands.md) to start an Ollama server on your local machine and add an LLM to the running Ollama server.

Next, start the Flask application that listens for new issue report submissions to the issue tracking system and assigns labels to newly submitted issue reports using the LLM loaded onto the Ollama server by running the following command:

```bash
python3 load_new_issue.py
```

Next, follow the instructions in [webhook_configuration_instructions.md](./webhook_configuration_instructions.md) to allow the Flask application to listen to the issue report events occurring in your repository.

Lastly, you can add what you want to be done with the resulting assigned labels at Line 245 in the file [label_issue.py](./label_issue.py).