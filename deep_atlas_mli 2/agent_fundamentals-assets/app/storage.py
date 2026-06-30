import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class ExpenseStorage:
    def __init__(self, db_path: str = "expenses.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # FILL_THIS_IN: Create the expenses table with columns:
            # id (INTEGER PRIMARY KEY AUTOINCREMENT)
            # category (TEXT NOT NULL)
            # amount (REAL NOT NULL)
            # description (TEXT)
            # date (TEXT NOT NULL)
            conn.execute(
                """
                FILL_THIS_IN
            """
            )

    def add_expense(
        self, category: str, amount: float, description: str = "", date: str = None
    ) -> Dict:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            # FILL_THIS_IN: Insert the expense into the database using parameterized query
            # Use ? placeholders for values to prevent SQL injection
            cursor = conn.execute("FILL_THIS_IN", (category, amount, description, date))
            return {
                "id": cursor.lastrowid,
                "category": category,
                "amount": amount,
                "description": description,
                "date": date,
            }

    def get_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        # FILL_THIS_IN: Build a query that filters by category, start_date, and end_date
        # Start with "SELECT id, category, amount, description, date FROM expenses WHERE 1=1"
        # Then conditionally add filters using AND clauses
        # Use parameterized queries with ? placeholders
        query = "FILL_THIS_IN"
        params = []

        if category:
            query += " FILL_THIS_IN"
            params.append(category)
        if start_date:
            query += " FILL_THIS_IN"
            params.append(start_date)
        if end_date:
            query += " FILL_THIS_IN"
            params.append(end_date)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [
                {
                    "id": row[0],
                    "category": row[1],
                    "amount": row[2],
                    "description": row[3],
                    "date": row[4],
                }
                for row in cursor.fetchall()
            ]

    def update_expense(
        self,
        expense_id: int,
        category: str = None,
        amount: float = None,
        description: str = None,
        date: str = None,
    ) -> Dict:
        updates = []
        params = []

        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if date is not None:
            updates.append("date = ?")
            params.append(date)

        if not updates:
            raise ValueError("No fields to update")

        params.append(expense_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?", params
            )
            cursor = conn.execute(
                "SELECT id, category, amount, description, date FROM expenses WHERE id = ?",
                (expense_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "category": row[1],
                    "amount": row[2],
                    "description": row[3],
                    "date": row[4],
                }
            # FILL_THIS_IN: Raise a ValueError if the expense_id was not found

    def delete_expense(self, expense_id: int) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, category, amount, description, date FROM expenses WHERE id = ?",
                (expense_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Expense {expense_id} not found")

            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return {
                "id": row[0],
                "category": row[1],
                "amount": row[2],
                "description": row[3],
                "date": row[4],
            }
