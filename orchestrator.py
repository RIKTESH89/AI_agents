# orchestrator.py

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from data import event_planning_data
import time

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: str 
    next_action: str

def orchestrator_agent(state: AgentState) -> AgentState:
    """Main orchestrator agent that routes requests to appropriate agents."""
    messages = state["messages"]
    
    user_message = next((msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
    if user_message:
        event_planning_data["user_request"] = user_message
    
    system_prompt = SystemMessage(content="""You are the Orchestrator Agent. Your job is to analyze user requests and route them to the correct specialist agent (scheduler or communication).

- Route to SCHEDULER for: event planning, organizing, coordinating.
- Route to COMMUNICATION for: sending messages or invitations when details are known.

Provide a brief analysis and specify the next agent.""")
    recommendations = event_planning_data.get("recommendations", [])
    selected_theme = event_planning_data.get("selected_theme", {})
    
    if not recommendations:
        next_agent = "research"
        response_content = f"""🎯 ORCHESTRATOR ANALYSIS:
        No recommendations received. Routing to Research Agent.
        """
    elif not selected_theme:
        print("Please select a theme out of the following recommendations: ")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. **Venue:** {rec['venue']}, **Theme:** {rec['theme']}, **Price:** ${rec['price']}")
        user_input = input("\nPlease enter a theme: 1 or 2 or 3: ")
        selected_theme = recommendations[int(user_input) - 1]
        print(f"\n\nSelected theme: {selected_theme['theme']}\n\n")
        event_planning_data["selected_theme"] = selected_theme
        time.sleep(5)
        next_agent = "scheduler"
        response_content = f"""🎯 ORCHESTRATOR ANALYSIS:
        
        {selected_theme['theme']} This is a Event Planning request. Routing to Scheduler Agent."""
    
    elif user_message and recommendations and selected_theme and any(keyword in user_message.lower() for keyword in ["plan", "organize", "schedule", "birthday", "party", "meeting"]):
        next_agent = "scheduler"
        response_content = f"""🎯 ORCHESTRATOR ANALYSIS:

Request: "{user_message}"

This is an EVENT PLANNING request. Routing to Scheduler Agent."""
    else:
        next_agent = "communication"
        response_content = f"""🎯 ORCHESTRATOR ANALYSIS:

Request: "{user_message}"

This is a COMMUNICATION request. Routing to Communication Agent."""
    
    return {
        "messages": [AIMessage(content=response_content)],
        "current_agent": next_agent,
        "next_action": next_agent
    }