import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.gemini import ask_food_assistant

def index_view(request):
    """Renders the main food assistant chatbot page."""
    return render(request, 'index.html')

@csrf_exempt
def chat_api_view(request):
    """
    API endpoint for sending a message to the food assistant.
    Expects a POST request with a JSON body containing 'message' and optionally 'history'.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        history = data.get('history', [])
        
        if not message:
            return JsonResponse({'error': 'Message is required.'}, status=400)
        
        # Get structured response from Gemini service
        response_data = ask_food_assistant(message, history)
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
