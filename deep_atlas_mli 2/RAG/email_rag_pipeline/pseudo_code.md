# Pseudo-code for the First Step

```text
INPUT: mailbox file or exported email folder
OUTPUT: JSON file with structured email records

for each email in mailbox:
    # 1. Read the email content
    header = read_sender_and_date(email)
    body = read_main_body(email)

    # 2. Keep the signature as an important field
    signature = extract_signature(body)

    # 3. Remove obvious noise but preserve meaningful signature content
    cleaned_body = remove_quoted_replies(body)
    cleaned_body = remove_html_tags(cleaned_body)

    # 4. Extract key fields
    person_name = detect_person_name(signature)
    company = detect_company(signature)
    job_title = detect_job_title(signature)
    contact_info = detect_contact_info(signature)

    # 5. Build one structured record
    record = {
        "sender": header.sender,
        "date": header.date,
        "body": cleaned_body,
        "signature": signature,
        "person_name": person_name,
        "company": company,
        "job_title": job_title,
        "contact_info": contact_info
    }

    # 6. Save the record for later RAG indexing
    append record to output list

save output list as JSON
```

## Notes
- The signature is not treated as noise here.
- It is treated as a high-value field because it contains recruiter/company/job information.
- The first step is about building a clean structured dataset, not yet building the full retrieval system.
