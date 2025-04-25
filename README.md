# NomadAI - AI Travel Planner (Streamlit + Langchain)

NomadAI is an interactive travel planning assistant built using Streamlit and Langchain. It engages users in a conversation to understand their travel preferences and leverages Google's Gemini LLM and Tavily Search to gather information and generate personalized, day-by-day travel itineraries.

**Core Features:**

*   **Conversational Interface:** Uses Streamlit for an easy-to-use chat interface.
*   **Preference Gathering:** Asks clarifying questions to understand destination, dates, budget, interests, pace, dietary needs, etc.
*   **Context-Aware:** Maintains conversation history using Streamlit's session state.
*   **Real-time Information:** Uses Tavily Search to fetch up-to-date details (attractions, restaurants, events) when needed.
*   **Intelligent Search Triggering:** The LLM determines *when* external information is required and formulates specific search queries.
*   **Itinerary Generation:** Creates detailed, structured itineraries based on the gathered preferences and search results.
*   **Powered by Langchain & Gemini:** Utilizes Langchain for structuring the interaction with the LLM and tools, and Google's `gemini-2.0-flash-001` model for generation.

## How it Works

1.  **Initial Interaction:** The agent starts a conversation to gather basic travel details.
2.  **Conversation Loop:**
    *   The user provides input.
    *   The `conversation_chain` (using the `CONVERSATION_SYSTEM_PROMPT`) processes the input and history.
    *   The LLM either asks clarifying questions, provides information, or signals a need for external data.
3.  **Search Integration:**
    *   If the LLM's response includes the specific signal `[SEARCH_NEEDED: query="<query>"]`, the application extracts the query.
    *   It uses the `TavilySearchResults` tool to perform the web search.
    *   The search results are formatted and fed back into the `conversation_chain` as context for the *next* turn. The LLM then uses these results to provide relevant suggestions.
4.  **Itinerary Generation:**
    *   When the LLM determines enough information is gathered and the user requests the plan, it outputs the signal `[GENERATE_ITINERARY]`.
    *   The application triggers the `itinerary_chain` (using the `ITINERARY_SYSTEM_PROMPT`).
    *   This chain receives the *entire* conversation history and generates a detailed, formatted itinerary.
5.  **Output:** The agent's responses (including the final itinerary) are displayed in the Streamlit chat interface.

## Setup and Installation

**Prerequisites:**

*   Python 3.8+
*   Git (for cloning the repository)

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <https://github.com/sainiakhil/AI-Travel-Planner> # Replace with your actual repo URL
    cd <repository-directory-name>
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    # For Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    streamlit
    langchain
    langchain-google-genai
    langchain-community
    langchain-core
    google-generativeai
    tavily-python
    regex # Although built-in, good to list if explicitly imported
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    This application requires API keys for Google AI (Gemini) and Tavily Search. It uses Streamlit's Secrets management.
    *   Create a directory named `.streamlit` in your project's root folder (if it doesn't exist).
    *   Inside `.streamlit`, create a file named `secrets.toml`.
    *   Add your API keys to `secrets.toml` like this:

    ```toml
    # .streamlit/secrets.toml

    google_token = "YOUR_GOOGLE_AI_API_KEY"
    travily_token = "YOUR_TAVILY_API_KEY"
    ```
    *   Replace `"YOUR_GOOGLE_AI_API_KEY"` and `"YOUR_TAVILY_API_KEY"` with your actual keys.
    *   **Important:** Make sure to add `.streamlit/secrets.toml` to your `.gitignore` file to avoid committing your secret keys to version control.

## Running the Application

1.  **Save the Code:** Ensure the provided Python code is saved in a file, for example, `app.py`.

2.  **Start Streamlit:**
    Run the following command in your terminal (make sure your virtual environment is activated):
    ```bash
    streamlit run Agentic AI Travel Planner.py
    ```

3.  **Access the App:** Streamlit will typically open the application automatically in your default web browser. If not, it will display a local URL (usually `http://localhost:8501`) that you can navigate to.

4.  **Interact:** Start chatting with NomadAI to plan your trip!

## Dependencies

*   `streamlit`: For the web application framework and UI.
*   `langchain`, `langchain-core`, `langchain-community`: For the core Langchain framework, prompt templates, output parsers, and tool integrations.
*   `langchain-google-genai`: For integrating with Google's Gemini models via Langchain.
*   `google-generativeai`: The underlying SDK for Google AI services.
*   `tavily-python`: The Python client for the Tavily Search API.
*   `regex`: Used for parsing search queries from the LLM output.

## Potential Improvements

*   More robust error handling for API calls and parsing.
*   Adding options for different LLMs or search tools.
*   Implementing user profiles to save preferences across sessions.
*   Adding visual elements like maps or images to the itinerary.
*   Integrating booking links or price estimations.
*   Refining the prompts for even better conversational flow and itinerary quality.
