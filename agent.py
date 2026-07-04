"""here is the logic of the agent that is trying to fix the mistake in the code"""

import os
import subprocess

from google import genai
from google.genai import types  # Needed for function response formatting
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

model = "gemini-3.5-flash" #the brain of the agent


"""every agent has a set of tools that it can use to perform tasks. 
These tools are defined in the TOOLS variable below. Each tool has a name, a description and input schema. 
The agent can use these tools to perform tasks such as reading files, writing files, and executing shell commands."""

# Declarations explicitly mapped via native types to prevent Pydantic schema parsing issues
TOOLS = [
    types.FunctionDeclaration(
        name="read_file",
        description="Reads the content of a file.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(type=types.Type.STRING, description="The path to the file to read.")
            },
            required=["file_path"]
        )
    ),
    types.FunctionDeclaration(
        name="write_file",
        description="Writes content to a file.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(type=types.Type.STRING, description="The path to the file to write."),
                "content": types.Schema(type=types.Type.STRING, description="The content to write to the file.")
            },
            required=["file_path", "content"]
        )
    ),
    types.FunctionDeclaration(
        name="directory_list",
        description="Lists all files in a directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "directory_path": types.Schema(type=types.Type.STRING, description="The path to the directory to list files from. Defaults to '.' if not provided.")
            },
            required=[]
        )
    ),
    types.FunctionDeclaration(
        name="run_test",
        description="Runs the test in the test.py file and returns the output, including any errors.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "test_file_path": types.Schema(type=types.Type.STRING, description="The path to the test file to run.")
            },
            required=["test_file_path"]
        )
    )
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
    
def directory_list(directory_path="."):
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

TOOLS_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "directory_list": directory_list,
    "run_test": run_test
}


"""The agent loop"""

def run_agent_loop(task, max_iterations=5):
    messages = [{"role": "user" , "parts": [{"text": task}]}]

    for i in range(1, max_iterations + 1):

        print(f"\n--- Step {i} ---")

        response = client.models.generate_content(
            model=model,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=TOOLS)],
                system_instruction="You are a software engineering agent. If you state you want to perform an action that matches a tool, you MUST call that tool in the exact same turn. Do not just say what you plan to do; execute the tool call.",
                temperature=0.0
            )
        )

        # Extracted manually to safely circumvent SDK warnings when no text is returned alongside a function call
        text_content = ""
        if response.candidates and response.candidates[0].content.parts:
            text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
            if text_parts:
                text_content = "".join(text_parts)

        print(f"Model's response:\n{text_content}") #just for debugging purposes

        """save the model's response to the messages list so that it can be used in the next iteration"""
        messages.append({"role": "model", "parts": response.candidates[0].content.parts})

        if not response.function_calls:

            final_text = text_content
            print("Model has finished its reasoning and does not require any more tools." + final_text)
            break

        """if the model has requested to use a tool, we need to extract the tool name and input from the response and call the corresponding function.
        We also need to save the result of the tool call so it can be used in the next iteration."""

        tool_results = []

        for call in response.function_calls:
            tool_name = call.name
            tool_input = call.args if call.args else {}

            print(f"Model requested to use tool: {tool_name} with input: {tool_input}")

            if tool_name in TOOLS_FUNCTIONS:
                tool_function = TOOLS_FUNCTIONS[tool_name]
                
                if tool_name == "directory_list" and "directory_path" not in tool_input:
                    tool_input = {"directory_path": "."}

                result = tool_function(**tool_input)
                print(f"Tool result: {result}")
                tool_results.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response=result
                    )
                )
            else:
                print(f"Tool {tool_name} is not defined.")
                tool_results.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"error": f"Tool '{tool_name}' is not defined."}
                    )
                )

        """save the tool results to the messages list so that it can be used in the next iteration"""

        messages.append({"role": "user", "parts": tool_results})
    
    print("\n--- Agent loop finished ---")
    return None


if __name__ == "__main__":
    task = (
        "There is a bug in agent_practise/calculator.py. Find it by reading the file "
        "and running the tests, fix it, then run the tests again to confirm "
        "everything passes. Explain what the bug was at the end."
    )
    run_agent_loop(task)