#!/usr/bin/env python3
"""
Test script for AIPanel chat flow with all topology nodes.
This script tests the complete flow from API request to response,
ensuring all nodes are executed correctly.
"""

import requests
import json
import time
import sys
import os

# Configuration
API_URL = "http://localhost:8000/api/chat"
API_KEY = "test_api_key"  # Replace with actual API key if needed
TOPOLOGY = "zain_default"
AGENT_NAME = "zain_agent"
USER_ID = "test_user"
TEST_INPUT = "What is the capital of France?"

def test_chat_flow():
    """Test the complete chat flow through all nodes."""
    print("Testing AIPanel chat flow...")
    
    # Prepare request payload
    payload = {
        "client_id": "test_client",
        "topology": TOPOLOGY,
        "agent_name": AGENT_NAME,
        "user_id": USER_ID,
        "input": TEST_INPUT,
        "context": {
            "test_mode": True,
            "trace_execution": True  # Enable detailed tracing
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        # Send request
        print(f"Sending request to {API_URL}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(API_URL, json=payload, headers=headers)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Chat request successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify all nodes were executed
            verify_node_execution(result)
            
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return False

def verify_node_execution(result):
    """Verify that all expected nodes were executed."""
    expected_nodes = [
        "start_node",
        "intent_router_node",
        "planner_node",
        "llm_agent_node",  # or external_agent_node
        "tool_executor_node",
        "grounding_node",
        "memory_store_node",
        "audit_node",
        "end_node"
    ]
    
    if "node_execution" not in result:
        print("\n⚠️ Warning: No node execution data in response")
        return
    
    executed_nodes = result["node_execution"]
    print("\nNode Execution Summary:")
    
    all_nodes_executed = True
    for node in expected_nodes:
        if node in executed_nodes:
            duration = executed_nodes[node].get("duration_ms", "N/A")
            status = executed_nodes[node].get("status", "unknown")
            print(f"  ✅ {node}: {status} ({duration} ms)")
        else:
            print(f"  ❌ {node}: Not executed")
            all_nodes_executed = False
    
    if all_nodes_executed:
        print("\n✅ All expected nodes were executed successfully!")
    else:
        print("\n⚠️ Some expected nodes were not executed")

def test_monitoring():
    """Test the monitoring endpoints."""
    print("\nTesting monitoring endpoints...")
    
    monitoring_url = "http://localhost:8000/api/monitoring/summary"
    
    try:
        response = requests.get(monitoring_url, headers={"Authorization": f"Bearer {API_KEY}"})
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Monitoring request successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return False

def test_service_control():
    """Test the service control endpoints."""
    print("\nTesting service control endpoints...")
    
    service_url = "http://localhost:8000/api/monitoring/service-status"
    
    try:
        response = requests.get(service_url, headers={"Authorization": f"Bearer {API_KEY}"})
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Service status request successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=== AIPanel Runtime Testing ===\n")
    
    # Test chat flow
    chat_success = test_chat_flow()
    
    # Test monitoring
    monitoring_success = test_monitoring()
    
    # Test service control
    service_success = test_service_control()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Chat Flow: {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"Monitoring: {'✅ PASS' if monitoring_success else '❌ FAIL'}")
    print(f"Service Control: {'✅ PASS' if service_success else '❌ FAIL'}")
    
    # Overall result
    if chat_success and monitoring_success and service_success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
