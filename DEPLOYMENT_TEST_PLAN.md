# 🧪 Deployment Test Plan - Stateless Handler Verification

## ⏰ Test Window: 17:29:57 CDT (When deployment completes)

## 🎯 Test Objectives
1. Verify NO recursion errors occur
2. Confirm stateless handler processes messages atomically
3. Validate GHL integration works with actual field IDs
4. Ensure conversation flow progresses correctly

## 📋 Test Scenarios

### Test 1: Basic Message Processing (HIGH PRIORITY)
**Purpose**: Verify webhook processes single message without loops
```
Send: "Hi"
Expected: Greeting response in detected language
Verify: Check logs for single execution (no loops)
```

### Test 2: Spanish Language Detection
```
Send: "Hola, necesito ayuda"
Expected: Spanish greeting response
Verify: Language field set to "es" in GHL
```

### Test 3: Full Conversation Flow
```
1. Send: "Hello"
   Expected: "Hi! Welcome to AI Outlet Media..."
   
2. Send: "John Smith"
   Expected: "Nice to meet you John Smith! What specific goals..."
   
3. Send: "I want to grow my business"
   Expected: "That's great! What's the biggest challenge..."
   
4. Send: "Getting more customers"
   Expected: "What's your monthly marketing budget?"
   
5. Send: "$500"
   Expected: "Perfect! What's the best email..."
```

### Test 4: Below Budget Rejection
```
Send budget: "$200"
Expected: "I appreciate your interest! Our programs start at $300..."
Verify: Conversation ends gracefully
```

### Test 5: Concurrent Messages (Stress Test)
```
Send 3 messages rapidly:
- Message 1: "Hi"
- Message 2: "My name is Jane"  
- Message 3: "I need help"

Verify: Each processed independently, no cross-contamination
```

## 🔍 Monitoring Checklist

During testing, monitor for:

- [ ] **Trace IDs**: Each message has unique trace, no recursion
- [ ] **Response Time**: Messages processed in < 3 seconds
- [ ] **GHL Updates**: Contact fields updating correctly
- [ ] **Error Logs**: No "Recursion limit" errors
- [ ] **Memory**: No accumulating state between messages

## 📊 Success Criteria

✅ **PASS** if:
- Zero recursion errors in logs
- All messages get responses
- GHL fields update correctly
- No timeout errors

❌ **FAIL** if:
- Any "Recursion limit" error appears
- Messages loop or repeat
- Webhook times out
- GHL fields don't update

## 🚨 Rollback Plan

If critical issues found:
1. Revert commit 4a6a1fb
2. Push revert immediately
3. Investigate in dev environment
4. CEO approval before re-deployment

## 📝 Test Results Template

```markdown
Test Run: [DATE TIME]
Tester: [NAME]

Test 1 - Basic Message: [PASS/FAIL]
- Response time: ___ ms
- Trace ID: ___
- Notes: ___

Test 2 - Spanish: [PASS/FAIL]
- Language detected: ___
- GHL field updated: [YES/NO]

Test 3 - Full Flow: [PASS/FAIL]
- Steps completed: ___/5
- Final state: ___

Test 4 - Budget Rejection: [PASS/FAIL]
- Rejected correctly: [YES/NO]

Test 5 - Concurrent: [PASS/FAIL]
- Messages processed: ___/3
- Any conflicts: [YES/NO]

Overall Result: [PASS/FAIL]
```

## 🎯 Post-Deployment Cleanup

After successful testing:
1. Delete old test files with graph imports
2. Update langgraph.json
3. Remove api/webhook.py (duplicate endpoint)
4. Archive old graph-related code