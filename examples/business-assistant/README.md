# Business Assistant Example

A specialized agent for email triage, meeting scheduling, and report generation.

## Overview

This example demonstrates:
- **Email triage** — Categorizing and prioritizing emails
- **Meeting scheduling** — Finding available times, sending invites
- **Report generation** — Creating summaries from data
- **Task management** — Tracking deadlines and priorities

## Setup

```bash
cp -r examples/business-assistant my-business-agent/
cd my-business-agent
docker compose up -d
```

## Usage Examples

### Email Triage

**User:** Check my inbox and prioritize

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "agentmail.list_emails", "arguments": "{\"folder\": \"inbox\", \"limit\": 20}"}}
]}
```

**Tool result:** [20 emails]

**Agent:** I see 20 unread emails. Here's the priority breakdown:

**🔴 Urgent (3):**
1. Client X — Contract signature needed by EOD
2. Server alert — Production database at 95% capacity
3. Legal — Compliance deadline tomorrow

**🟡 Important (7):**
4. Team meeting — Agenda for Friday
5. Vendor invoice — Due next week
6. Project update — Milestone 3 complete
...

**🟢 Low priority (10):**
11. Newsletter — Industry trends
12. Marketing — New blog post
...

Want me to draft responses for the urgent ones? `[mood: focused]`

### Meeting Scheduling

**User:** Schedule a 1-hour meeting with the design team next week

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "calendar.find_availability", "arguments": "{\"attendees\": [\"design-team\"], \"duration\": 60, \"range\": \"next_week\"}"}}
]}
```

**Tool result:** Available slots: Mon 2-3pm, Tue 10-11am, Wed 3-4pm, Thu 9-10am

**Agent:** Found 4 available slots:

- **Monday 2:00-3:00 PM**
- **Tuesday 10:00-11:00 AM** ⭐ (recommended — early in week)
- **Wednesday 3:00-4:00 PM**
- **Thursday 9:00-10:00 AM**

Which one works best? I'll send the invite. `[mood: neutral]`

### Report Generation

**User:** Generate a weekly sales report

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "database.query", "arguments": "{\"sql\": \"SELECT * FROM sales WHERE date >= NOW() - INTERVAL 7 DAY\"}"}}
]}
```

**Tool result:** [sales data]

**Agent:** # Weekly Sales Report (Aug 1-7, 2026)

## Summary
- **Total Revenue:** $127,450
- **Transactions:** 342
- **Average Order Value:** $372.66
- **Growth:** +12% vs last week

## Top Products
1. Product A — $45,200 (35.5%)
2. Product B — $32,100 (25.2%)
3. Product C — $28,900 (22.7%)

## Insights
- Strong performance in Product A (new marketing campaign)
- Product C declining (-8% vs last week) — investigate?

Want me to email this to the team? `[mood: proud]`

## Custom Skills

### email-triage

```python
def prioritize_emails(emails: list):
    """Categorize emails by urgency."""
    categories = {"urgent": [], "important": [], "low": []}
    
    for email in emails:
        urgency = classify_urgency(email)
        categories[urgency].append(email)
    
    return categories
```

### meeting-scheduler

```python
def schedule_meeting(attendees: list, duration: int):
    """Find available time and send invite."""
    slots = find_availability(attendees, duration)
    best_slot = select_best_slot(slots)
    send_invite(best_slot, attendees)
    return best_slot
```

## License

MIT
