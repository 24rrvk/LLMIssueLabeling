## Ollama server start command on local machine

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama serve &
```

This command will start an Ollama server on your local machine on port 11453 as a background process.

## Command to add an LLM to your Ollama server

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen2.5:7b
```