# messaging_agent.py

from langchain_core.messages import SystemMessage, AIMessage
from orchestrator import AgentState
from data import event_planning_data

def communication_agent(state: AgentState, communication_model) -> AgentState:
    """
    A state-aware communication agent that handles a multi-step invitation process.
    1. Drafts the invitation text.
    2. Waits for the design agent to create templates.
    3. Sends the final invitation with designs via the appropriate channel.
    """
    messages = state["messages"]
    user_request = event_planning_data.get("user_request", "")
    invitation_content = event_planning_data.get("invitation_info")
    design_content = event_planning_data.get("design_info")

    # Check if the process is already complete
    if event_planning_data.get("whatsapp_status") or event_planning_data.get("email_status"):
        summary = "📱 COMMUNICATION COMPLETED: Invitations have already been sent."
        return {
            "messages": [AIMessage(content=summary)],
            "current_agent": "communication",
            "next_action": "end"
        }

    # Scenario 1: Invitation not drafted yet.
    if not invitation_content:
        system_prompt = SystemMessage(content=f"""You are the Communication Agent, stage 1. Your first job is to draft the invitation text.

Original user request: "{user_request}"
Plan details have been gathered by the scheduler.

Your workflow is as follows:
1.  Use the `invite_people` tool to generate the perfect invitation text based on the event details in the user request.
This is your only task in this step. The designer will take over after this.""")
    
    # Scenario 2: Invitation is drafted, but no designs yet. This state should not be handled by this agent.
    # The routing will handle passing control to the design agent.

    # Scenario 3: Invitation and Designs are ready. Time to send.
    elif invitation_content and design_content:
        system_prompt = SystemMessage(content=f"""You are the Communication Agent, stage 2. The invitation text and design templates are ready. Your final job is to send them.

Invitation Text: "{invitation_content}"
Design Info: "{design_content}"

Your workflow is as follows:
1.  Review the invitation content to determine if it's for a formal or informal event.
2.  Choose the correct tool: `whatsapp_message` for informal events or `email_message` for formal ones.
3.  Call the chosen tool with the invitation text, a subject (for email), and the list of design templates. The design templates can be extracted from the 'Design Info' provided above.""")
    
    else: # Fallback, should not happen in the correct flow
         system_prompt = SystemMessage(content="You are the Communication Agent. Determine the next step based on the conversation history.")


    all_messages = [system_prompt] + list(messages)
    
    response = communication_model.invoke(all_messages)

    return {
        "messages": [response],
        "current_agent": "communication", 
        "next_action": "tools" if response.tool_calls else "end"
    }
