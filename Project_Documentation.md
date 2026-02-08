
---

# ✅ 3. PROJECT DOCUMENTATION

```md
# AURELIUS — Project Documentation

## 1. Introduction
AURELIUS is a smart feedback management system that captures structured user feedback through a conversational chatbot and presents insights via an executive-style dashboard.

The project focuses on:
- User experience
- Data-driven decision making
- Clean system design

---

## 2. System Architecture

- **Client Layer:** Browser-based UI (HTML/CSS/JS)
- **Application Layer:** Flask backend
- **Data Layer:** SQLite database
- **Analytics Layer:** Sentiment analysis + Chart.js
- **Reporting Layer:** PDF generation via ReportLab

---

## 3. Workflow

1. User interacts with chatbot
2. System collects:
   - Username
   - Rating
   - Experience
   - Recommendation
3. Feedback is analyzed using NLP
4. Data is stored in SQLite
5. Admin dashboard displays:
   - Statistics
   - Sentiment chart
   - Recent feedback
6. Admin can export PDF report

---

## 4. Sentiment Analysis

Sentiment polarity is calculated using TextBlob:
- Positive
- Neutral
- Negative

This allows qualitative feedback to be quantified.

---

## 5. Security & Reliability

- Server-side validation
- Controlled session-based interaction
- Read-only admin analytics
- No third-party data sharing

---

## 6. Future Enhancements

- Admin authentication
- Role-based access
- Advanced analytics
- Cloud deployment
- API integration

---

## 7. Conclusion

AURELIUS demonstrates how conversational UX and analytics can coexist in a premium, production-style application suitable for enterprise feedback systems.
