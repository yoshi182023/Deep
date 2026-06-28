# Email RAG Project Plan

This folder contains the first-step plan for building a RAG system over your email conversations.

## Goal
Extract and structure the most important fields from each email:
- sender
- date
- body
- signature
- person name
- company
- job title
- contact information

## First-step pipeline
1. Read emails from an .mbox file or a folder of exported emails.
2. Parse headers and body.
3. Extract signature and contact details.
4. Create a structured record for each email.
5. Save the records as JSON for later embedding and retrieval.

## Suggested output schema
```json
{
  "id": "unique-email-id",
  "sender": "recruiter@example.com",
  "date": "2026-06-28",
  "body": "Email content here",
  "signature": "John Smith\nRecruiter at ABC Corp",
  "person_name": "John Smith",
  "company": "ABC Corp",
  "job_title": "Recruiter",
  "contact_info": "john@example.com"
}
```
