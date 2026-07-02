# GenMail 后端入口：Flask REST API + SQLite
import uuid
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
from openai import APIError
from agents.env import load_env_file
from agents.summarizer import summarize_thread
from agents.digest import digest_unread 
# 功能 2：未读邮件摘要
from agents.sender_topics import analyze_sender_topics  # 功能 3：发件人主题分析
from agents.analytics import inbox_analytics  # 功能 4：统计仪表盘
from agents.commitments import track_commitments  # 功能 5：承诺追踪
from agents.urgency import classify_email_urgency  # 功能 6：紧急程度分类
from agents.thread_state import classify_thread_state  # 功能 7：线程状态分类
from agents.inbox_intelligence import (  # 功能 9【LangGraph】
    proactive_inbox,
    resume_proactive_inbox,
    start_proactive_inbox,
)
from agents.cross_thread import synthesize_topic  # 功能 10：跨线程综合
from agents.draft_reply import resume_draft_reply, start_draft_reply  # 功能 8：智能回复（【LangGraph】唯一入口）
from models import db, Email
from seeds import SEED_EMAILS

# 启动时加载 server/.env 中的环境变量
load_env_file()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emails.db"  # SQLite 数据库文件
CORS(app)  # 允许前端跨域访问
db.init_app(app)

# 应用启动时自动建表（若不存在）
with app.app_context():
    db.create_all()


@app.route("/ping")
def ping():# 健康检查
    return {"message": "pong"}


@app.route("/emails", methods=["POST"])
def create_email():
    """创建新邮件；未传 thread_id 时自动生成新线程"""
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
    """获取邮件列表，支持按线程、已读状态、发件人、收件人过滤"""
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
    """获取单封邮件"""
    email = Email.query.get_or_404(email_id)
    return email.to_dict()


@app.route("/emails/<int:email_id>", methods=["PUT"])
def update_email(email_id):
    """更新邮件字段（含 is_read）"""
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
    """将邮件标记为已读"""
    email = Email.query.get_or_404(email_id)
    email.is_read = True
    db.session.commit()
    return email.to_dict()


@app.route("/emails/<int:email_id>", methods=["DELETE"])
def delete_email(email_id):
    """删除单封邮件"""
    email = Email.query.get_or_404(email_id)
    db.session.delete(email)
    db.session.commit()
    return "", 204


@app.route("/threads", methods=["GET"])
def get_threads():
    """按 thread_id 聚合，返回每个线程的摘要元数据"""
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
    """收件箱基础统计：总数、未读数、线程数"""
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
    """批量删除邮件，请求体需包含 ids 数组"""
    data = request.json
    Email.query.filter(Email.id.in_(data["ids"])).delete()
    db.session.commit()
    return "", 204

#POST /ai/summarize/<thread_id> -> AI 功能：生成指定线程的摘要（后加）
@app.route("/ai/summarize/<thread_id>", methods=["POST"])
def ai_summarize(thread_id):
    """AI 功能：生成指定线程的摘要（后加）"""
    try:
        result = summarize_thread(thread_id)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502

    if result is None:
        return {"error": f"thread not found: {thread_id}"}, 404

    return result


# 功能 2：POST /ai/digest — 未读邮件摘要（按发件人分组）
@app.route("/ai/digest", methods=["POST"])
def ai_digest():
    """AI 功能：未读邮件摘要（按发件人分组）"""
    try:
        return digest_unread()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        # LLM API 调用失败（Key、配额等）
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


# 功能 3：POST /ai/sender/<sender> — 发件人主题聚类分析
@app.route("/ai/sender/<path:sender>", methods=["POST"])
def ai_sender_topics(sender):
    """AI 功能：分析指定发件人的邮件主题聚类"""
    try:
        result = analyze_sender_topics(sender)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502

    if result is None:
        return {"error": f"未找到发件人: {sender}"}, 404

    return result


# =============================================================================
# 第四步：POST /ai/analytics — 统计仪表盘（收件箱智能分析）
# -----------------------------------------------------------------------------
# 无输入参数；调用 inbox_analytics()：
#   - Python 先算事实（邮件量、最忙日、最长线程等）
#   - LLM 再写成中文报告
# 返回：total_emails / unread_count / thread_count / facts / report
# =============================================================================
@app.route("/ai/analytics", methods=["POST"])
def ai_analytics():
    """AI 功能 4：超越 /stats 的收件箱智能分析"""
    try:
        return inbox_analytics()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


# =============================================================================
# 第五步：POST /ai/commitments — 承诺追踪
# -----------------------------------------------------------------------------
# 扫描 pm@acme.com 发出的邮件，LLM 提取明确承诺（I'll / 我会 + 截止时间等）。
# 返回：sent_email_count / commitment_count / commitments[] / report
# =============================================================================
@app.route("/ai/commitments", methods=["POST"])
def ai_commitments():
    """AI 功能 5：扫描已发送邮件并提取承诺"""
    try:
        return track_commitments()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


# =============================================================================
# 第六步：POST /ai/urgency/<email_id> — 紧急程度分类
# -----------------------------------------------------------------------------
# Python 先 gather_urgency_facts（时间、已回复、发件人历史、跨线程提及等），
# LLM 输出 score / level / reasoning。不持久化，按需实时计算。
# =============================================================================
@app.route("/ai/urgency/<int:email_id>", methods=["POST"])
def ai_urgency(email_id):
    """AI 功能 6：分析单封邮件的紧急程度"""
    try:
        result = classify_email_urgency(email_id)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502

    if result is None:
        return {"error": f"邮件不存在: {email_id}"}, 404

    return result


# =============================================================================
# 第七步：POST /ai/thread-state/<thread_id> — 线程状态分类
# -----------------------------------------------------------------------------
# Python 先 gather_thread_state_facts，LLM 输出 state / blocking_party / context。
# 不持久化；功能 9「停滞对话」将复用 classify_thread_state()。
# =============================================================================
@app.route("/ai/thread-state/<thread_id>", methods=["POST"])
def ai_thread_state(thread_id):
    """AI 功能 7：分析邮件线程当前状态"""
    try:
        result = classify_thread_state(thread_id)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502

    if result is None:
        return {"error": f"线程不存在: {thread_id}"}, 404

    return result


# =============================================================================
# 第九步：主动收件箱提醒 — 【LangGraph 并行 gather + interrupt 确认】
# -----------------------------------------------------------------------------
# POST /ai/inbox-intelligence         → 并行 gather，interrupt 返回 run_id + 待办列表
# POST /ai/inbox-intelligence/resume  → { run_id, action: confirm_all|skip }
# body.auto_confirm=true 时一键跑完（兼容旧行为）
# =============================================================================
@app.route("/ai/inbox-intelligence", methods=["POST"])
def ai_inbox_intelligence():
    """AI 功能 9：LangGraph 主动收件箱（默认在待办确认处 interrupt）"""
    data = request.get_json(silent=True) or {}
    try:
        if data.get("auto_confirm"):
            return proactive_inbox()
        return start_proactive_inbox()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


@app.route("/ai/inbox-intelligence/resume", methods=["POST"])
def ai_inbox_intelligence_resume():
    """AI 功能 9：LangGraph Command(resume) — 用户确认待办后生成报告"""
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id")
    action = data.get("action", "confirm_all")
    filtered_items = data.get("filtered_items")

    if not run_id:
        return {"error": "需要 run_id"}, 400

    try:
        return resume_proactive_inbox(run_id, action, filtered_items)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


# =============================================================================
# 第十步：POST /ai/synthesize — 跨线程综合【LangGraph: search→synthesize→reflect】
# -----------------------------------------------------------------------------
# 请求体：{ "topic": "Phoenix" }；搜索相关邮件并生成综合报告。
# =============================================================================
@app.route("/ai/synthesize", methods=["POST"])
def ai_synthesize():
    """AI 功能 10：LangGraph 跨线程综合（search → synthesize → reflect）"""
    data = request.json or {}
    topic = data.get("topic", "")
    try:
        return synthesize_topic(topic)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


# =============================================================================
# 第八步：智能回复起草 — 【LangGraph + Human-in-the-Loop】
# -----------------------------------------------------------------------------
# 全项目 LangGraph 路由：功能 8 draft_reply、功能 9 inbox_intelligence、功能 10 cross_thread
# POST /ai/draft-reply/<thread_id>  → graph.invoke()，在 interrupt 暂停，返回 run_id
# POST /ai/draft-reply/resume       → graph.invoke(Command(resume=...)) 用户审批后续跑
# =============================================================================
@app.route("/ai/draft-reply/<thread_id>", methods=["POST"])
def ai_draft_reply_start(thread_id):
    """AI 功能 8：LangGraph 生成草稿，等待用户审批（interrupt）"""
    try:
        result = start_draft_reply(thread_id)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502

    if result is None:
        return {"error": f"线程不存在: {thread_id}"}, 404

    return result


@app.route("/ai/draft-reply/resume", methods=["POST"])
def ai_draft_reply_resume():
    """AI 功能 8：LangGraph Command(resume) — 批准/编辑后发送，或 reject 取消"""
    data = request.json or {}
    run_id = data.get("run_id")
    action = data.get("action")
    body = data.get("body")

    if not run_id or not action:
        return {"error": "需要 run_id 和 action"}, 400

    try:
        return resume_draft_reply(run_id, action, body)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except APIError as exc:
        return {
            "error": str(exc),
            "type": "llm_api_error",
            "hint": "Check API key billing/quota, or switch to Ollama for local inference.",
        }, 502


@app.route("/reset", methods=["POST"])
def reset_database():
    """清空数据库并重新导入 seeds.py 中的 23 封种子邮件"""
    db.drop_all()
    db.create_all()
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
    return {"message": "database reset", "emails_created": len(SEED_EMAILS)}


if __name__ == "__main__":
    app.run(debug=True)

