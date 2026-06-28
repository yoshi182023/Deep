import json
import os
import re
import mailbox
from pathlib import Path
from typing import Dict, List, Optional
from email.parser import Parser as EmailParser
from email.utils import parsedate_to_datetime


class EmailProcessor:
    """Parse emails and extract the fields needed for the first RAG step."""

    def __init__(self, input_path: str):
        self.input_path = Path(input_path)

    def parse(self) -> List[Dict]:
        """Parse the input mailbox and return a list of structured email records."""
        records: List[Dict] = []

        if self.input_path.is_file():
            # Try to parse as mbox (works for .mbox files and bare mbox format files like "Inbox")
            records.extend(self._parse_mbox_file(self.input_path))
        elif self.input_path.is_dir():
            for file_path in self.input_path.glob("*.eml"):
                records.extend(self._parse_eml_file(file_path))
        return records

    def _parse_mbox_file(self, path: Path) -> List[Dict]:
        """Parse an .mbox file and extract all email records."""
        records = []
        try:
            mbox = mailbox.mbox(str(path))
            for idx, msg in enumerate(mbox):
                record = self._extract_email_record(msg, idx)
                if record:
                    records.append(record)
        except Exception as e:
            print(f"Error parsing .mbox file {path}: {e}")
        return records

    def _parse_eml_file(self, path: Path) -> List[Dict]:
        """Parse a single .eml file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                msg = EmailParser().parsestr(f.read())
            record = self._extract_email_record(msg, 0)
            return [record] if record else []
        except Exception as e:
            print(f"Error parsing .eml file {path}: {e}")
            return []

    def _extract_email_record(self, msg, idx: int) -> Optional[Dict]:
        """Extract structured fields from a single email message."""
        try:
            sender = msg.get("From", "")
            date_str = msg.get("Date", "")
            # Format date to MM-DD format
            date = self._format_date(date_str)
            subject = msg.get("Subject", "")
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
            # Extract signature and clean body
            signature = self.extract_signature(body)
            cleaned_body = self.remove_quoted_replies(body)
            
            # Extract key fields from signature
            person_name = self.extract_person_name(signature)
            company = self.extract_company(signature)
            job_title = self.extract_job_title(signature)
            contact_info = self.extract_contact_info(signature, sender)
            
            return {
                "id": f"email_{idx}",
                "sender": sender,
                "date": date,
                "subject": subject,
                "body": cleaned_body.strip(),
                "signature": signature.strip(),
                "person_name": person_name,
                "company": company,
                "job_title": job_title,
                "contact_info": contact_info,
            }
        except Exception as e:
            print(f"Error extracting record: {e}")
            return None

    def _format_date(self, date_str: str) -> str:
        """Format email date to MM-DD format."""
        if not date_str:
            return ""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%m-%d")
        except Exception:
            # If parsing fails, try simple regex extraction
            match = re.search(r"(\d{1,2})\s+(\w+)\s+\d{4}", date_str)
            if match:
                day = match.group(1).zfill(2)
                month_str = match.group(2)
                months = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                         "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                         "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                month = months.get(month_str, "")
                if month:
                    return f"{month}-{day}"
            return date_str

    def extract_signature(self, body: str) -> str:
        """Extract signature from email body. Keep the last block after '--' if present."""
        # Simple heuristic: if there's a '--' separator, take everything after it
        if "--" in body:
            parts = body.split("--")
            return parts[-1].strip()
        # Otherwise, take the last few lines
        lines = body.strip().split("\n")
        if len(lines) > 3:
            return "\n".join(lines[-5:])
        return body.strip()

    def remove_quoted_replies(self, body: str) -> str:
        """Remove quoted replies (lines starting with '>')."""
        lines = body.split("\n")
        cleaned = [line for line in lines if not line.strip().startswith(">")]
        return "\n".join(cleaned).strip()

    def extract_person_name(self, signature: str) -> str:
        """Extract person name from signature. Look for lines that might be a name."""
        lines = signature.split("\n")
        for line in lines:
            line = line.strip()
            # Simple heuristic: a name is usually the first non-empty, non-email line
            if line and "@" not in line and len(line) < 50:
                return line
        return ""

    def extract_company(self, signature: str) -> str:
        """Extract company name from signature."""
        # Simple heuristic: look for common company markers like "at", "from", "Inc", "Corp", etc.
        patterns = [
            r"(?:at|from|@)\s+([A-Za-z0-9\s&\-\.]+?)(?:,|\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, signature, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) < 100:
                    return company
        return ""

    def extract_job_title(self, signature: str) -> str:
        """Extract job title from signature."""
        # Simple heuristic: look for role indicators
        patterns = [
            r"(?:Recruiter|Manager|Engineer|Developer|Designer|Lead|Head|Director|VP)",
        ]
        for pattern in patterns:
            match = re.search(pattern, signature, re.IGNORECASE)
            if match:
                return match.group(0)
        return ""

    def extract_contact_info(self, signature: str, sender: str) -> str:
        """Extract contact info (email, phone) from signature."""
        # Look for email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", signature)
        if email_match:
            return email_match.group(0)
        return sender

    def save_json(self, records: List[Dict], output_path: str) -> None:
        """Save records to JSON file."""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Usage: python email_parser.py
    input_mbox = "./emails/All mail Including Spam and Trash.mbox"
    output_json = "./output/email_records.json"
    
    processor = EmailProcessor(input_mbox)
    records = processor.parse()
    processor.save_json(records, output_json)
    print(f"Processed {len(records)} emails. Saved to {output_json}")
