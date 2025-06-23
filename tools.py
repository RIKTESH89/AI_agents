# tools.py

import random
from datetime import datetime
from langchain_core.tools import tool
from data import event_planning_data, WEATHER_DATA
from typing import Optional, List

# ============================================================================
# SCHEDULER AGENT TOOLS
# ============================================================================

@tool
def calendar(query: str, date: Optional[int] = None, month: Optional[int] = None, periodic_event: bool = False) -> str:
    """Checks calendar availability."""
    if date and month:
        result = f"📅 Calendar Check: The date {month}/{date} is available! No conflicts found."
    else:
        result = f"📅 Calendar checked for: '{query}'. Weekend slots are generally open."
    event_planning_data["calendar_info"] = result
    return result

@tool
def finance(query: str, amount: int = 500) -> str:
    """Analyzes budget and provides cost estimates."""
    result = f"💰 Budget analysis for '{query}' with a budget of ${amount} completed. Key recommendations: allocate 40% to venue/catering, 20% to entertainment. Detailed breakdown generated."
    event_planning_data["finance_info"] = result
    return result

@tool
def health(query: str) -> str:
    """Checks health, safety, and dietary restrictions."""
    result = f"🏥 Health & Safety check for '{query}' complete. Standard protocols include providing hand sanitizer, ensuring accessibility, and offering vegetarian/vegan food options."
    event_planning_data["health_info"] = result
    return result

@tool
def weather(query: str, date: Optional[int] = None, month: Optional[int] = None) -> str:
    """Gets weather forecasts."""
    if date and month:
        month_name = datetime(2024, month, 1).strftime('%B').lower()
        date_key = f"{month_name}_{date}"
        forecasts = WEATHER_DATA["specific_dates"].get(date_key, ["General forecast: Partly cloudy with a light breeze."])
        result = random.choice(forecasts)
    else:
        result = random.choice(WEATHER_DATA["general_forecasts"])
    event_planning_data["weather_info"] = result
    return result

@tool
def traffic(query: str) -> str:
    """Analyzes transportation and parking."""
    result = f"🚗 Traffic analysis for '{query}' complete. Expect moderate traffic; advise guests to allow 20 minutes extra travel time. Parking details provided."
    event_planning_data["traffic_info"] = result
    return result

# ============================================================================
# COMMUNICATION & DESIGN AGENT TOOLS
# ============================================================================

@tool
def invite_people(query: str) -> str:
    """Generates the text content for an invitation."""
    is_informal = any(word in query.lower() for word in ["birthday", "party", "home"])
    if is_informal:
        result = "🎉 You're Invited! Join us for a fun birthday celebration on June 30th at our home. RSVP soon!"
    else:
        result = "You are cordially invited to attend [Event Name] on [Date] at [Venue]. Further details to follow."
    event_planning_data["invitation_info"] = result
    return result

@tool
def invite_designing(invite_message: str, query: str) -> List[str]:
    """
    Creates visual design templates for an invitation message.

    Args:
        invite_message (str): The message to be included in the design.
        query (str): The original user request to inform the design style.

    Returns:
        List[str]: A list of generated template filenames.
    """
    templates = [
        "birthday_party_invite_template1.jpg",
        "birthday_party_invite_template2.jpg",
        "birthday_party_invite_template1.mp4"
    ]
    
    print("finding different templates suitable for the message content")
    # Store the pure list in the data dictionary
    event_planning_data["design_info"] = templates
    return templates

@tool
def whatsapp_message(message: str, contacts: str = "auto_detect", design_templates: Optional[List[str]] = None) -> str:
    """Sends a WhatsApp message, optionally attaching design templates."""
    if contacts == "auto_detect":
        contacts = "family_and_friends" if "birthday" in message.lower() else "general_contacts"
    
    status = f"📱 WhatsApp Message Sent to {contacts}."
    if design_templates:
        status += f" Attached designs: {', '.join(design_templates)}."
    
    event_planning_data["whatsapp_status"] = status
    return status

@tool
def email_message(message: str, subject: str, contacts: str = "auto_detect", design_templates: Optional[List[str]] = None) -> str:
    """Sends a formal email, optionally attaching design templates."""
    if contacts == "auto_detect":
        contacts = "professional_contacts" if "meeting" in message.lower() else "general_email_list"
        
    status = f"📧 Email Sent to {contacts} with subject '{subject}'."
    if design_templates:
        status += f" Attached designs: {', '.join(design_templates)}."
        
    event_planning_data["email_status"] = status
    return status
