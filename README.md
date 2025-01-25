# Master Thesis Project

This repository contains the files and code used for the completion of the Master Thesis Project WS2024/25.
The project also includes the browser executor feature, implemented in the [AttackMate repository on the `browser-executor` branch](https://github.com/annaerdi/attackmate/tree/browser-executor).


## Folder Structure

The table below outlines the structure of the project and its contents.

| Folder/File        | Description                                                                                                                            |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `evaluation/`      | Contains preliminary experiments for comparing human created vs LLM generated playbooks                                                |
| `playbooks/llm`    | Collection of playbook files generated by LLM                                                                                          |
| `playbooks/manual` | Collection of manually created playbook files                                                                                          |
| `prompts/`         | Collection of prompts used for generating the playbooks                                                                                |
| `src/helpers/`     | Python files for generating text docs for creating the RAG enabled GPT. Results are collected in `src/txt-docs/`.                      |
| `src/txt-docs/`    | Text based documentation of the AttackMate for feeding the custom GPT. Generated programmatically by scraping the AttackMate codebase. |




