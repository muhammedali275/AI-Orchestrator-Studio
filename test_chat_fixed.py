"""
Test the fixed chat functionality with Ollama
"""
import requests
import json

# Test the chat endpoint
url = "http://localhost:8000/v1/chat/ui/send"

payload = {
    "message": "Hello, how are you?",
    "model_id": "llama3:8b",
    "routing_profile": "direct_llm",
    "use_memory": False,
    "use_tools": False
}

print("Testing chat endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=120)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ SUCCESS!")
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
    else:
        print(f"\n✗ FAILED!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
