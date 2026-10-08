import os

import qa
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


def _get_qa_module():
    if os.environ.get("USE_LANGCHAIN") == "1":
        import qa_lc

        return qa_lc
    return qa


def _extract_question():
    payload = request.get_json(silent=True)
    question = payload.get("question") if isinstance(payload, dict) else None

    if not isinstance(question, str) or not question.strip():
        return None, (jsonify({"error": "问题不能为空"}), 400)

    question = question.strip()
    if len(question) > 500:
        return None, (jsonify({"error": "问题过长"}), 400)

    return question, None


def _extract_thread_id():
    payload = request.get_json(silent=True)
    thread_id = payload.get("thread_id") if isinstance(payload, dict) else None

    if thread_id is None:
        return None, None
    if not isinstance(thread_id, str) or not thread_id.strip():
        return None, (jsonify({"error": "thread_id 无效"}), 400)

    return thread_id.strip(), None


def _run_agent(question, thread_id=None):
    import agent

    if thread_id is None:
        return agent.run_agent(question)
    return agent.run_agent(question, thread_id=thread_id)


def _run_configured_backend(question, thread_id=None):
    if os.environ.get("USE_AGENT") == "1":
        if thread_id is None:
            return _run_agent(question)
        return _run_agent(question, thread_id=thread_id)
    return _get_qa_module().ask(question)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/ask")
def ask_question():
    question, error_response = _extract_question()
    if error_response is not None:
        return error_response
    thread_id, error_response = _extract_thread_id()
    if error_response is not None:
        return error_response

    try:
        result = _run_configured_backend(question, thread_id=thread_id)
    except Exception:
        app.logger.exception("问答接口处理失败")
        return jsonify({"answer": "服务暂时不可用，请稍后重试", "references": []})

    return jsonify(result)


@app.post("/api/agent/ask")
def ask_agent_question():
    question, error_response = _extract_question()
    if error_response is not None:
        return error_response
    thread_id, error_response = _extract_thread_id()
    if error_response is not None:
        return error_response

    try:
        if thread_id is None:
            result = _run_agent(question)
        else:
            result = _run_agent(question, thread_id=thread_id)
    except Exception:
        app.logger.exception("Agent 接口处理失败")
        return jsonify({"answer": "服务暂时不可用，请稍后重试", "references": []})

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
