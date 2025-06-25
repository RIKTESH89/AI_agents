# # tools.py

import random
from datetime import datetime
from langchain_core.tools import tool
from data import event_planning_data, WEATHER_DATA
from typing import Optional, List

# ============================================================================
# ENHANCED SCHEDULER AGENT TOOLS (6 tools)
# ============================================================================



@tool
def calendar(query: str, date: Optional[int] = None, month: Optional[int] = None, periodic_event: bool = False) -> str:
    """
    Check calendar events and availability for specific dates and times.
    
    WHEN TO USE:
    - ANY event that requires scheduling (birthdays, meetings, conferences, parties, gatherings)
    - When user mentions specific dates or asks about availability
    - For events that need time coordination with multiple people
    - When checking for conflicts with existing commitments
    
    CONTEXTS:
    ✅ Use for: Birthdays, meetings, conferences, parties, social gatherings, appointments
    ❌ Skip for: Simple reminders, one-time tasks without specific timing
    
    This tool provides date availability, suggests optimal time slots, and identifies potential conflicts.
    
    Args:
        date (int, optional): date of the event to be scheduled
        month (int, optional): month of the event to be scheduled
        query (str): user query to be used for scheduling
        periodic_event (bool, optional): indicates if the event is periodic (e.g., monthly, yearly)
    Returns:
        str: A detailed description of the calendar check and potential conflicts.
    """
    
    # Initialize the result string based on whether a specific date was provided
    if date and month:
        result = f"📅 Calendar Check: The date {month}/{date} is available! No conflicts found. Weekend timing is perfect for family gatherings. "
    else:
        result = f"📅 Calendar checked for: {query}. Available time slots found. Saturday and Sunday will be perfect for family gatherings. "
        
    # FIX: Use the 'random_val' variable instead of the 'random' module.
    # This was causing a TypeError.
    random_val = random.randint(1, 100)
    if random_val % 2 == 0:
        result += "Found a conflict with another event: 'Pick up kids from school'. Please adjust your schedule."
    else:
        # Add suggestions based on event type
        if any(keyword in query.lower() for keyword in ["birthday", "party", "celebration"]):
            result += "Multiple time slots available. Consider 2-6 PM for family events or 7-11 PM for adult celebrations."
        elif any(keyword in query.lower() for keyword in ["meeting", "conference", "business"]):
            result += "Recommended slots: 10:00 AM - 12:00 PM or 2:00 PM - 4:00 PM. Conference rooms available."
        else:
            result += f"Available time slots found. No major conflicts detected."
    
    event_planning_data["calendar_info"] = result
    return result

def create_budget_breakdown(event_type: str, budget: float, guest_count: int, query: str) -> str:
    """Create detailed budget breakdown based on event type and user budget."""
    
    budget_breakdown = f"💰 PERSONALIZED BUDGET BREAKDOWN\n"
    budget_breakdown += f"Total Budget: ${budget:,.2f} | Event Type: {event_type.replace('_', ' ').title()} | Estimated Guests: {guest_count}\n"
    budget_breakdown += "="*60 + "\n\n"
    
    # Budget categories based on event type
    if event_type == "birthday_party":
        categories = {
            "Food & Beverages": 0.40,
            "Decorations & Theme": 0.20,
            "Entertainment & Activities": 0.15,
            "Cake & Desserts": 0.10,
            "Party Favors & Gifts": 0.10,
            "Miscellaneous/Emergency": 0.05
        }
        budget_breakdown += "🎉 BIRTHDAY PARTY BUDGET ALLOCATION:\n"
    elif event_type == "wedding":
        categories = {
            "Venue & Catering": 0.45,
            "Photography & Videography": 0.15,
            "Attire & Beauty": 0.10,
            "Flowers & Decorations": 0.10,
            "Music & Entertainment": 0.08,
            "Transportation": 0.05,
            "Invitations & Stationery": 0.03,
            "Emergency Fund": 0.04
        }
        budget_breakdown += "💍 WEDDING BUDGET ALLOCATION:\n"
    else:  # General event
        categories = {
            "Venue": 0.30,
            "Food & Beverages": 0.35,
            "Decorations": 0.15,
            "Entertainment": 0.10,
            "Supplies": 0.05,
            "Emergency Fund": 0.05
        }
        budget_breakdown += "🎊 GENERAL EVENT BUDGET ALLOCATION:\n"
    
    # Calculate and display each category
    for category, percentage in categories.items():
        amount = budget * percentage
        per_person = amount / guest_count if guest_count > 0 else 0
        budget_breakdown += f"• {category}: ${amount:,.2f} ({percentage*100:.0f}%) - ${per_person:.2f} per person\n"
    
    budget_breakdown += f"\n💡 MONEY-SAVING TIPS:\n"
    budget_breakdown += "• Consider off-peak dates for venue discounts\n"
    budget_breakdown += "• DIY decorations and invitations can save a lot\n"
    
    return budget_breakdown

def get_minimum_budget(event_type: str, guest_count: int) -> float:
    """Calculate minimum realistic budget based on event type and guest count."""
    base_costs = {
        "birthday_party": 15, "wedding": 80, "business_event": 25,
        "graduation": 20, "anniversary": 25, "general": 20
    }
    per_person_cost = base_costs.get(event_type, 20)
    return per_person_cost * guest_count

@tool
def finance(query: str, amount: int = 500) -> str:
    """
    Analyze budget requirements and provide cost estimates for events.
    
    ARGUMENTS:
    - amount: int - Total budget for the event
    - query: str - User query or description of the event
    
    WHEN TO USE:
    - Events involving significant expenses (parties, conferences, weddings, corporate events)
    - When user mentions budget concerns or asks about costs
    - For events requiring multiple vendors or services
    - When planning needs cost optimization
    
    CONTEXTS:
    ✅ Use for: Birthday parties, weddings, conferences, corporate events, large gatherings
    ❌ Skip for: Simple meetings, small gatherings (under 5 people), free events
    
    This tool provides detailed cost breakdowns, budget recommendations, and cost-saving suggestions.
    
    Args:
        amount (int): Amount of money to be used for the event. Defaults to 500.
        query (str): User query or description of the event.
    Returns:
        str: A detailed description of the budget analysis and cost-saving suggestions.
    """
    # FIX: Initialize 'result' to an empty string to prevent an UnboundLocalError
    # if the budget is not over 1000.
    result = ""
    
    # FIX: The signature now correctly uses an integer default.
    # The logic is simplified to directly use the integer amount.
    budget_amount = float(amount)
    
    if budget_amount > 1000:
        result = "Warning: 💰 Budget exceeds your general savings. Still, I'll go ahead and provide a detailed budget breakdown.\n"
    
    event_type = "general"
    if "birthday" in query.lower(): event_type = "birthday_party"
    elif "wedding" in query.lower(): event_type = "wedding"
    
    import re
    guest_matches = re.findall(r'(\d+)\s*(?:people|guests)', query.lower())
    guest_count = int(guest_matches[0]) if guest_matches else 20
    
    # Now it's safe to use +=
    result += create_budget_breakdown(event_type, budget_amount, guest_count, query)
    event_planning_data["finance_info"] = result
    return result

@tool
def health(query: str) -> str:
    """
    Check health and safety considerations, dietary restrictions, and accessibility needs.
    
    WHEN TO USE:
    - Events involving food service (parties, meetings with catering, celebrations)
    - When planning for diverse groups or elderly/children attendees
    - For events in public spaces or requiring safety protocols
    - When user mentions health concerns or dietary restrictions
    
    CONTEXTS:
    ✅ Use for: Food-related events, large gatherings, events with vulnerable populations, outdoor events
    ❌ Skip for: Simple meetings without food, small familiar groups, virtual events
    
    This tool ensures safety compliance and inclusive planning for all attendees.
    
    Args:
        query (str): User query or description of the event
    Returns:
        str: A detailed description of health considerations and climate needs.
    """
    if any(keyword in query.lower() for keyword in ["food", "party"]):
        result = "🏥 Health & Safety Check for Food Events:\n- Common allergens to avoid: Nuts, dairy, gluten.\n- Ensure vegetarian/vegan options available.\n- Keep first aid kit accessible."
    elif "outdoor" in query.lower():
        result = "🏥 Health & Safety Check for Outdoor Events:\n- Sun protection and shade availability.\n- Insect repellent considerations.\n- Weather contingency plans."
    else:
        result = "🏥 General Health & Safety Guidelines:\n- Ensure venue accessibility.\n- Have emergency contact information."
    
    event_planning_data["health_info"] = result
    return result

@tool
def weather(query: str, date: Optional[int] = None, month: Optional[int] = None) -> str:
    """
    Get weather forecasts and climate considerations for event planning.
    
    WHEN TO USE:
    - Outdoor events (parties, weddings, sports, festivals)
    - Events sensitive to weather conditions
    - When planning seasonal activities
    - For events requiring weather-dependent backup plans
    
    CONTEXTS:
    ✅ Use for: Outdoor parties, weddings, sports events, festivals, picnics, garden parties
    ❌ Skip for: Indoor events, virtual meetings, events in climate-controlled venues
    
    This tool provides weather forecasts and helps plan weather-contingent activities.
    
    Args:
        query (str): User query or description of the event.
        date (int, optional): Date of the event to be scheduled.
        month (int, optional): Month of the event to be scheduled (as a number 1-12).
    Returns:
        str: A detailed description of weather considerations and climate needs.
    """
    query_lower = query.lower()
    
    # FIX: The logic is now mutually exclusive using if/elif. This prevents
    # a general query like "outdoor party" from overwriting a specific date forecast.
    if date and month:
        try:
            # Convert month number to name to match the WEATHER_DATA structure
            month_name = datetime(2024, month, 1).strftime('%B').lower()
            date_val = f"{month_name}_{date}"
            
            # Check if the specific date exists in our data
            if date_val in WEATHER_DATA["specific_dates"]:
                result = random.choice(WEATHER_DATA["specific_dates"][date_val])
            else:
                # Fallback to a general forecast if the date is not found
                result = f"☀️ No specific forecast for {month_name} {date}. General forecast: " + random.choice(WEATHER_DATA["general_forecasts"])
        except (ValueError, KeyError):
            # Handle cases with invalid month numbers or other errors
            result = "Could not retrieve specific date forecast. " + random.choice(WEATHER_DATA["general_forecasts"])

    elif "outdoor" in query_lower:
        result = random.choice(WEATHER_DATA["outdoor_events"])
    elif "spring" in query_lower:
        result = random.choice(WEATHER_DATA["seasonal_weather"]["spring"])
    else:
        result = random.choice(WEATHER_DATA["general_forecasts"])
        
    event_planning_data["weather_info"] = result
    return result

@tool
def traffic(query: str) -> str:
    """
    Analyze transportation, parking, and accessibility for event venues.
    
    WHEN TO USE:
    - Events at specific venues (not virtual)
    - When guests need to travel to location
    - For events during peak traffic times
    - When parking or transportation is a concern
    
    CONTEXTS:
    ✅ Use for: Venue-based events, large gatherings, events in busy areas, out-of-town events
    ❌ Skip for: Virtual events, home-based small gatherings, walking-distance events
    
    This tool helps optimize guest arrival and provides transportation guidance.
    """
    if "home" in query.lower():
        result = "🚗 Traffic & Transportation Analysis for Home Events:\n- Residential area with good access.\n- Recommend guests arrive 15-20 minutes early.\n- Street parking available."
    elif "downtown" in query.lower():
        result = "🚗 Urban Venue Transportation:\n- Peak traffic congestion expected.\n- Public transportation recommended.\n- Parking may be limited and expensive."
    else:
        result = f"🚗 Traffic analysis for: {query}. Check venue accessibility and parking options."
        
    event_planning_data["traffic_info"] = result
    return result

# @tool
# def invite_people(query: str) -> str:
#     """
#     Generate invitation content and manage guest lists based on event type and formality.
    
#     WHEN TO USE:
#     - ALL events requiring attendee coordination
#     - When user wants to invite specific people or groups
#     - For events needing RSVP management
#     - When creating guest communications
    
#     CONTEXTS:
#     ✅ Use for: ANY event with attendees (parties, meetings, weddings, conferences, gatherings)
#     ❌ Skip for: Personal reminders, solo activities, events with pre-confirmed attendees
    
#     This tool creates appropriate invitations and manages guest list considerations.
#     """
#     is_informal = any(word in query.lower() for word in ["birthday", "party", "home"])
    
#     if is_informal:
#         result = """📧 Invitation Generated - INFORMAL EVENT:
        
# 🎉 You're Invited to a Birthday Celebration! 🎉

# Join us for a wonderful birthday party!
# 📅 Date: June 30th
# 🕐 Time: 2:00 PM - 6:00 PM  
# 🏠 Venue: At our home

# RSVP by June 25th!"""
#     else:
#         result = """📧 Invitation Generated - FORMAL EVENT:
        
# You are cordially invited to attend [EVENT NAME]

# Date: [Event Date]
# Time: [Event Time]  
# Venue: [Event Location]

# RSVP by [Date]"""
        
#     event_planning_data["invitation_info"] = result
#     return result


# @tool
# def invite_designing(invite_message: str, query: str) -> List[str]:
#     """
#     Creates visual design templates for an invitation message.

#     Args:
#         invite_message (str): The message to be included in the design.
#         query (str): The original user request to inform the design style.

#     Returns:
#         List[str]: A list of generated template filenames.
#     """
#     templates = [
#         "birthday_party_invite_template1.jpg",
#         "birthday_party_invite_template2.jpg",
#         "birthday_party_invite_template1.mp4"
#     ]
    
#     print("finding different templates suitable for the message content")
#     # Store the pure list in the data dictionary
#     event_planning_data["design_info"] = templates
#     return templates

# @tool
# def whatsapp_message(message: str, contacts: str = "auto_detect", design_templates: Optional[List[str]] = None) -> str:
#     """Sends a WhatsApp message, optionally attaching design templates."""
#     if contacts == "auto_detect":
#         contacts = "family_and_friends" if "birthday" in message.lower() else "general_contacts"
    
#     status = f"📱 WhatsApp Message Sent to {contacts}."
#     if design_templates:
#         status += f" Attached designs: {', '.join(design_templates)}."
    
#     event_planning_data["whatsapp_status"] = status
#     return status

# @tool
# def email_message(message: str, subject: str, contacts: str = "auto_detect", design_templates: Optional[List[str]] = None) -> str:
#     """Sends a formal email, optionally attaching design templates."""
#     if contacts == "auto_detect":
#         contacts = "professional_contacts" if "meeting" in message.lower() else "general_email_list"
        
#     status = f"📧 Email Sent to {contacts} with subject '{subject}'."
#     if design_templates:
#         status += f" Attached designs: {', '.join(design_templates)}."
        
#     event_planning_data["email_status"] = status
#     return status


# tools.py

# import random
# from datetime import datetime
# from langchain_core.tools import tool
# from data import event_planning_data, WEATHER_DATA
# from typing import Optional, List

# # ============================================================================
# # SCHEDULER AGENT TOOLS
# # ============================================================================

# @tool
# def calendar(query: str, date: Optional[int] = None, month: Optional[int] = None, periodic_event: bool = False) -> str:
#     """Checks calendar availability."""
#     if date and month:
#         result = f"📅 Calendar Check: The date {month}/{date} is available! No conflicts found."
#     else:
#         result = f"📅 Calendar checked for: '{query}'. Weekend slots are generally open."
#     event_planning_data["calendar_info"] = result
#     return result

# @tool
# def finance(query: str, amount: int = 500) -> str:
#     """Analyzes budget and provides cost estimates."""
#     result = f"💰 Budget analysis for '{query}' with a budget of ${amount} completed. Key recommendations: allocate 40% to venue/catering, 20% to entertainment. Detailed breakdown generated."
#     event_planning_data["finance_info"] = result
#     return result

# @tool
# def health(query: str) -> str:
#     """Checks health, safety, and dietary restrictions."""
#     result = f"🏥 Health & Safety check for '{query}' complete. Standard protocols include providing hand sanitizer, ensuring accessibility, and offering vegetarian/vegan food options."
#     event_planning_data["health_info"] = result
#     return result

# @tool
# def weather(query: str, date: Optional[int] = None, month: Optional[int] = None) -> str:
#     """Gets weather forecasts."""
#     if date and month:
#         month_name = datetime(2024, month, 1).strftime('%B').lower()
#         date_key = f"{month_name}_{date}"
#         forecasts = WEATHER_DATA["specific_dates"].get(date_key, ["General forecast: Partly cloudy with a light breeze."])
#         result = random.choice(forecasts)
#     else:
#         result = random.choice(WEATHER_DATA["general_forecasts"])
#     event_planning_data["weather_info"] = result
#     return result

# @tool
# def traffic(query: str) -> str:
#     """Analyzes transportation and parking."""
#     result = f"🚗 Traffic analysis for '{query}' complete. Expect moderate traffic; advise guests to allow 20 minutes extra travel time. Parking details provided."
#     event_planning_data["traffic_info"] = result
#     return result

# ============================================================================
# COMMUNICATION & DESIGN AGENT TOOLS
# ============================================================================

@tool
def invite_people(query: str) -> str:
    """
    Generates the text content for an invitation.
    
    Args:
        query (str): The original user request to inform the invitation style.
    
    Returns:
        str: The text content for the invitation.
    """
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
    """
    Sends a WhatsApp message, optionally attaching design templates.
    
    Args:
        message (str): The message to be sent.
        contacts (str, optional): The contacts to send the message to. Defaults to "auto_detect".
        design_templates (Optional[List[str]], optional): A list of design templates to attach. Defaults to None.
    
    Returns:
        str: A status message indicating the message was sent.
    
    """
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

@tool
def research_tool(query: str) -> List[dict[str, any]]: 
    """
    Analyzes user's recent interests, hobbies, visited places, and preferences
    to generate event recommendations.
    
    Args:
        query (str): User query or description of the event.
    
    Returns:
        List[Dict[str, Any]]: A list of recommended event themes and venues.
    """
    # In a real-world scenario, this would connect to databases, social media APIs, etc.
    # For this implementation, we will simulate the research and return static recommendations.
    print(f"🔬 Researching preferences for: '{query}'...")
    recommendations = [
        {
            "venue": "Home backyard setup",
            "theme": "Cozy garden party with fairy lights",
            "price": 300
        },
        {
            "venue": "Premium restaurant downtown",
            "theme": "Elegant dinner celebration",
            "price": 800
        },
        {
            "venue": "Community event hall",
            "theme": "Game night with catered food",
            "price": 500
        }
    ]
    event_planning_data["recommendations"] = recommendations
    return recommendations