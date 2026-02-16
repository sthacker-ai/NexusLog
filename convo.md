# NexusLog Conversation Log

---

## 2026-02-08 13:40:19 IST

Voice note processing fix was confirmed working.

Request: Every time I write something, add it to convo.md in project root. File should update with what I ask or say, in markdown format with timestamp and message content.

---

## 2026-02-08 21:47:48 IST

what is next for us now?

---

## 2026-02-08 21:51:30 IST

if i send a youtube video link and ask it to summarize(via voice note or via text message) what would it do?
if i send an image, ask(via voice note or via text message) it to extract information from it, summarize, what would it do?

---

## 2026-02-08 21:57:11 IST

essentially what I want is, each input, be it in any form or any combination, need to be processed by AI and the ask is to be understood, as to what is the next action.

so video as a link or uploaded to bot along with voice note or text, i expect that the ask/action is understood and performed. then same as what we did earlier, is it one entry or two or 4 or 5, it needs to decide that and add accordingly

same applies to image or link to an image and same applies to any other link that is shared there

---

## 2026-02-09 15:35:58 IST

Plan approved. Dependencies (yt-dlp, trafilatura) and increased API usage acceptable.

---

## 2026-02-14 11:03:00 IST

1. Model Stacking (Deferred/Backburner): Priority-based model usage (1->7).
2. Simplified Processing:
   - NO Summarization for anything.
   - Text/Voice: Only correct grammar/spelling. Do not change message content.
   - Video/Image/Links: Save as is with metadata (title, etc.). Do not extract content.
   - Display: Embed images/videos directly in NexusLog page. Open articles in new tab.
3. Google Sheet Integration (Trading Journal):
   - Trigger: "Trading journal" keywords.
   - Logic: Find row by Date + Stock Name.
   - Action: Update Column L (Commentary) and M (Lessons).
   - Sheet ID: `1dNB-i8GoYDR4upLYN-swX6G2wZn1rCnEE7SDnRf1BP8`

Ask: First make a plan, get approval, then work one item at a time.
