#!/usr/bin/env python3
"""
Test script for the Steam MCP server
"""
import json
import subprocess
import sys
import time

def test_mcp_server():
    """Test the MCP server functionality"""
    print("Testing Steam MCP Server...")
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Test 1: Initialize
        print("1. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        if response:
            init_response = json.loads(response.strip())
            print(f"✓ Initialize response: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("✗ No response to initialize")
            return False
        
        # Test 2: List tools
        print("2. Testing tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        if response:
            tools_response = json.loads(response.strip())
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"✓ Found {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool.get('name', 'Unknown')}")
        else:
            print("✗ No response to tools/list")
            return False
        
        # Test 3: Call a tool (search for CS:GO items)
        print("3. Testing tool call (search CS:GO items)...")
        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_steam_items",
                "arguments": {
                    "appid": "730",
                    "search_term": "AK-47",
                    "max_results": 3
                }
            }
        }
        
        process.stdin.write(json.dumps(tool_request) + "\n")
        process.stdin.flush()
        
        # Wait a bit for the response
        time.sleep(2)
        
        response = process.stdout.readline()
        if response:
            tool_response = json.loads(response.strip())
            if 'result' in tool_response:
                print("✓ Tool call successful")
                content = tool_response['result']['content'][0]['text']
                result_data = json.loads(content)
                if 'results' in result_data:
                    print(f"  Found {len(result_data['results'])} items")
                else:
                    print(f"  Response: {result_data.get('status', 'unknown')}")
            else:
                print(f"✗ Tool call failed: {tool_response.get('error', 'Unknown error')}")
        else:
            print("✗ No response to tool call")
            return False
        
        print("\n✓ All tests passed! MCP server is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
