#!/usr/bin/env python3
"""Direct test of Ollama endpoint to debug 404 issue."""

import httpx
import asyncio
import json

async def test_ollama():
    """Test Ollama /api/generate endpoint directly."""
    
    base_url = "http://localhost:11434"
    endpoint = f"{base_url}/api/generate"
    
    payload = {
        "model": "llama3:8b",
        "prompt": "Say hi",
        "stream": False
    }
    
    print(f"Testing endpoint: {endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\nSending POST request...")
            response = await client.post(endpoint, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ Success!")
                print(f"Response text: {result.get('response', '')}")
            else:
                print(f"\n✗ Failed with status {response.status_code}")
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
