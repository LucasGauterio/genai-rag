from flask import Blueprint, request, jsonify

from rag.retriever import retrieve_context
from rag.prompts import build_prompt
from llm.openrouter import call_openrouter

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json()
    question = payload.get("question")

    if not question:
        return jsonify({"error": "Missing question"}), 400

    context = retrieve_context(question)
    prompt = build_prompt(context, question)
    answer = call_openrouter(prompt)

    return jsonify({
        "answer": answer,
        "context": context
    })
