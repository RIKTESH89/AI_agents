# research_agent.py

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from orchestrator import AgentState
from data import event_planning_data

def research_agent(state: AgentState, research_model) -> AgentState:
    """
    Analyzes user preferences and generates event recommendations.
    """
    messages = state["messages"]
    user_request = event_planning_data.get("user_prompt", "")

    system_prompt = SystemMessage(content=f"""You are the Research Agent. Your primary role is to understand the user's preferences and generate three distinct, creative, and appealing recommendations for the event.

Original user request: "{user_request}"

You have one tool at your disposal:
1.  **research_tool**: Use this to analyze the user's interests, past activities, and preferences to generate tailored recommendations.

Your workflow is as follows:
1.  Analyze the user's request.
2.  Call the `research_tool` with a query that captures the essence of the event (e.g., "wife's birthday party").
3.  The tool will return structured recommendations.
4.  Present these recommendations clearly to the orchestrator, who will then present them to the user.

Your final output should be a message containing the recommendations from the tool.
""")

    # Construct the message list for the model
    all_messages = [system_prompt] + list(messages) + [HumanMessage(content=f"Generate event recommendations for the following request: {user_request}")]

    # Invoke the model to get the response, which should include a tool call
    response = research_model.invoke(all_messages)

    return {
        "messages": [response],
        "current_agent": "research_agent",
        "next_action": "research_tools" if response.tool_calls else "orchestrator"
    }
