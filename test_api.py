#!/usr/bin/env python
"""
Test script for AIpanel API.

This script tests the basic functionality of the AIpanel API.
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional

import httpx


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test AIpanel API")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000", 
        help="Base URL of AIpanel API"
    )
    parser.add_argument(
        "--api-key", 
        default="test_key", 
        help="API key for authentication"
    )
    parser.add_argument(
        "--prompt", 
        default="What is the status of our top contracts?", 
        help="Prompt to send to the API"
    )
    parser.add_argument(
        "--agent", 
        default="zain_agent", 
        help="Agent to use for the request"
    )
    parser.add_argument(
        "--test", 
        default="chat", 
        choices=["health", "chat", "topology", "config", "all"], 
        help="Test to run"
    )
    
    return parser.parse_args()


async def test_health(client: httpx.AsyncClient, base_url: str) -> bool:
    """
    Test health endpoint.
    
    Args:
        client: HTTP client
        base_url: Base URL
        
    Returns:
        True if successful, False otherwise
    """
    print("\n=== Testing Health Endpoint ===")
    
    try:
        response = await client.get(f"{base_url}/api/health")
        response.raise_for_status()
        
        result = response.json()
        print(f"Health status: {result['status']}")
        print(f"Version: {result['version']}")
        
        return True
        
    except Exception as e:
        print(f"Error testing health endpoint: {str(e)}")
        return False


async def test_chat(
    client: httpx.AsyncClient, 
    base_url: str, 
    prompt: str, 
    agent: str
) -> bool:
    """
    Test chat endpoint.
    
    Args:
        client: HTTP client
        base_url: Base URL
        prompt: Prompt to send
        agent: Agent to use
        
    Returns:
        True if successful, False otherwise
    """
    print("\n=== Testing Chat Endpoint ===")
    
    try:
        # Use test endpoint to avoid authentication
        response = await client.post(
            f"{base_url}/api/chat/test",
            json={
                "prompt": prompt,
                "agent": agent,
                "user_id": "test_user"
            }
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"Answer: {result['answer']}")
        print(f"Trace ID: {result['trace_id']}")
        
        if "sources" in result and result["sources"]:
            print("\nSources:")
            for source in result["sources"]:
                print(f"- {source['type']}: {source['name']}")
        
        return True
        
    except Exception as e:
        print(f"Error testing chat endpoint: {str(e)}")
        return False


async def test_topology(client: httpx.AsyncClient, base_url: str, agent: str) -> bool:
    """
    Test topology endpoint.
    
    Args:
        client: HTTP client
        base_url: Base URL
        agent: Agent to use
        
    Returns:
        True if successful, False otherwise
    """
    print("\n=== Testing Topology Endpoint ===")
    
    try:
        response = await client.get(
            f"{base_url}/api/topology",
            params={"agent": agent}
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"Topology has {len(result['nodes'])} nodes and {len(result['edges'])} edges")
        
        # Print node types
        node_types = {}
        for node in result["nodes"]:
            node_type = node["type"]
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("\nNode types:")
        for node_type, count in node_types.items():
            print(f"- {node_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"Error testing topology endpoint: {str(e)}")
        return False


async def test_config(client: httpx.AsyncClient, base_url: str) -> bool:
    """
    Test configuration endpoints.
    
    Args:
        client: HTTP client
        base_url: Base URL
        
    Returns:
        True if successful, False otherwise
    """
    print("\n=== Testing Configuration Endpoints ===")
    
    try:
        # Test LLM connections
        print("\nLLM Connections:")
        response = await client.get(f"{base_url}/api/config/llm-connections")
        response.raise_for_status()
        
        connections = response.json()
        print(f"Found {len(connections)} LLM connections")
        
        # Test agents
        print("\nAgents:")
        response = await client.get(f"{base_url}/api/config/agents")
        response.raise_for_status()
        
        agents = response.json()
        print(f"Found {len(agents)} agents")
        
        # Test tools
        print("\nTools:")
        response = await client.get(f"{base_url}/api/config/tools")
        response.raise_for_status()
        
        tools = response.json()
        print(f"Found {len(tools)} tools")
        
        return True
        
    except Exception as e:
        print(f"Error testing configuration endpoints: {str(e)}")
        return False


async def main():
    """Main function."""
    args = parse_args()
    
    # Create HTTP client
    async with httpx.AsyncClient(
        headers={"X-API-Key": args.api_key},
        timeout=60.0
    ) as client:
        # Run tests
        if args.test == "health" or args.test == "all":
            await test_health(client, args.url)
        
        if args.test == "chat" or args.test == "all":
            await test_chat(client, args.url, args.prompt, args.agent)
        
        if args.test == "topology" or args.test == "all":
            await test_topology(client, args.url, args.agent)
        
        if args.test == "config" or args.test == "all":
            await test_config(client, args.url)


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(main())
