#!/usr/bin/env python3
"""Test language detection fix."""

import sys
sys.path.append('.')

from booking_agent.utils.nodes import detect_language

# Test cases
test_cases = [
    # Spanish tests
    ("hola", "es", "Single Spanish word 'hola'"),
    ("Hola, necesito ayuda", "es", "Multiple Spanish words"),
    ("¿Cómo estás?", "es", "Spanish with accents"),
    ("gracias", "es", "Single Spanish word 'gracias'"),
    
    # English tests
    ("hello", "en", "English greeting"),
    ("I need help", "en", "English sentence"),
    ("Hello, I need help with my business", "en", "Longer English"),
    
    # Edge cases
    ("", "en", "Empty string defaults to English"),
    ("123", "en", "Numbers default to English"),
    ("hello gracias", "es", "Mixed - has 1 Spanish indicator"),
    ("I went to see the hola dancers", "es", "English with Spanish word"),
]

print("🧪 Testing Language Detection Fix (>= 1)\n")

passed = 0
failed = 0

for text, expected, description in test_cases:
    result = detect_language(text)
    status = "✅" if result == expected else "❌"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} '{text}' → {result} (expected: {expected})")
    print(f"   {description}")
    print()

print(f"\n📊 Summary: {passed} passed, {failed} failed")

# Additional edge case analysis
print("\n🔍 Edge Case Analysis:")
print("The >= 1 threshold means ANY Spanish indicator triggers Spanish detection.")
print("This could cause false positives if English text contains Spanish words.")
print("Example: 'I love salsa dancing' would NOT trigger Spanish (no indicators)")
print("But: 'I said hola to my friend' WOULD trigger Spanish (has 'hola')")