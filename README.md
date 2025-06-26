# Master Thesis Project

This repository contains the files and code used for the completion of the Master Thesis Project WS2024/25.
The project also includes the browser executor feature, implemented in the [AttackMate repository on the `browser-executor` branch](https://github.com/annaerdi/attackmate/tree/browser-executor).


## Folder Structure

The table below outlines the structure of the project and its contents.

| Folder/File        | Description                                                                                                                            |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `evaluation/`      | Contains preliminary experiments for comparing human created vs LLM generated playbooks                                                |
| `playbooks/`       | Collection of playbook files for testing                                                                                               |
| `prompts/`         | Collection of prompts used for generating the playbooks                                                                                |
| `src/txt-docs/`    | Text based documentation of the AttackMate for feeding the custom GPT. Generated programmatically by scraping the AttackMate codebase. |
| `src/playbookgen/` | The core CLI tool for generating playbooks using LLM.                                                                                  |


## PlaybookGen CLI Tool

The `playbookgen` CLI tool is used for generating playbooks using the LLM model. The tool is located in the `src/playbookgen/` folder.

### Setup

1. Clone the repository
2. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY="your_api_key_here"
   ```
3. Create and activate venv, and install the package in development mode:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

### Usage

To run the PlaybookGen CLI tool:

```bash
cd src/playbookgen
python main.py [--output path/to/playbook.yml]
```
Use the optional `--output` or `-o` argument to automatically save the
generated YAML playbook to the provided file path.

### Troubleshooting

If you encounter `ImportError: cannot import name 'OpenAI' from 'openai'`, you may need to reinstall the OpenAI package:

```bash
pip uninstall openai
pip install openai
```

