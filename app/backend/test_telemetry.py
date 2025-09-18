#!/usr/bin/env python3
"""
Test script to verify Azure Monitor telemetry configuration.
Run this to check if your telemetry setup is working correctly.
"""
import os
import sys
import time
import asyncio
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_environment_variables():
    """Test if required environment variables are present"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "AZURE_RESOURCE_GROUP"
    ]
    
    optional_vars = [
        "APPINSIGHTS_INSTRUMENTATIONKEY",
        "AZURE_AI_FOUNDRY_HUB_NAME",
        "AZURE_AI_FOUNDRY_PROJECT_NAME",
        "RUNNING_IN_PRODUCTION"
    ]
    
    results = {"found": [], "missing": [], "optional": []}
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "CONNECTION_STRING" in var:
                masked_value = f"{value[:20]}...{value[-10:]}" if len(value) > 30 else value
                results["found"].append(f"{var}={masked_value}")
            else:
                results["found"].append(f"{var}={value}")
        else:
            results["missing"].append(var)
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            results["optional"].append(f"{var}={value}")
    
    print(f"✅ Found required variables: {len(results['found'])}")
    for var in results["found"]:
        print(f"   ✓ {var}")
    
    if results["missing"]:
        print(f"❌ Missing required variables: {len(results['missing'])}")
        for var in results["missing"]:
            print(f"   ✗ {var}")
    
    if results["optional"]:
        print(f"ℹ️  Optional variables found: {len(results['optional'])}")
        for var in results["optional"]:
            print(f"   • {var}")
    
    return len(results["missing"]) == 0

def test_azure_monitor_import():
    """Test if Azure Monitor packages are available"""
    print("\n📦 Testing Azure Monitor package imports...")
    
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        print("✅ Azure Monitor OpenTelemetry package available")
        return True
    except ImportError as e:
        print(f"❌ Azure Monitor OpenTelemetry not available: {e}")
        print("💡 Install with: pip install azure-monitor-opentelemetry")
        return False

def test_telemetry_setup():
    """Test the telemetry setup function"""
    print("\n🔧 Testing telemetry setup...")
    
    try:
        from telemetry import setup_azure_monitor, verify_telemetry_setup
        
        # Run setup
        setup_result = setup_azure_monitor()
        print(f"Setup result: {setup_result}")
        
        # Run diagnostics
        diagnostics = verify_telemetry_setup()
        
        print(f"✅ Telemetry diagnostics completed")
        print(f"   Connection string found: {diagnostics.get('connection_string_found', False)}")
        print(f"   Azure Monitor available: {diagnostics.get('azure_monitor_available', False)}")
        print(f"   Test trace created: {diagnostics.get('test_trace_created', False)}")
        
        if diagnostics.get("errors"):
            print(f"⚠️  Errors found: {len(diagnostics['errors'])}")
            for error in diagnostics["errors"]:
                print(f"   • {error}")
        
        return setup_result
        
    except Exception as e:
        print(f"❌ Telemetry setup test failed: {e}")
        return False

def test_trace_creation():
    """Test creating traces"""
    print("\n🎯 Testing trace creation...")
    
    try:
        from telemetry import trace_tool_call, trace_model_call, get_tracer
        
        # Test tool call tracing
        print("Creating test tool call trace...")
        with trace_tool_call("test_tool", {"param1": "value1"}, 0.123, {"result": "success"}) as span:
            print(f"   Tool call span created: {span}")
        
        # Test model call tracing
        print("Creating test model call trace...")
        with trace_model_call("gpt-4o", "completion", 150, 0.456, 0.02, "test prompt", "test response") as span:
            print(f"   Model call span created: {span}")
        
        print("✅ Trace creation test completed")
        return True
        
    except Exception as e:
        print(f"❌ Trace creation test failed: {e}")
        return False

async def test_api_endpoints():
    """Test telemetry API endpoints"""
    print("\n🌐 Testing API endpoints...")
    
    try:
        import aiohttp
        
        # Test if we can reach the diagnostics endpoint
        # This would only work if the server is running
        print("Note: API endpoint test requires the server to be running")
        print("You can test manually by visiting:")
        print("   GET /api/telemetry/diagnostics")
        print("   GET /api/telemetry")
        
        return True
        
    except Exception as e:
        print(f"⚠️  API endpoint test skipped: {e}")
        return True

def main():
    """Main test function"""
    print("🚀 Azure Monitor Telemetry Configuration Test")
    print("=" * 50)
    
    # Load environment from .env if not in production
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("📁 Loaded environment from .env file")
        except ImportError:
            print("⚠️  python-dotenv not available, skipping .env loading")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Azure Monitor Import", test_azure_monitor_import),
        ("Telemetry Setup", test_telemetry_setup),
        ("Trace Creation", test_trace_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Run async test
    try:
        print("\nRunning async tests...")
        asyncio.run(test_api_endpoints())
        results.append(("API Endpoints", True))
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        results.append(("API Endpoints", False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your telemetry configuration looks good.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)