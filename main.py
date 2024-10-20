import os
import json
import datetime
from groq import Groq
from dotenv import load_dotenv

INDEX_FILE = "history/index.json"
SESSION_FILE_PREFIX = "session_"
HISTORY_DIR = "history"

# Model specifications with keywords
MODEL_SPECIALIZATIONS = {
    "llama-3.1-8b-instant": ["shortest", "brief", "concise", "quick", "clear", "simple"],
    "llama-3.1-70b-versatile": ["explanation", "detailed", "in-depth", "comprehensive", "thorough", "elaborate"],
    "image-model-specialized": ["image", "visual", "picture", "graph", "illustration"],
    "gemma2-9b-it": ["detailed", "complex", "extended", "rich", "insightful"],
    "gemma-7b-it": ["in-depth", "thorough", "intensive", "comprehensive", "detailed"],
    "llama-guard-3-8b": ["guarded", "safe", "secure", "protected"],
    "llama3-70b-8192": ["large-context", "extensive", "contextual", "broad"],
    "llama3-8b-8192": ["quick", "medium-context", "responsive", "efficient"],
    "llama3-groq-70b-8192-tool-use-preview": ["tool-use", "preview", "functional", "specialized"],
    "llama3-groq-8b-8192-tool-use-preview": ["tool-use", "preview", "functional", "specialized"],
    "llava-v1.5-7b-4096-preview": ["preview", "specific", "focused", "targeted"],
    "mixtral-8x7b-32768": ["large-context", "expansive", "extended", "wide"]
}

# Extended shades and bright colors for models
MODEL_COLOR_SHADES = {
    "llama-3.1-8b-instant": [32, 92, 42],  # Different shades of green
    "llama-3.1-70b-versatile": [34, 94, 36],  # Different shades of blue
    "gemma2-9b-it": [33, 93, 43],  # Different shades of yellow
    "gemma-7b-it": [35, 95, 45],  # Different shades of magenta
    "llama-guard-3-8b": [36, 96, 46],  # Different shades of cyan
}

# Dictionary to track how many responses a model has generated
model_response_count = {}

def load_history(session_id):
    """Load conversation history for a specific session."""
    filename = get_session_filename(session_id)
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return [{"role": "system", "content": "You are a helpful assistant."}]

def get_index():
    """Load or initialize the index file."""
    ensure_history_directory()
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as file:
            return json.load(file)
    return {"sessions": []}

def update_index(session_id, file_path):
    """Update the index file with a new session."""
    index = get_index()
    index["sessions"].append({"session_id": session_id, "file_path": file_path})
    with open(INDEX_FILE, "w") as file:
        json.dump(index, file)


def ensure_history_directory():
    """Create the history directory if it doesn't exist."""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)


def get_session_filename(session_id):
    """Generate a filename for the given session ID within the history directory."""
    return os.path.join(HISTORY_DIR, f"{SESSION_FILE_PREFIX}{session_id}.json")


def save_history(session_id, history):
    """Save conversation history for a specific session."""
    filename = get_session_filename(session_id)
    # try:
    with open(filename, "w") as file:
        json.dump(history, file)
    #     print(f"History saved to {filename}")
    # except Exception as e:
    #     print(f"Error saving history: {e}")

def color_text(text, color_code):
    """Return the text wrapped in the appropriate color code."""
    return f"\033[{color_code}m{text}\033[0m"

def print_colored_output(result, model):
    """Print the response with a distinct shade per model response."""
    # Get shades for the model
    shades = MODEL_COLOR_SHADES.get(model, [37])  # Default to white shades

    # Track how many times the model has generated a response
    if model not in model_response_count:
        model_response_count[model] = 0

    # Select a color shade based on the response count for this model
    shade_index = model_response_count[model] % len(shades)
    color_code = shades[shade_index]

    # Print the response text with the chosen shade
    print(color_text(f"\nResponse from {model}:", color_code))
    print(color_text(result, color_code))

    # Increment the model's response count for the next time
    model_response_count[model] += 1

load_dotenv("api_key.env")

def generate_text(messages, model):
    """Generate a response from the specified model with conversation history."""
    try:
        api_key=os.getenv('API_KEY')
        if not api_key:
            raise ValueError("API Not Found")
        
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model
        )
        response_text = chat_completion.choices[0].message.content
        return response_text
    except Exception as e:
        return f"Error: {e}"

def select_model_based_on_keyword(prompt):
    """Select the appropriate model based on the first word in the prompt."""
    # Get the first word of the prompt
    first_word = prompt.lower().split()[0] if prompt.strip() else None

    if first_word:
        # Iterate through the models and their keywords
        for model, keywords in MODEL_SPECIALIZATIONS.items():
            if first_word in keywords:
                return model

    # Default model if no match is found
    return "llama-3.1-70b-versatile"  # Default model if no keyword matches

def interactive_prompt():
    """Run an interactive prompt for the user with conversation history."""
    print("Hey boss, welcome to Terminal GPT!")

    # Generate a unique session ID based on timestamp
    session_id = str(datetime.datetime.now().strftime("%Y-%m-%d_%H_%M"))
    
    # Track if the first question has been asked
    first_question_asked = False

    while True:
        user_input = input("Enter your prompt (or type 'exit' to quit): ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        if not first_question_asked:
            first_question_asked = True
            # Generate the session filename with the first question
            session_filename = get_session_filename(f"{user_input[:50]}_{session_id}")  # Use a snippet of the first question
            update_index(session_id, session_filename)
            history = [{"role": "system", "content": "You are a helpful assistant."}]
        else:
            session_filename = get_session_filename(session_id)
            history = load_history(session_id)

        # Determine the model based on user input
        model = select_model_based_on_keyword(user_input)

        # Add user input to history
        history.append({"role": "user", "content": user_input})

        # Generate response using the selected model
        result = generate_text(history, model)
        
        if result:
            if "Error:" in result:
                print(f"Model {model} failed with error: {result}")
            else:
                # Add model's response to history
                history.append({"role": "assistant", "content": result})
                
                # Print the response with colored text
                print_colored_output(result, model)
        else:
            print("Failed to get a response. Please try again later.")
        
        # Save the updated history
        # print(session_id,type(session_id))
        # print('s_'+session_id.replace('-','')+'.json')
        save_history(session_id, history)

if __name__ == "__main__":
    interactive_prompt()
