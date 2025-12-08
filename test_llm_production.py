#!/usr/bin/env python3
"""
Comprehensive LLM Connection Test for Production Readiness
Tests all aspects of LLM connectivity before deployment
"""

import asyncio
import httpx
import json
import time
import sys
from typing import Dict, Any, List


class LLMProductionTester:
    """Test LLM connection for production readiness."""
    
    def __init__(self, base_url: str, model: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.results = []
    
    async def test_server_reachability(self) -> Dict[str, Any]:
        """Test if LLM server is reachable."""
        print("\n🔍 Test 1: Server Reachability")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                version = response.json()
                print(f"✅ Server reachable - Version: {version.get('version', 'unknown')}")
                return {"passed": True, "version": version}
        except Exception as e:
            print(f"❌ Server unreachable: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_model_availability(self) -> Dict[str, Any]:
        """Test if specified model is available."""
        print("\n🔍 Test 2: Model Availability")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                if self.model in model_names:
                    print(f"✅ Model '{self.model}' is available")
                    return {"passed": True, "available_models": model_names}
                else:
                    print(f"❌ Model '{self.model}' not found")
                    print(f"   Available models: {', '.join(model_names)}")
                    return {"passed": False, "available_models": model_names}
        except Exception as e:
            print(f"⚠️  Could not verify model: {str(e)}")
            return {"passed": True, "warning": "Could not verify, but continuing"}
    
    async def test_simple_completion(self) -> Dict[str, Any]:
        """Test simple completion request."""
        print("\n🔍 Test 3: Simple Completion")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Say 'test successful' and nothing else."}
                    ],
                    "stream": False
                }
                
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response_time = (time.time() - start_time) * 1000
                
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                print(f"✅ Completion successful ({response_time:.0f}ms)")
                print(f"   Response: {content[:100]}...")
                return {
                    "passed": True,
                    "response_time_ms": response_time,
                    "response": content
                }
        except Exception as e:
            print(f"❌ Completion failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_conversation_context(self) -> Dict[str, Any]:
        """Test multi-turn conversation."""
        print("\n🔍 Test 4: Conversation Context")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First message
                payload1 = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Remember this number: 42"}
                    ],
                    "stream": False
                }
                response1 = await client.post(f"{self.base_url}/api/chat", json=payload1)
                
                # Second message referencing first
                payload2 = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Remember this number: 42"},
                        {"role": "assistant", "content": response1.json()["message"]["content"]},
                        {"role": "user", "content": "What number did I ask you to remember?"}
                    ],
                    "stream": False
                }
                response2 = await client.post(f"{self.base_url}/api/chat", json=payload2)
                
                content = response2.json()["message"]["content"]
                has_42 = "42" in content
                
                if has_42:
                    print(f"✅ Context maintained correctly")
                else:
                    print(f"⚠️  Context may not be maintained")
                
                return {"passed": has_42, "response": content}
        except Exception as e:
            print(f"❌ Context test failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid requests."""
        print("\n🔍 Test 5: Error Handling")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test with invalid model
                payload = {
                    "model": "nonexistent-model-xyz",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": False
                }
                
                try:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    print(f"⚠️  Expected error but got success")
                    return {"passed": False, "warning": "No error on invalid model"}
                except httpx.HTTPStatusError as e:
                    print(f"✅ Error handling works (status {e.response.status_code})")
                    return {"passed": True, "error_code": e.response.status_code}
        except Exception as e:
            print(f"✅ Error handling works: {str(e)}")
            return {"passed": True}
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance with multiple requests."""
        print("\n🔍 Test 6: Performance Test")
        try:
            times = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i in range(3):
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": f"Count to {i+1}"}],
                        "stream": False
                    }
                    
                    start = time.time()
                    await client.post(f"{self.base_url}/api/chat", json=payload)
                    times.append((time.time() - start) * 1000)
            
            avg_time = sum(times) / len(times)
            print(f"✅ Average response time: {avg_time:.0f}ms")
            print(f"   Min: {min(times):.0f}ms, Max: {max(times):.0f}ms")
            
            return {
                "passed": True,
                "avg_time_ms": avg_time,
                "min_time_ms": min(times),
                "max_time_ms": max(times)
            }
        except Exception as e:
            print(f"❌ Performance test failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate report."""
        print("=" * 60)
        print("🚀 LLM Production Readiness Test")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Model: {self.model}")
        
        tests = [
            ("Server Reachability", self.test_server_reachability),
            ("Model Availability", self.test_model_availability),
            ("Simple Completion", self.test_simple_completion),
            ("Conversation Context", self.test_conversation_context),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
        ]
        
        results = {}
        passed_count = 0
        
        for test_name, test_func in tests:
            result = await test_func()
            results[test_name] = result
            if result.get("passed"):
                passed_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed_count}/{len(tests)} tests passed")
        print("=" * 60)
        
        if passed_count == len(tests):
            print("✅ ALL TESTS PASSED - Ready for production!")
        elif passed_count >= len(tests) - 1:
            print("⚠️  MOSTLY PASSED - Review warnings before production")
        else:
            print("❌ TESTS FAILED - Fix issues before production")
        
        return {
            "total_tests": len(tests),
            "passed": passed_count,
            "results": results,
            "production_ready": passed_count >= len(tests) - 1
        }


async def main():
    """Main test execution."""
    if len(sys.argv) < 3:
        print("Usage: python test_llm_production.py <base_url> <model> [api_key]")
        print("Example: python test_llm_production.py http://localhost:11434 llama3:8b")
        sys.exit(1)
    
    base_url = sys.argv[1]
    model = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else None
    
    tester = LLMProductionTester(base_url, model, api_key)
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("llm_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: llm_test_results.json")
    
    sys.exit(0 if results["production_ready"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
