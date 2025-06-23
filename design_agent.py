# messaging_agent.py

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from orchestrator import AgentState
from data import event_planning_data
import time

def design_agent(state: AgentState, desing_model) -> AgentState:
    """
    Template designing agent which created different templates as per given data. Uses the 'invite_designing' tool for creating invitation templates.
    """
    messages = state["messages"]
    user_request = event_planning_data.get("user_request", "")
    invitation_content = event_planning_data.get("invitation_info", "No invitation template has been created yet.")
    
    # Updated system prompt to include the 'invite_people' tool.
    system_prompt = SystemMessage(content=f"""You are the invitation designer Agent. Your role is to create different invitation templates as per given message for the event.

Original user request: "{user_request}"
Current invitation content prepared by the communication: "{invitation_content}"

You have 1 tools at your disposal:
1.  **invite_designing**: To generate different invitation templates for the event.

Your workflow is as follows:
1.  Use the `invite_designing` tool to generate different invite templates on the event details.

After sending, summarize the designer actions taken. If messages have already been sent, simply state that designing is complete.""")
    
    # Check if communication tasks have already been completed in a previous step.
    
    all_messages = [system_prompt] + list(messages) + [HumanMessage(content=f"Use invite_designing tool to generate different invite templates for the event. User request: {user_request}")]
    
    # # Invoke the model to get the response, which may include tool calls.
    response = desing_model.invoke(all_messages)

    # print(f"\n Creating drafts message templates as per the message content:")
    # time.sleep(2)
    # print(f"\n ")
    return {
        "messages": [response],
        "current_agent": "design_agent", 
        # If the model's response includes tool calls, the next action is 'tools', otherwise the process ends.
        "next_action": "design_tools" if response.tool_calls else "end"
    }
