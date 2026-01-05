# YouTube API Testing - Quick Reference Card

> **Print this out or keep it open while testing!**

---

## 🎯 Your Task

Get a YouTube Data API key and test that real YouTube data is being fetched.

---

## ⚡ Quick Steps (10 Minutes Total)

### 1. Get API Key (5 min)
```
https://console.cloud.google.com/
→ Create Project
→ Enable "YouTube Data API v3"
→ Create API Key
→ Copy key (starts with AIza...)
```

### 2. Add to .env (30 sec)
```bash
# Edit .env file, replace:
YOUTUBE_API_KEY=your_youtube_api_key_here

# With:
YOUTUBE_API_KEY=AIza...YOUR_KEY
```

### 3. Restart Backend (10 sec)
```bash
# Stop with Ctrl+C, then:
python backend_main.py
```

### 4. Verify (1 min)
```bash
python verify_api_setup.py

# Should see:
# ✓ All checks passed!
# ✓ YouTube API: configured
```

### 5. Test (2 min)
```bash
python test_youtube_api.py

# Should see:
# ✅ REAL API
# 🎉 SUCCESS!
```

---

## 🧪 Quick Tests

### Test 1: Health Check
```bash
curl http://localhost:8000/api/health | grep youtube_api

# Should show:
# "status": "configured"
# "will_use": "real_api"
```

### Test 2: Single Channel
```bash
curl http://localhost:8000/api/test-youtube/@Fireship

# Look for:
# "source": "api"  (NOT "local_fallback")
# "subscriber_count": 3542000  (real number!)
```

### Test 3: Full UI Flow
```
1. Open: http://localhost:5173
2. Click: "Fireship (REAL API TEST)"
3. Click: "Generate Response"
4. Check: Subscribers show ~3,542,000
```

---

## ✅ Success Signs

| Check | What to Look For |
|-------|-----------------|
| **Logs** | `✅ SUCCESS! Fetched REAL data from YouTube Data API v3` |
| **Numbers** | Subscriber counts match current YouTube data |
| **Speed** | Response takes 2-5 seconds (API call delay) |
| **Source** | `"source": "api"` in JSON responses |

---

## ⚠️ Fallback Signs (API NOT Working)

| Check | What You'll See |
|-------|----------------|
| **Logs** | `📦 Using LOCAL FALLBACK data` |
| **Numbers** | Fixed numbers from youtube_profiles.json |
| **Speed** | Instant (< 1 sec) |
| **Source** | `"source": "local_fallback"` |

---

## 🐛 Quick Fixes

### Problem: Still seeing fallback?

```bash
# 1. Check .env has real key (not placeholder)
cat .env | grep YOUTUBE_API_KEY

# 2. Restart backend
# Stop (Ctrl+C) then: python backend_main.py

# 3. Verify API enabled at:
https://console.cloud.google.com/apis/library/youtube.googleapis.com
```

### Problem: "quotaExceeded"

- You used your daily 10,000 quota units
- Wait 24 hours for reset
- Fallback will work automatically!

### Problem: "invalidKey"

```bash
# Regenerate key at:
https://console.cloud.google.com/apis/credentials

# Update .env with new key
# Restart backend
```

---

## 📊 What Gets Tested

### 4 Real YouTube Channels:
1. **Fireship** (~3.5M subs) - Tech
2. **Veritasium** (~16M subs) - Science
3. **MKBHD** (~19M subs) - Tech reviews
4. **3Blue1Brown** (~6M subs) - Math

### What API Returns:
- ✅ Real subscriber count (updated)
- ✅ Video count
- ✅ View count
- ✅ Channel description
- ✅ Thumbnails

### What Agent Uses It For:
- ✅ CPM pricing calculation
- ✅ Engagement multiplier
- ✅ Niche multiplier
- ✅ ROI forecast
- ✅ Authenticity scoring

---

## 📝 Test Email Thread IDs

Use these in the UI:

- `thread_api_test_fireship` - Negotiation
- `thread_api_test_veritasium` - Acceptance
- `thread_api_test_mkbhd` - Bulk deal
- `thread_api_test_3blue1brown` - Clarification

---

## 🎯 Testing Checklist

Before you're done, verify:

- [ ] Health endpoint shows `"status": "configured"`
- [ ] Test script shows "🎉 SUCCESS!"
- [ ] Backend logs show `✅ SUCCESS! Fetched REAL data`
- [ ] UI shows current subscriber counts
- [ ] Can generate responses for all 4 test emails

---

## 📂 Files Created for Testing

```
test_youtube_api.py              # Main test script
verify_api_setup.py              # Verify everything is set up
verify_api_setup.sh              # Bash version
YOUTUBE_API_TESTING_GUIDE.md     # Full detailed guide
TESTING_QUICK_REFERENCE.md       # This file!
```

---

## 🚀 Ready to Test?

```bash
# Step 1: Verify setup
python verify_api_setup.py

# Step 2: Test API
python test_youtube_api.py

# Step 3: Test in UI
# Open http://localhost:5173
# Generate responses for Fireship, Veritasium, etc.
```

---

## 💡 Pro Tips

1. **Use browser DevTools** to see API responses
2. **Check `server.log`** for detailed debugging
3. **Compare subscriber counts** on YouTube to verify it's real data
4. **Test multiple channels** to see different pricing tiers
5. **The fallback is GOOD** - it means the system never crashes!

---

**Questions?** See `YOUTUBE_API_TESTING_GUIDE.md` for full details!
