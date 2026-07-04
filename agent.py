"""here is the logic of the agent that is trying to fix the mistake in the code"""

import os
import subprocess

from google import genai
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

model="gemini-3.5-flash" #the brain of the agent


"""every agent has a set of tools that it can use to perform tasks. 
These tools are defined in the TOOLS variable below. Each tool has a name, a description and input schema. 
The agent can use these tools to perform tasks such as reading files, writing files, and executing shell commands."""


TOOLS = [
    {
        "name": "read_file",
        "description": "Reads the content of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read."
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Writes content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to write."
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file."
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "Lists all files in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "The path to the directory to list files from."
                }
            },
            "required": ["directory_path"]
        }
    },
    {
        "name": "run_test",
        "description": "Runs the test in the test.py file and returns the output, including any errors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_file_path": {
                    "type": "string",
                    "description": "The path to the test file to run."
                }
            },
            "required": ["test_file_path"]
        }
    }
]


"""The functions below implement the logic for each tool. The model just asks for the functions to be called, and the functions are executed in the background. 
The model does not have direct access to the file system or the ability to execute shell commands, so it relies on these functions to perform those tasks.
Python is the one that executes the functions and returns the results to the model.
so the model can focus on reasoning and decision-making, while Python handles the actual execution of tasks.
The results of the functions are returned to the model, which can then use that information to make decisions and take further actions."""

def read_file(file_path):
    """Reads the content of a file."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}
    
def write_file(file_path, content):
    """Writes content to a file."""
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return {"message": f"Content written to {file_path}"}
    except Exception as e:
        return {"error": str(e)}
    
def list_files(directory_path):
    """Lists all files in a directory."""
    try:
        files = os.listdir(directory_path)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
    
def run_test(test_file_path):
    """Runs the test in the test.py file and returns the output, including any errors."""
    try:
        result = subprocess.run(['python', test_file_path], capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"error": str(e)}
