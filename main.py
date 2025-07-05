import streamlit as st
import io
import contextlib
from googleapiclient.discovery import build
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub

# --- Tool Function ---
def Google_Search_for_news(query):
    """This function is used by the AI agent."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        if 'items' in res:
            formatted_results = []
            for item in res['items']:
                title = item.get('title', 'No Title'); link = item.get('link', '#'); snippet = item.get('snippet', 'No snippet available.').replace('\n', '')
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
            return "\n".join(formatted_results)
        else: return f"No search results found for '{query}'."
    except Exception as e: return f"An error occurred during the search: {e}"

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("🤖 AI Research Assistant")

# --- Initialize Agent ---
if 'agent_executor' not in st.session_state:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
    tools = [Tool(name="Google_Search_for_news", func=Google_Search_for_news, description="Use to search for recent news on a company or topic.")]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- UI Interaction ---
ai_question = st.text_input("Ask for news or recent developments:", "Latest news on AI infrastructure stocks", key="ai_input")
if st.button("Ask AI"):
    if ai_question:
        with st.spinner("AI is searching..."):
            string_io = io.StringIO()
            with contextlib.redirect_stdout(string_io):
                 response = st.session_state.agent_executor.invoke({"input": ai_question})
            thought_process = string_io.getvalue()
            output = response.get("output")
            st.markdown("### AI Response:"); st.write(output)
            with st.expander("Show Thought Process"): st.text(thought_process)
    else:
        st.warning("Please enter a question for the AI.")
