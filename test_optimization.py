#!/usr/bin/env python3
"""
Quick validation script to test the new optimization features.
Run this after activating your virtual environment.
"""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from github_bot.utils.cache import SimpleCache, github_cache
        print("✅ cache.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import cache.py: {e}")
        return False
    
    try:
        from github_bot.utils.github_service import GitHubService
        print("✅ github_service.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import github_service.py: {e}")
        return False
    
    try:
        from github_bot.utils.chat_service import ChatService
        print("✅ chat_service.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import chat_service.py: {e}")
        return False
    
    return True

def test_cache():
    """Test cache functionality."""
    print("\nTesting cache...")
    
    try:
        from github_bot.utils.cache import SimpleCache
        
        cache = SimpleCache(default_ttl_seconds=10)
        
        # Test set and get
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        
        if value == "test_value":
            print("✅ Cache set/get works")
        else:
            print("❌ Cache get returned wrong value")
            return False
        
        # Test expiration
        cache.set("expire_key", "expire_value", ttl_seconds=0)
        import time
        time.sleep(0.1)
        expired_value = cache.get("expire_key")
        
        if expired_value is None:
            print("✅ Cache expiration works")
        else:
            print("❌ Cache expiration failed")
            return False
        
        # Test stats
        stats = cache.get_stats()
        print(f"✅ Cache stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def test_github_service():
    """Test GitHubService initialization."""
    print("\nTesting GitHubService...")
    
    try:
        from github_bot.utils.github_service import GitHubService
        
        # Test initialization
        service = GitHubService(use_cache=True)
        print("✅ GitHubService initialized with caching")
        
        service_no_cache = GitHubService(use_cache=False)
        print("✅ GitHubService initialized without caching")
        
        # Test new methods exist
        methods = [
            'get_repository_tree',
            'get_important_files',
            'extract_code_summary',
            'get_smart_repository_context',
            '_get_file_type'
        ]
        
        for method in methods:
            if hasattr(service, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHubService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("OPTIMIZATION VALIDATION SCRIPT")
    print("=" * 60)
    
    results = []
    
    results.append(("Import Test", test_imports()))
    results.append(("Cache Test", test_cache()))
    results.append(("GitHubService Test", test_github_service()))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The optimization is ready to use.")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
