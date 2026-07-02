import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from sqlalchemy import text
from models import db, Email, Task, AgentLog, init_fts, rebuild_fts
from seeds import SEED_EMAILS
from agents.task_extractor import extract_tasks_from_emails
from agents.reply_drafter import draft_reply_for_email
from agents.tool_agent import ToolSelectionAgent
from agents.tool_executor import execute_tool
from agents.react_agent import run_react_agent

PRIMARY_USER = "pm@acme.com"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emails.db"
db.init_app(app)

# Configure CORS to allow all origins
CORS(app)

with app.app_context():
    db.create_all()
    init_fts(db.session)


@app.route("/ping")
def ping():
    return {"message": "pong"}


@app.route("/emails", methods=["POST"])
def create_email():
    data = request.json
    email = Email(
        thread_id=data.get("thread_id") or str(uuid.uuid4()),
        sender=data["sender"],
        recipient=data["recipient"],
        subject=data["subject"],
        body=data["body"]
    )
    db.session.add(email)
    db.session.commit()
    return email.to_dict(), 201


@app.route("/emails", methods=["GET"])
def get_emails():
    query = Email.query

    thread_id = request.args.get("thread_id")
    if thread_id:
        query = query.filter_by(thread_id=thread_id)

    is_read = request.args.get("is_read")
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == "true")

    sender = request.args.get("sender")
    if sender:
        query = query.filter_by(sender=sender)

    recipient = request.args.get("recipient")
    if recipient:
        query = query.filter_by(recipient=recipient)

    emails = query.order_by(Email.created_at.desc()).all()
    return [email.to_dict() for email in emails]


@app.route("/emails/<int:email_id>", methods=["GET"])
def get_email(email_id):
    email = Email.query.get_or_404(email_id)
    return email.to_dict()


@app.route("/emails/search", methods=["GET"])
def search_emails():
    query_text = request.args.get("q")
    if not query_text:
        return {"error": "Query parameter 'q' is required"}, 400

    limit = request.args.get("limit", 50, type=int)

    fts_query = text("""
        SELECT email.*, email_fts.rank
        FROM email_fts
        JOIN email ON email.id = email_fts.rowid
        WHERE email_fts MATCH :query
        ORDER BY rank
        LIMIT :limit
    """)

    results = db.session.execute(fts_query, {"query": query_text, "limit": limit}).fetchall()

    emails = []
    for row in results:
        email = Email.query.get(row.id)
        if email:
            email_dict = email.to_dict()
            email_dict["rank"] = row.rank
            emails.append(email_dict)

    is_read = request.args.get("is_read")
    if is_read is not None:
        is_read_bool = is_read.lower() == "true"
        emails = [e for e in emails if e["is_read"] == is_read_bool]

    sender = request.args.get("sender")
    if sender:
        emails = [e for e in emails if e["sender"] == sender]

    recipient = request.args.get("recipient")
    if recipient:
        emails = [e for e in emails if e["recipient"] == recipient]

    thread_id = request.args.get("thread_id")
    if thread_id:
        emails = [e for e in emails if e["thread_id"] == thread_id]

    return emails


@app.route("/emails/<int:email_id>", methods=["PUT"])
def update_email(email_id):
    email = Email.query.get_or_404(email_id)
    data = request.json
    email.sender = data.get("sender", email.sender)
    email.recipient = data.get("recipient", email.recipient)
    email.subject = data.get("subject", email.subject)
    email.body = data.get("body", email.body)
    if "is_read" in data:
        email.is_read = data["is_read"]
    db.session.commit()
    return email.to_dict()


@app.route("/emails/<int:email_id>/read", methods=["PATCH"])
def mark_email_read(email_id):
    email = Email.query.get_or_404(email_id)
    email.is_read = True
    db.session.commit()
    return email.to_dict()


@app.route("/emails/<int:email_id>", methods=["DELETE"])
def delete_email(email_id):
    email = Email.query.get_or_404(email_id)
    db.session.delete(email)
    db.session.commit()
    return "", 204


@app.route("/threads", methods=["GET"])
def get_threads():
    threads = db.session.query(
        Email.thread_id,
        db.func.min(Email.subject).label("subject"),
        db.func.count(Email.id).label("message_count"),
        db.func.min(Email.created_at).label("first_message_at"),
        db.func.max(Email.created_at).label("last_message_at"),
        db.func.sum(db.case((Email.is_read == False, 1), else_=0)).label("unread_count")
    ).group_by(Email.thread_id).all()

    return [
        {
            "thread_id": t.thread_id,
            "subject": t.subject,
            "message_count": t.message_count,
            "first_message_at": t.first_message_at.isoformat(),
            "last_message_at": t.last_message_at.isoformat(),
            "unread_count": t.unread_count or 0
        }
        for t in threads
    ]


@app.route("/stats", methods=["GET"])
def get_stats():
    total_emails = Email.query.count()
    unread_count = Email.query.filter_by(is_read=False).count()
    thread_count = db.session.query(Email.thread_id).distinct().count()

    return {
        "total_emails": total_emails,
        "unread_count": unread_count,
        "read_count": total_emails - unread_count,
        "thread_count": thread_count
    }


@app.route("/emails", methods=["DELETE"])
def delete_emails():
    data = request.json
    Email.query.filter(Email.id.in_(data["ids"])).delete()
    db.session.commit()
    return "", 204


@app.route("/tasks", methods=["GET"])
def get_tasks():
    query = Task.query

    completed = request.args.get("completed")
    if completed is not None:
        query = query.filter_by(completed=completed.lower() == "true")

    tasks = query.order_by(Task.created_at.desc()).all()
    return [task.to_dict() for task in tasks]


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json
    if "completed" in data:
        task.completed = data["completed"]
    db.session.commit()
    return task.to_dict()


@app.route("/tasks/generate", methods=["POST"])
def generate_tasks():
    unread_emails = Email.query.filter_by(
        recipient=PRIMARY_USER,
        is_read=False
    ).all()

    if not unread_emails:
        return {"message": "No unread emails", "tasks_created": 0}

    email_dicts = [e.to_dict() for e in unread_emails]
    extracted_tasks = extract_tasks_from_emails(email_dicts)

    Task.query.filter_by(completed=False).delete()

    for item in extracted_tasks:
        task = Task(
            description=item.description,
            email_id=item.email_id,
            thread_id=item.thread_id,
            priority=item.priority
        )
        db.session.add(task)

    db.session.commit()
    return {"message": "Tasks generated", "tasks_created": len(extracted_tasks)}


@app.route("/emails/<int:email_id>/draft-reply", methods=["POST"])
def draft_reply(email_id):
    email = Email.query.get_or_404(email_id)
    data = request.json or {}
    result = draft_reply_for_email(
        email_id=email_id,
        feedback=data.get("feedback"),
        tone=data.get("tone"),
        previous_draft=data.get("previous_draft")
    )
    return jsonify(result)


@app.route("/agent-logs", methods=["GET"])
def get_agent_logs():
    limit = request.args.get("limit", 100, type=int)
    agent_name = request.args.get("agent_name")

    query = AgentLog.query
    if agent_name:
        query = query.filter_by(agent_name=agent_name)

    logs = query.order_by(AgentLog.created_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]


@app.route("/agent-logs/stats", methods=["GET"])
def get_agent_stats():
    total_logs = AgentLog.query.count()
    total_cost = db.session.query(db.func.sum(AgentLog.cost_usd)).scalar() or 0.0
    total_tokens = db.session.query(db.func.sum(AgentLog.total_tokens)).scalar() or 0
    avg_latency = db.session.query(db.func.avg(AgentLog.latency_ms)).scalar() or 0

    by_agent = db.session.query(
        AgentLog.agent_name,
        db.func.count(AgentLog.id).label("call_count"),
        db.func.sum(AgentLog.total_tokens).label("total_tokens"),
        db.func.sum(AgentLog.cost_usd).label("total_cost"),
        db.func.avg(AgentLog.latency_ms).label("avg_latency")
    ).group_by(AgentLog.agent_name).all()

    by_operation = db.session.query(
        AgentLog.operation,
        db.func.count(AgentLog.id).label("call_count"),
        db.func.sum(AgentLog.total_tokens).label("total_tokens"),
        db.func.sum(AgentLog.cost_usd).label("total_cost")
    ).group_by(AgentLog.operation).all()

    return {
        "overview": {
            "total_calls": total_logs,
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "avg_latency_ms": int(avg_latency)
        },
        "by_agent": [
            {
                "agent_name": a.agent_name,
                "call_count": a.call_count,
                "total_tokens": a.total_tokens,
                "total_cost_usd": round(a.total_cost, 6),
                "avg_latency_ms": int(a.avg_latency)
            }
            for a in by_agent
        ],
        "by_operation": [
            {
                "operation": o.operation,
                "call_count": o.call_count,
                "total_tokens": o.total_tokens,
                "total_cost_usd": round(o.total_cost, 6)
            }
            for o in by_operation
        ]
    }


@app.route("/command", methods=["POST"])
def preview_command():
    data = request.json
    user_input = data.get("input")

    if not user_input:
        return {"error": "Input is required"}, 400

    agent = ToolSelectionAgent()
    tools = agent.select_tools(user_input)

    return {"tools": tools}


@app.route("/command/run", methods=["POST"])
def run_command():
    data = request.json
    user_input = data.get("input")

    if not user_input:
        return {"error": "Input is required"}, 400

    result = run_react_agent(user_input)
    return result


@app.route("/command/execute", methods=["POST"])
def execute_command():
    data = request.json
    tools = data.get("tools", [])

    if not tools:
        return {"error": "Tools array is required"}, 400

    results = []
    for tool in tools:
        tool_name = tool.get("name")
        tool_input = tool.get("input", {})
        result = execute_tool(tool_name, tool_input)
        results.append({
            "tool": tool_name,
            "output": result
        })

    return {"results": results}


@app.route("/reset", methods=["POST"])
def reset_database():
    db.drop_all()
    db.create_all()
    init_fts(db.session)
    for seed in SEED_EMAILS:
        email = Email(
            thread_id=seed.get("thread_id") or str(uuid.uuid4()),
            sender=seed["sender"],
            recipient=seed["recipient"],
            subject=seed["subject"],
            body=seed["body"],
            created_at=datetime.fromisoformat(seed["created_at"]) if seed.get("created_at") else None,
            is_read=seed.get("is_read", False)
        )
        db.session.add(email)
    db.session.commit()
    rebuild_fts(db.session)
    return {"message": "database reset", "emails_created": len(SEED_EMAILS)}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
