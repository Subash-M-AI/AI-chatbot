import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# System instructions to set the assistant's persona and output format
SYSTEM_INSTRUCTION = """
You are "Rasoi Safar" (Kitchen Journey) - a premium, highly knowledgeable AI Culinary Assistant for famous foods of India. 
Your goal is to guide users through the rich history, local secrets, recipes, ingredients, and geographic origins of famous Indian dishes.

For every user message, you must respond with a JSON object containing two fields:
1. "response": A rich, engaging, beautifully formatted markdown response. Describe the food, its origin story, ingredients, and details. Keep it warm, descriptive, and expert.
2. "locations": An array of geographic coordinates of famous places, historical origins, or legendary restaurants associated with the food item being discussed. Each location must have:
   - "name": The name of the city, region, or legendary restaurant (e.g. "Paradise Biryani, Hyderabad").
   - "lat": The latitude (float, e.g. 17.3850).
   - "lng": The longitude (float, e.g. 78.4867).
   - "description": A short, vibrant note explaining why this place is famous for this food (e.g., "The birthplace of Hyderabadi Biryani, known for its slow-cooked aromatic basmati rice and tender meat.").

If the user's message is a general greeting or does not mention any food, you can return a welcoming response and guide them to ask about famous Indian food, with the "locations" array empty or pointing to general food capitals of India (like Delhi, Mumbai, Kolkata, Chennai).

IMPORTANT: You must return ONLY a raw JSON string matching this structure:
{
  "response": "...",
  "locations": [
    {
      "name": "...",
      "lat": ...,
      "lng": ...,
      "description": "..."
    }
  ]
}
"""

def get_demo_response(message: str) -> dict:
    """Provides a fallback response if the Gemini API key is missing."""
    msg = message.lower()
    
    # Check for keywords
    if "biryani" in msg:
        return {
            "response": "### 🍛 Hyderabadi Biryani\n\n**Hyderabadi Biryani** is a crown jewel of Indian cuisine, originating from the kitchens of the Nizams of Hyderabad. It is prepared in two ways: *Kachchi* (raw) Biryani, where raw marinated meat is layered with parboiled basmati rice and cooked *dum* (slow-cooked under pressure), and *Pakki* (cooked) Biryani.\n\n#### Key Characteristics:\n- **Spices:** Saffron, cardamom, cinnamon, cloves, and mint.\n- **Meat:** Typically lamb or chicken marinated in yogurt and spices.\n- **Serving:** Best enjoyed with *Mirchi ka Salan* (chilli curry) and *Raita*.\n\n*Note: You are seeing a demo response because the Gemini API key is not configured in `.env`.*",
            "locations": [
                {
                    "name": "Charminar, Hyderabad (Origin)",
                    "lat": 17.3616,
                    "lng": 78.4747,
                    "description": "The historic heart of Hyderabad where aromatic Dum Biryani has been perfected over centuries."
                },
                {
                    "name": "Paradise Biryani, Secunderabad",
                    "lat": 17.4436,
                    "lng": 78.4899,
                    "description": "One of the most famous and legendary outlets serving Hyderabadi Biryani since 1953."
                }
            ]
        }
    elif "vada pav" in msg or "vadapav" in msg:
        return {
            "response": "### 🍔 Mumbai Vada Pav\n\nOften called the 'Bombay Burger', **Vada Pav** is the ultimate street food of Maharashtra. It consists of a deep-fried potato dumpling (*vada*) placed inside a sliced bread bun (*pav*), accompanied by spicy chutneys and green chillies.\n\n#### Key Characteristics:\n- **The Vada:** Mashed potato spiced with mustard seeds, garlic, ginger, and green chillies, dipped in chickpea batter and fried.\n- **The Chutneys:** Dry garlic chutney (lasun), sweet tamarind chutney, and green coriander chutney.\n- **History:** Invented by Ashok Vaidya in 1966 near Dadar station to feed hungry mill workers.\n\n*Note: You are seeing a demo response because the Gemini API key is not configured in `.env`.*",
            "locations": [
                {
                    "name": "Dadar Station, Mumbai (Origin)",
                    "lat": 19.0178,
                    "lng": 72.8478,
                    "description": "Where Ashok Vaidya set up the first Vada Pav stall in 1966, launching a culinary phenomenon."
                },
                {
                    "name": "Ashok Vada Pav (Kirti College)",
                    "lat": 19.0224,
                    "lng": 72.8358,
                    "description": "One of Mumbai's most iconic and busy Vada Pav joints, legendary for its crispy 'chura' mix."
                }
            ]
        }
    elif "rosogolla" in msg or "rasgulla" in msg:
        return {
            "response": "### 🍡 Bengali Rosogolla\n\n**Rosogolla** (or Rasgulla) is a beloved syrup-filled dessert popular throughout India, particularly in West Bengal and Odisha. It consists of spherical dumplings of *chhena* (an Indian cottage cheese) and semolina dough, cooked in light sugar syrup.\n\n#### Key Characteristics:\n- **Texture:** Soft, spongy, and juicy, bursting with sweet syrup when bitten.\n- **Variations:** *Nolen Gur-er Rosogolla* (made with fresh date palm jaggery in winter) is highly prized.\n- **History:** West Bengal was awarded the GI tag for 'Banglar Rosogolla' in 2017, celebrating its creation by Nobin Chandra Das in 19th-century Kolkata.\n\n*Note: You are seeing a demo response because the Gemini API key is not configured in `.env`.*",
            "locations": [
                {
                    "name": "Bagbazar, Kolkata (Nobin Chandra Das)",
                    "lat": 22.6025,
                    "lng": 88.3694,
                    "description": "Where Nobin Chandra Das created the modern spongy Rosogolla in 1868."
                },
                {
                    "name": "K.C. Das Grandson, Kolkata",
                    "lat": 22.5645,
                    "lng": 88.3524,
                    "description": "The legendary sweet shop carrying forward the legacy of Nobin Chandra Das's family."
                }
            ]
        }
    elif "salem" in msg:
        return {
            "response": "### 🍛 Salem Famous Food & Legendary Shops\n\n**Salem**, the fifth-largest city in Tamil Nadu, is a paradise for street food lovers and is widely celebrated for its unique local snacks, aromatic biryanis, and top-tier mangoes. Here are the most legendary food shops and items you must try in Salem:\n\n#### 1. Thattu Vadai Settu (Salem Junction / Town)\n- **The Dish:** Salem's signature street food! It is a crispy sandwich made of two flat crunchy puris (*thattu vadai*) filled with freshly grated carrots, beetroot, onions, and slathered with a unique, tangy green-chilli and sweet-tomato chutney mix.\n- **Where:** Stalls around Salem Junction and Salem Town are legendary for this.\n\n#### 2. Mutton Dum Biryani & Chukka at Selvi Mess\n- **The Dish:** A legendary culinary institution in Salem serving mouthwatering South Indian non-veg fare. Their mutton biryani, spicy mutton chukka, and brain fry are cooked with authentic local spices.\n- **Where:** Meyyanur Bypass Road, Salem.\n\n#### 3. Salem Malgova Mangoes (Chinna Kadai Street / Salem Markets)\n- **The Fruit:** Salem is known as the **Mango City of India**. The *Malgova* mango variety grown here is world-famous for its exceptionally sweet, fleshy, and fiberless texture.\n- **Where:** Local fruit markets on Chinna Kadai Street.\n\n#### 4. Sukku Malli Coffee (Dry Ginger Coffee)\n- **The Beverage:** A warming traditional herbal beverage made of dry ginger (*sukku*), coriander seeds (*malli*), and palm jaggery. It is the go-to health drink served across tea shops in Salem.\n- **Where:** Local tea shops near Salem Town.",
            "locations": [
                {
                    "name": "Selvi Mess, Salem (Meyyanur Bypass Rd)",
                    "lat": 11.6660,
                    "lng": 78.1462,
                    "description": "Legendary Salem mess serving authentic non-vegetarian meals, mutton chukka, and aromatic Salem biryani."
                },
                {
                    "name": "Settu Shop, Salem Junction Road",
                    "lat": 11.6698,
                    "lng": 78.1332,
                    "description": "One of the oldest street stalls serving authentic Salem Thattu Vadai Settu and Norukkal snacks."
                },
                {
                    "name": "Chinna Kadai Street Fruit Market, Salem",
                    "lat": 11.6586,
                    "lng": 78.1585,
                    "description": "The historical marketplace famous for authentic Salem Malgova and Alphonso mangoes."
                }
            ]
        }
    else:
        return {
            "response": "### 👋 Namaste! Welcome to Rasoi Safar (Demo Mode)\n\nI am your **Indian Famous Food Assistant**. I am running in **Demo Mode** with local knowledge.\n\n#### Try asking about:\n- **Biryani** (Hyderabadi Biryani description & map locations)\n- **Vada Pav** (Mumbai's famous street food)\n- **Rosogolla** (Kolkata's sweet spongy delicacy)\n- **Salem** (Salem's famous street foods & messes)\n\n*To unlock full AI capabilities covering any dish across India, please ensure a valid `GEMINI_API_KEY` (starting with `AIzaSy`) is configured in the `.env` file!*",
            "locations": [
                {
                    "name": "Delhi (Food Capital)",
                    "lat": 28.6139,
                    "lng": 77.2090,
                    "description": "Famous for Chandni Chowk street food, Butter Chicken, and Paranthe Wali Gali!"
                },
                {
                    "name": "Mumbai (Street Food Hub)",
                    "lat": 19.0760,
                    "lng": 72.8777,
                    "description": "The home of Vada Pav, Pav Bhaji, and Bhel Puri!"
                },
                {
                    "name": "Kolkata (Sweet Capital)",
                    "lat": 22.5726,
                    "lng": 88.3639,
                    "description": "Famous for Rosogolla, Sondesh, and Kathi Rolls!"
                },
                {
                    "name": "Hyderabad (Biryani Hub)",
                    "lat": 17.3850,
                    "lng": 78.4867,
                    "description": "Famous for Nizam's Biryani, Haleem, and Irani Chai!"
                }
            ]
        }

def ask_food_assistant(message: str, history: list = None) -> dict:
    """
    Sends the chat history and message to Gemini and returns structured JSON
    containing the markdown response and location markers.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    # If the API key is missing or is the placeholder, use the demo fallback
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        logger.warning("GEMINI_API_KEY is not configured. Returning demo response.")
        return get_demo_response(message)
        
    # Standard Gemini API keys from Google AI Studio start with 'AIzaSy'
    if not api_key.startswith("AIzaSy"):
        logger.warning("GEMINI_API_KEY does not start with 'AIzaSy'. Returning demo response with diagnostic warning.")
        fallback = get_demo_response(message)
        diagnostic_warning = (
            "⚠️ **API Key Format Warning**\n\n"
            f"The API key you pasted in `.env` starts with `{api_key[:5]}...` instead of the standard `AIzaSy...` prefix.\n\n"
            "To unlock full AI capabilities and get answers for *any* custom questions:\n"
            "1. Go to [Google AI Studio](https://aistudio.google.com/)\n"
            "2. Click **Get API Key** and create a new API key.\n"
            "3. Copy the key (it will start with **`AIzaSy`**) and paste it on line 2 in your [.env](file:///c:/ALL/projects/projects/chatbot/.env) file.\n\n"
            "---\n\n"
        )
        fallback["response"] = diagnostic_warning + fallback["response"]
        return fallback
    
    try:
        # Configure Gemini Client
        genai.configure(api_key=api_key)
        
        # We use gemini-2.5-flash as the standard, robust model for general chatbot tasks
        # It supports system instructions and structured JSON output config
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Build chat contents
        contents = []
        if history:
            for turn in history:
                contents.append({"role": turn.get("role", "user"), "parts": [turn.get("content", "")]})
        
        contents.append({"role": "user", "parts": [message]})
        
        # Generate content with JSON constraint
        response = model.generate_content(
            contents=contents,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        logger.exception("Error calling Gemini API: %s", e)
        # Fallback to demo mode but append error context as a clean footer disclaimer
        fallback = get_demo_response(message)
        fallback["response"] += f"\n\n---\n*⚠️ Note: Displayed using local database due to API error ({str(e)}). Please check your key quota.*"
        return fallback
