#!/usr/bin/env python3
"""
Test script to verify password hashing works correctly
"""
import sys
import os

# Add the services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../services/user_service'))

from auth import get_password_hash, verify_password

def test_password_hashing():
    """Test password hashing with various passwords"""
    test_passwords = [
        "securepass123",
        "short",
        "a" * 100,  # Very long password
        "test@123!",
        "password with spaces",
    ]
    
    print("Testing password hashing...")
    print("=" * 60)
    
    for password in test_passwords:
        try:
            print(f"\nTesting password: '{password[:20]}...' (length: {len(password)})")
            print(f"  Bytes: {len(password.encode('utf-8'))}")
            
            # Hash the password
            hashed = get_password_hash(password)
            print(f"  ✓ Hash successful: {hashed[:50]}...")
            
            # Verify the password
            is_valid = verify_password(password, hashed)
            if is_valid:
                print(f"  ✓ Verification successful")
            else:
                print(f"  ✗ Verification failed!")
                return False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    return True

if __name__ == "__main__":
    success = test_password_hashing()
    sys.exit(0 if success else 1)




