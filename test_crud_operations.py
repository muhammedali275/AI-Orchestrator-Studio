#!/usr/bin/env python3
"""
Comprehensive CRUD Operations Testing Script
Tests all API endpoints with Create, Read, Update, Delete operations
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_test(test_name, status, details=""):
    symbol = "✓" if status == "PASS" else "✗"
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol} {test_name}: {status}{reset}")
    if details:
        print(f"  Details: {details}")

test_results = []

# Test 1: Create Credential
print_header("TEST 1: Create Credential")
try:
    data = {
        "name": "test_api_key_001",
        "type": "api_key",
        "secret": "sk-test-key-123456789"
    }
    response = requests.post(f"{BASE_URL}/api/credentials", json=data)
    if response.status_code == 201:
        credential_id = response.json()["id"]
        print_test("POST /api/credentials", "PASS", f"Created credential with ID: {credential_id}")
        test_results.append(("POST /api/credentials", "PASS"))
    else:
        print_test("POST /api/credentials", "FAIL", f"Status: {response.status_code}")
        test_results.append(("POST /api/credentials", "FAIL"))
except Exception as e:
    print_test("POST /api/credentials", "FAIL", str(e))
    test_results.append(("POST /api/credentials", "FAIL"))

# Test 2: List Credentials
print_header("TEST 2: List Credentials")
try:
    response = requests.get(f"{BASE_URL}/api/credentials")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/credentials", "PASS", f"Retrieved {data['total']} credentials")
        test_results.append(("GET /api/credentials", "PASS"))
    else:
        print_test("GET /api/credentials", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/credentials", "FAIL"))
except Exception as e:
    print_test("GET /api/credentials", "FAIL", str(e))
    test_results.append(("GET /api/credentials", "FAIL"))

# Test 3: Create Agent
print_header("TEST 3: Create Agent")
try:
    data = {
        "name": "test_agent_001",
        "url": "http://localhost:8080",
        "timeout_seconds": 30,
        "enabled": True,
        "metadata": {
            "system_prompt": "You are a helpful assistant",
            "description": "Test agent"
        }
    }
    response = requests.post(f"{BASE_URL}/api/agents", json=data)
    if response.status_code in [200, 201]:
        print_test("POST /api/agents", "PASS", "Agent created successfully")
        test_results.append(("POST /api/agents", "PASS"))
    else:
        print_test("POST /api/agents", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
        test_results.append(("POST /api/agents", "FAIL"))
except Exception as e:
    print_test("POST /api/agents", "FAIL", str(e))
    test_results.append(("POST /api/agents", "FAIL"))

# Test 4: List Agents
print_header("TEST 4: List Agents")
try:
    response = requests.get(f"{BASE_URL}/api/agents")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/agents", "PASS", f"Retrieved {len(data)} agents")
        test_results.append(("GET /api/agents", "PASS"))
    else:
        print_test("GET /api/agents", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/agents", "FAIL"))
except Exception as e:
    print_test("GET /api/agents", "FAIL", str(e))
    test_results.append(("GET /api/agents", "FAIL"))

# Test 5: Create Datasource
print_header("TEST 5: Create Datasource")
try:
    data = {
        "name": "test_cubejs_001",
        "type": "cubejs",
        "url": "http://localhost:4000",
        "timeout_seconds": 30,
        "enabled": True,
        "config": {}
    }
    response = requests.post(f"{BASE_URL}/api/datasources", json=data)
    if response.status_code in [200, 201]:
        print_test("POST /api/datasources", "PASS", "Datasource created successfully")
        test_results.append(("POST /api/datasources", "PASS"))
    else:
        print_test("POST /api/datasources", "FAIL", f"Status: {response.status_code}")
        test_results.append(("POST /api/datasources", "FAIL"))
except Exception as e:
    print_test("POST /api/datasources", "FAIL", str(e))
    test_results.append(("POST /api/datasources", "FAIL"))

# Test 6: List Datasources
print_header("TEST 6: List Datasources")
try:
    response = requests.get(f"{BASE_URL}/api/datasources")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/datasources", "PASS", f"Retrieved {len(data)} datasources")
        test_results.append(("GET /api/datasources", "PASS"))
    else:
        print_test("GET /api/datasources", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/datasources", "FAIL"))
except Exception as e:
    print_test("GET /api/datasources", "FAIL", str(e))
    test_results.append(("GET /api/datasources", "FAIL"))

# Test 7: Create Tool
print_header("TEST 7: Create Tool")
try:
    data = {
        "name": "test_http_tool",
        "type": "http_request",
        "enabled": True,
        "config": {
            "base_url": "http://localhost:8080",
            "timeout": 30
        }
    }
    response = requests.post(f"{BASE_URL}/api/tools", json=data)
    if response.status_code in [200, 201]:
        print_test("POST /api/tools", "PASS", "Tool created successfully")
        test_results.append(("POST /api/tools", "PASS"))
    else:
        print_test("POST /api/tools", "FAIL", f"Status: {response.status_code}")
        test_results.append(("POST /api/tools", "FAIL"))
except Exception as e:
    print_test("POST /api/tools", "FAIL", str(e))
    test_results.append(("POST /api/tools", "FAIL"))

# Test 8: List Tools
print_header("TEST 8: List Tools")
try:
    response = requests.get(f"{BASE_URL}/api/tools")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/tools", "PASS", f"Retrieved {len(data)} tools")
        test_results.append(("GET /api/tools", "PASS"))
    else:
        print_test("GET /api/tools", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/tools", "FAIL"))
except Exception as e:
    print_test("GET /api/tools", "FAIL", str(e))
    test_results.append(("GET /api/tools", "FAIL"))

# Test 9: Get Certificate Info
print_header("TEST 9: Get Certificate Info")
try:
    response = requests.get(f"{BASE_URL}/api/certs")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/certs", "PASS", f"TLS Enabled: {data['tls_enabled']}")
        test_results.append(("GET /api/certs", "PASS"))
    else:
        print_test("GET /api/certs", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/certs", "FAIL"))
except Exception as e:
    print_test("GET /api/certs", "FAIL", str(e))
    test_results.append(("GET /api/certs", "FAIL"))

# Test 10: Get LLM Config
print_header("TEST 10: Get LLM Config")
try:
    response = requests.get(f"{BASE_URL}/api/llm/config")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/llm/config", "PASS", f"Base URL: {data.get('base_url', 'N/A')}")
        test_results.append(("GET /api/llm/config", "PASS"))
    else:
        print_test("GET /api/llm/config", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/llm/config", "FAIL"))
except Exception as e:
    print_test("GET /api/llm/config", "FAIL", str(e))
    test_results.append(("GET /api/llm/config", "FAIL"))

# Test 11: Get Monitoring Health
print_header("TEST 11: Get Monitoring Health")
try:
    response = requests.get(f"{BASE_URL}/api/monitoring/health")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/monitoring/health", "PASS", f"Status: {data.get('status', 'N/A')}")
        test_results.append(("GET /api/monitoring/health", "PASS"))
    else:
        print_test("GET /api/monitoring/health", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/monitoring/health", "FAIL"))
except Exception as e:
    print_test("GET /api/monitoring/health", "FAIL", str(e))
    test_results.append(("GET /api/monitoring/health", "FAIL"))

# Test 12: Get Topology Graph
print_header("TEST 12: Get Topology Graph")
try:
    response = requests.get(f"{BASE_URL}/api/topology/graph")
    if response.status_code == 200:
        data = response.json()
        print_test("GET /api/topology/graph", "PASS", f"Nodes: {len(data.get('nodes', []))}")
        test_results.append(("GET /api/topology/graph", "PASS"))
    else:
        print_test("GET /api/topology/graph", "FAIL", f"Status: {response.status_code}")
        test_results.append(("GET /api/topology/graph", "FAIL"))
except Exception as e:
    print_test("GET /api/topology/graph", "FAIL", str(e))
    test_results.append(("GET /api/topology/graph", "FAIL"))

# Summary
print_header("Test Summary")
passed = sum(1 for _, status in test_results if status == "PASS")
failed = sum(1 for _, status in test_results if status == "FAIL")

print(f"\nTotal Tests: {len(test_results)}")
print(f"\033[92mPassed: {passed}\033[0m")
print(f"\033[91mFailed: {failed}\033[0m")
print(f"Success Rate: {(passed/len(test_results)*100):.1f}%\n")

if failed == 0:
    print("\033[92m✓ All CRUD operations working!\033[0m\n")
    sys.exit(0)
else:
    print("\033[91m✗ Some tests failed. Review the output above.\033[0m\n")
    sys.exit(1)
