# ⚡ QUICK START - Testing Critical Fixes

## 🚀 30-Second Setup

```bash
# Terminal 1: Backend
cd backend/orchestrator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

**Then**: Open http://localhost:3000

---

## ✅ 5-Minute Verification

### Check 1: Timeout Sync ✓
```bash
curl http://localhost:8000/api/config/timeout | jq
# Look for: "frontend_timeout_ms": 125000
```

### Check 2: Error Codes ✓
```bash
curl http://localhost:8000/api/chat/ui/conversations/invalid | jq '.error_code'
# Look for: "CONVERSATION_NOT_FOUND" (not a 500 error)
```

### Check 3: Config Status ✓
```bash
curl http://localhost:8000/api/config/status | jq
# Look for: "llm_configured": true, "llm_timeout_seconds": 120
```

### Check 4: Soft Delete ✓
1. Open Chat Studio
2. Create a conversation
3. Delete it
4. List conversations
5. **Deleted conversation should NOT appear** ✓

### Check 5: Error Message ✓
1. Stop your LLM server
2. Try to load models in Chat Studio
3. Should see error with suggestions
4. **NOT a raw exception** ✓

---

## 📋 What Was Fixed

| # | Issue | Fix |
|---|-------|-----|
| 1 | Frontend timeout hardcoded | ✅ Now reads from backend `/api/config/timeout` |
| 2 | Error responses inconsistent | ✅ Now include `error_code` enum + suggestions |
| 3 | Config changes don't persist | ✅ Written to `.env`, survives restart |
| 4 | Deleted items show in lists | ✅ Soft delete filter added |
| 5 | Transaction safety unclear | ✅ Verified safe pattern used |

---

## 🐛 If Something's Wrong

### Frontend not loading config
- Check browser console (F12)
- Look for: `[ChatStudio] Loaded config - timeout: XXX ms`
- If missing: Backend not returning `/api/config/timeout` endpoint

### Error responses not showing error_code
- Check API response in Network tab
- Should have `"error_code": "ERROR_NAME"` field
- If missing: chat_ui.py not imported error_handling module

### Deleted conversations still showing
- Check database directly
- Run: `sqlite3 backend/orchestrator/orchestrator.db`
- Query: `SELECT id, is_deleted FROM conversations;`
- Deleted should have `is_deleted = 1`

### Timeout not changing when .env updated
- Restart backend completely
- Check: `curl http://localhost:8000/api/config/timeout`
- Should show new value

---

## 📚 DETAILED GUIDES

For more information, see:
- **CRITICAL_FIXES_SUMMARY.md** - What was fixed and why
- **TESTING_GUIDE.md** - Full test scenarios with curl commands
- **IMPLEMENTATION_DETAILS.md** - Code changes made
- **FINAL_STATUS_REPORT.md** - Overall status and next steps

---

## 🎯 SUCCESS CRITERIA

All 5 fixes are working if:
- ✅ Timeout shows correctly in error messages
- ✅ Error responses include error_code field
- ✅ Config changes appear in next API call
- ✅ Deleted conversations don't appear in list
- ✅ No raw exceptions in error responses

---

## 🔄 Test Flow (2 minutes)

```
1. Load Chat Studio
   → Check console for timeout message
   
2. Load models
   → Should work or show error with suggestions
   
3. Delete a conversation
   → Should disappear from list
   
4. Check API response
   → Should have error_code if error
   
5. Update .env + restart backend
   → New timeout should appear in config endpoint
```

**If all 5 steps pass → All fixes working ✓**

---

## 💡 Pro Tips

- Use `curl` to test endpoints directly
- Use `jq` to pretty-print JSON: `curl ... | jq`
- Check DevTools Network tab to see API responses
- Check browser console for [ChatStudio] logs
- Check backend terminal for INFO/ERROR logs

---

## ❓ FAQ

**Q: Do I need to restart frontend after backend changes?**  
A: No, but refresh browser (F5) to reload JavaScript

**Q: Will these changes break existing integrations?**  
A: No, all changes are backward compatible

**Q: Do I need to recreate the database?**  
A: No, no schema changes made

**Q: What if frontend doesn't load new timeout?**  
A: Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

**Q: Can I test without LLM server?**  
A: Yes, you'll see error messages (which proves fixes working)

---

## ✨ That's it!

The 5 critical/moderate concerns have been fixed and documented.  
All endpoints are ready for testing.

**Next**: Follow TESTING_GUIDE.md for detailed test scenarios.
