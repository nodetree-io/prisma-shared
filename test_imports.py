#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly.
"""

def test_basic_imports():
    """Test basic package imports."""
    print("Testing basic imports...")
    
    try:
        import prisma_common
        print(f"✅ Main package imported successfully (version: {prisma_common.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import main package: {e}")
        return False
    
    return True

def test_config_imports():
    """Test configuration imports."""
    print("\nTesting config imports...")
    
    try:
        from prisma_common.config import Settings
        print("✅ Settings imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Settings: {e}")
        return False
    
    try:
        from prisma_common import get_settings
        print("✅ get_settings imported from main package")
    except ImportError as e:
        print(f"❌ Failed to import get_settings: {e}")
        return False
    
    return True

def test_operators_imports():
    """Test operators imports."""
    print("\nTesting operators imports...")
    
    try:
        from prisma_common.operators.research import DeepResearchOperator
        print("✅ DeepResearchOperator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DeepResearchOperator: {e}")
        return False
    
    try:
        from prisma_common.operators.research.deep_research import DeepResearchOperator
        print("✅ DeepResearchOperator imported via deep path")
    except ImportError as e:
        print(f"❌ Failed to import via deep path: {e}")
        return False
    
    return True

def test_tools_imports():
    """Test tools imports."""
    print("\nTesting tools imports...")
    
    try:
        from prisma_common.tools.gmail import GmailTool
        print("✅ GmailTool imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import GmailTool: {e}")
        return False
    
    return True

def test_utils_imports():
    """Test utils imports."""
    print("\nTesting utils imports...")
    
    try:
        from prisma_common.utils.logging import get_logger
        print("✅ get_logger imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import get_logger: {e}")
        return False
    
    try:
        from prisma_common import get_logger
        print("✅ get_logger imported from main package")
    except ImportError as e:
        print(f"❌ Failed to import get_logger from main package: {e}")
        return False
    
    return True

def test_deep_imports():
    """Test deep import functionality."""
    print("\nTesting deep imports...")
    
    # Test that we can import submodules
    try:
        import prisma_common.operators.research
        print("✅ prisma_common.operators.research imported")
    except ImportError as e:
        print(f"❌ Failed to import research module: {e}")
        return False
    
    try:
        import prisma_common.tools.gmail
        print("✅ prisma_common.tools.gmail imported")
    except ImportError as e:
        print(f"❌ Failed to import gmail module: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 Testing Prisma Common SDK imports...")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_config_imports,
        test_operators_imports,
        test_tools_imports,
        test_utils_imports,
        test_deep_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test {test.__name__} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The SDK structure is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the import structure.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
