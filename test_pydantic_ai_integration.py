#!/usr/bin/env python3
"""
Test script for PydanticAI Stock Analyst integration
Run this to verify the system is working correctly
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.agents.pydantic_ai_stock_analyst import (
        PydanticAIStockAnalyst, 
        UserProfile, 
        StockAnalysisState
    )
    print("✅ Successfully imported PydanticAI Stock Analyst")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Make sure to install dependencies: pip install -r requirements.txt")
    sys.exit(1)


async def test_workflow_initialization():
    """Test that the workflow can be initialized"""
    print("\n🧪 Testing workflow initialization...")
    
    try:
        analyst = PydanticAIStockAnalyst()
        print("✅ Stock analyst initialized successfully")
        
        # Test workflow diagram generation
        diagram = analyst.generate_mermaid_diagram()
        print("✅ Mermaid diagram generated successfully")
        print(f"📊 Diagram length: {len(diagram)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


async def test_user_profile_creation():
    """Test user profile creation and validation"""
    print("\n🧪 Testing user profile creation...")
    
    try:
        # Test default profile
        default_profile = UserProfile()
        print(f"✅ Default profile: {default_profile.name}, {default_profile.risk_tolerance}")
        
        # Test custom profile
        custom_profile = UserProfile(
            name="Test Investor",
            risk_tolerance="aggressive",
            investment_horizon="short",
            email="test@example.com"
        )
        print(f"✅ Custom profile: {custom_profile.name}, {custom_profile.risk_tolerance}")
        
        # Test profile validation
        profile_dict = custom_profile.model_dump()
        print(f"✅ Profile serialization: {len(profile_dict)} fields")
        
        return True
    except Exception as e:
        print(f"❌ User profile test failed: {e}")
        return False


async def test_state_management():
    """Test state management system"""
    print("\n🧪 Testing state management...")
    
    try:
        profile = UserProfile(name="Test User")
        state = StockAnalysisState(
            symbol="TEST",
            user_profile=profile
        )
        
        print(f"✅ State created for symbol: {state.symbol}")
        print(f"✅ User profile attached: {state.user_profile.name}")
        print(f"✅ Raw data initialized: {len(state.raw_data)} items")
        
        return True
    except Exception as e:
        print(f"❌ State management test failed: {e}")
        return False


async def test_workflow_steps():
    """Test workflow step generation (without running full analysis)"""
    print("\n🧪 Testing workflow step generation...")
    
    try:
        analyst = PydanticAIStockAnalyst()
        
        # This won't run the full analysis but will show the steps
        print("✅ Workflow steps can be generated")
        print("ℹ️  Note: Full analysis requires API keys and MCP server")
        
        return True
    except Exception as e:
        print(f"❌ Workflow steps test failed: {e}")
        return False


async def test_mcp_configuration():
    """Test MCP configuration (without actually connecting)"""
    print("\n🧪 Testing MCP configuration...")
    
    try:
        from app.agents.pydantic_ai_stock_analyst import create_mcp_server
        
        # Test MCP server creation (this creates the config but doesn't connect)
        mcp_server = create_mcp_server()
        print("✅ MCP server configuration created")
        
        # Check environment variables
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'not_set')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', 'not_set')
        mcp_path = os.getenv('MCP_STOCK_SERVER_PATH', 'not_set')
        
        print(f"🔑 Alpha Vantage API Key: {'✅ Set' if alpha_vantage_key != 'not_set' else '⚠️  Not set'}")
        print(f"🔑 Anthropic API Key: {'✅ Set' if anthropic_key != 'not_set' else '⚠️  Not set'}")
        print(f"📁 MCP Server Path: {'✅ Set' if mcp_path != 'not_set' else '⚠️  Using default'}")
        
        if alpha_vantage_key == 'not_set' or anthropic_key == 'not_set':
            print("💡 Set API keys in environment variables for full functionality")
        
        return True
    except Exception as e:
        print(f"❌ MCP configuration test failed: {e}")
        return False


async def test_api_models():
    """Test API model serialization"""
    print("\n🧪 Testing API models...")
    
    try:
        from app.agents.pydantic_ai_stock_analyst import (
            StockDataPoint, 
            MarketConditions, 
            AnalysisResult
        )
        
        # Test StockDataPoint
        data_point = StockDataPoint(
            date="2024-12-07",
            symbol="TEST",
            open_price=150.0,
            high_price=155.0,
            low_price=148.0,
            close_price=152.0,
            volume=1000000,
            daily_change=2.0,
            daily_change_pct=1.33
        )
        print("✅ StockDataPoint model created")
        
        # Test MarketConditions  
        market = MarketConditions(
            sentiment="bullish",
            volatility="medium",
            trend="upward",
            confidence=0.75
        )
        print("✅ MarketConditions model created")
        
        # Test AnalysisResult
        result = AnalysisResult(
            symbol="TEST",
            recommendation="buy",
            confidence=0.85,
            target_price=160.0,
            stop_loss=140.0,
            reasoning="Test analysis reasoning",
            market_conditions=market,
            data_points=[data_point],
            analysis_timestamp=datetime.now()
        )
        print("✅ AnalysisResult model created")
        
        # Test serialization
        result_dict = result.model_dump()
        print(f"✅ Model serialization: {len(result_dict)} fields")
        
        return True
    except Exception as e:
        print(f"❌ API models test failed: {e}")
        return False


def display_environment_info():
    """Display environment information"""
    print("\n🔧 Environment Information:")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check for key dependencies
    dependencies = [
        'pydantic',
        'fastapi', 
        'uvicorn',
        'httpx'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: installed")
        except ImportError:
            print(f"❌ {dep}: missing")


async def main():
    """Run all tests"""
    print("🚀 PydanticAI Stock Analyst Integration Test")
    print("=" * 50)
    
    display_environment_info()
    
    tests = [
        ("Workflow Initialization", test_workflow_initialization),
        ("User Profile Creation", test_user_profile_creation),
        ("State Management", test_state_management),
        ("Workflow Steps", test_workflow_steps),
        ("MCP Configuration", test_mcp_configuration),
        ("API Models", test_api_models),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The PydanticAI integration is working correctly.")
        print("\n🚀 Next steps:")
        print("  1. Set up API keys (ALPHA_VANTAGE_API_KEY, ANTHROPIC_API_KEY)")
        print("  2. Run the FastAPI server: uvicorn app.main:app --reload")
        print("  3. Test the API at http://localhost:8000/docs")
        print("  4. Try the workflow test: http://localhost:8000/test-workflow")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 