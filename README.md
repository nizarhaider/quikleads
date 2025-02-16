
# Quikleads

Quikleads is a Python project designed to manage and interact with a SQL database using LangChain and Ollama models. This project includes functionalities for exporting and importing Ollama models, as well as querying a database for product information.

## Project Structure

```
quikleads/
├── models/
│   └── models_v2.ipynb
├── miscellaneous/
│   └── ollama_manager.py
└── README.md
```

## Notebooks

### models/models_v2.ipynb

This Jupyter notebook demonstrates how to interact with a SQL database using LangChain and Ollama models. It includes the following key functionalities:

- Setting up environment variables for LangSmith API.
- Connecting to a SQLite database and querying product information.
- Using LangChain's SQLDatabaseToolkit and ChatOllama for database interactions.
- Defining a custom system message template for the agent.

## Scripts

### miscellaneous/ollama_manager.py

This script provides functionalities to export and import Ollama models. It includes:

- Exporting an installed Ollama model to a tarball.
- Importing an Ollama model from a tarball.
- Handling manifest and blob files associated with the models.
- Confirming overwrites for existing files during import.

## Usage

### Exporting a Model

To export a model, run the following command:

```sh
python ollama_manager.py export <model_name>:<model_size> [--base_path /custom/path]
```

Example:

```sh
python ollama_manager.py export foo-model:14b
```

### Importing a Model

To import a model, run the following command:

```sh
python ollama_manager.py import <tarball_path> [--base_path /custom/path]
```

Example:

```sh
python ollama_manager.py import ollama_export_foo-model_14b.tar
```

## Requirements

- Python 3.12.8
- LangChain
- Ollama
- Jupyter Notebook

## Installation

1. Clone the repository:

```sh
git clone <repository_url>
cd quikleads
```

2. Create a virtual environment and activate it:

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

3. Install the required packages:

```sh
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License.
```
