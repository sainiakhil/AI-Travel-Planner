import streamlit as st
import os
import re # Import regex for parsing potential search queries

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser


# --- LLM and Tools ---
# Initialize the LLM with Gemini 2.0 Flash model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", google_api_key=st.secrets["google_token"], temperature=0.2, convert_system_message_to_human=True )

search_tool = TavilySearchResults(max_results=4, tavily_api_key=st.secrets["travily_token"])

# --- Prompt Templates ---

# Main Conversation Prompt - Guides the LLM on how to interact and *signal* needs
# Note: It now asks the LLM to output a specific signal if search is needed.
CONVERSATION_SYSTEM_PROMPT = """
You are ' NomadAI', a friendly AI travel planning assistant. Your goal is to create personalized travel itineraries.

**Your Process:**
1.  **Gather & Refine:** Chat with the user to understand: Destination, Dates/Duration, Budget, Start Location, Purpose, Interests, Dietary Needs, Pace, Accommodation Style, Must-dos/Avoids. Ask clarifying questions one or two at a time. Use the chat history for context.
2.  **Identify Need for Current Info:** If you need up-to-date information like top attractions, specific restaurant types, hidden gems, opening hours, or current events for the destination based on the user's refined preferences, you MUST end your response with the exact phrase: `[SEARCH_NEEDED: query="<your specific search query here>"]`. For example: `[SEARCH_NEEDED: query="best vegetarian restaurants Rome near Colosseum relaxed atmosphere"]`. Do NOT invent information; signal the need for a search.
3.  **Use Provided Search Results:** If the input contains '[SEARCH_RESULTS]', use that information to provide curated suggestions (3-5 options) linked to the user's preferences. Ask for feedback on the suggestions. Do not mention the search results directly unless necessary for clarification.
4.  **Check for Itinerary Request:** Identify when the user explicitly asks for the final itinerary (e.g., "generate the plan", "create the itinerary", "sounds good, let's make the schedule"). If they do, end your response ONLY with the exact phrase: `[GENERATE_ITINERARY]`.
5.  **Normal Conversation:** Otherwise, continue the conversation, ask relevant questions, or respond naturally based on the chat history.

**General Instructions:** Be conversational, helpful, empathetic. Maintain context. If the user asks for the itinerary *before* enough details are gathered, explain politely what information is still needed.
"""

conversation_prompt = ChatPromptTemplate.from_messages([
    ("system", CONVERSATION_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

# Specific Prompt for Generating the Final Itinerary
ITINERARY_SYSTEM_PROMPT = """
You are 'NomadAI', tasked with generating a final, detailed travel itinerary.
Based on the entire provided conversation history, which includes the user's preferences (destination, dates, budget, interests, pace, diet, etc.) and agreed-upon activities/suggestions:

1.  Create a coherent, day-by-day itinerary for the specified duration.
2.  Structure each day logically (e.g., Morning, Afternoon, Evening).
3.  Group nearby activities together to minimize travel time.
4.  Incorporate the user's specific interests and preferences (pace, diet, budget level).
5.  Include meal suggestions (e.g., "Lunch near [Attraction]", "Dinner in [Neighborhood]") fitting dietary needs.
6.  Mix activities with potential downtime.
7.  Add practical notes (e.g., booking recommendations, transport tips) if applicable.
8.  Format the output clearly and readably using markdown.
Ensure the itinerary directly reflects the details discussed in the conversation history.
"""

itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", ITINERARY_SYSTEM_PROMPT),
    # We will pass the *entire* relevant history here
    MessagesPlaceholder(variable_name="chat_history"),
    # The 'input' here is just a trigger, the history contains the substance
    ("human", "Please generate the detailed itinerary based on our conversation."),
])


# --- Memory ---
# Use Streamlit's session state for conversation history persistence
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Hello! I'm AI Travel Planner. Where are you dreaming of traveling to? Tell me a bit about your ideal trip!")]



parser = StrOutputParser()

# --- Chains ---
# Dedicated chain for the main conversation
conversation_chain = conversation_prompt | llm | parser
# Dedicated chain for final itinerary generation
itinerary_chain = itinerary_prompt | llm | parser

# --- Memory (using Streamlit Session State) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Hello! I'm NomadAI. Where are you dreaming of traveling to? Tell me a bit about your ideal trip!")]



# --- Streamlit App UI ---
st.set_page_config(page_title="NomadAI Travel Planner (Chain/Parser)", page_icon="✈️")
st.title("NomadAI - Your AI Travel Planner ✈️ (Chain/Parser Version) 🌎 ")
st.caption("Let's plan your next adventure! Tell me where you want to go.")

# Display chat history
for msg in st.session_state.chat_history:
    avatar = "🤖" if isinstance(msg, AIMessage) else "👤"
    with st.chat_message(msg.type, avatar=avatar):
        st.write(msg.content)

# Get user input
if user_input := st.chat_input("Your message"):
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    with st.chat_message("human", avatar="👤"):
        st.write(user_input)

    # --- Core Logic ---
    with st.spinner("NomadAI is thinking..."):
        try:
            # 1. Run the main conversation chain
            chain_input = {"input": user_input, "chat_history": st.session_state.chat_history[:-1]}
            ai_response_content = conversation_chain.invoke(chain_input) # Output is string

            if not ai_response_content:
                 ai_response_content = "Sorry, I seem to be having trouble responding right now. Could you try again?"

            # 2. Check for special commands in the AI's (string) response
            search_match = re.search(r"\[SEARCH_NEEDED: query=\"(.*?)\"\]", ai_response_content)
            generate_match = "[GENERATE_ITINERARY]" in ai_response_content

            if search_match:
                search_query = search_match.group(1)
                ai_response_content = re.sub(r"\[SEARCH_NEEDED: query=\".*?\"\]", "", ai_response_content).strip()
                st.info(f"NomadAI needs more info, searching for: '{search_query}'...")

                if ai_response_content:
                    st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                    with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)

                try:
                    search_results = search_tool.invoke(search_query)
                    search_context = f"\n[SEARCH_RESULTS]\nHere's some information I found related to '{search_query}':\n{search_results}\nUse this information to provide specific suggestions."

                    st.spinner("Processing search results...")
                    follow_up_input = {
                        "input": search_context,
                        "chat_history": st.session_state.chat_history
                    }
                    ai_response_content = conversation_chain.invoke(follow_up_input) # Output is string
                    if not ai_response_content:
                         ai_response_content = "I found some information, but had trouble formulating suggestions."

                except Exception as search_e:
                    st.error(f"Tavily search failed: {search_e}")
                    ai_response_content = (ai_response_content if ai_response_content else "") + \
                                         "\n\n(I tried searching for more info, but encountered an error.)"

                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)


            elif generate_match:
                ai_response_content = ai_response_content.replace("[GENERATE_ITINERARY]", "").strip()
                st.info("Okay, generating the detailed itinerary based on our conversation...")

                if ai_response_content:
                     st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                     with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)

                itinerary_input = {"chat_history": st.session_state.chat_history}

                # Call the itinerary chain - output is guaranteed string due to parser
                final_itinerary_response = itinerary_chain.invoke(itinerary_input)
                # --- MODIFIED HERE: Directly use the string output ---
                ai_response_content = final_itinerary_response
                # --- No helper function needed ---
                if not ai_response_content:
                    ai_response_content = "I seem to have trouble putting the final plan together. Could we review the key preferences?"

                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)

            else:
                # Normal conversational turn
                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)

        except Exception as e:
            st.error(f"An unexpected error occurred in the main processing loop: {e}")
            import traceback
            st.error(traceback.format_exc())
            ai_response_content = "Sorry, I encountered an internal error. Please try again."
            st.session_state.chat_history.append(AIMessage(content=ai_response_content))
            with st.chat_message("ai", avatar="🤖"):
                        st.write(ai_response_content)


    # --- History Pruning ---
    MAX_HISTORY_LENGTH = 20
    if len(st.session_state.chat_history) > MAX_HISTORY_LENGTH:
        st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY_LENGTH:]
