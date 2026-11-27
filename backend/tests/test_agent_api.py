from app.routes import agent as agent_route


def test_agent_rejects_invalid_text_before_creating_agent(client, monkeypatch):
    def should_not_create(_config):
        raise AssertionError("Gemini should not be initialized")

    monkeypatch.setattr(agent_route, "AIWritingAgent", should_not_create)
    response = client.post("/api/agent/analyze", json={"text": " ", "goal": "Improve"})
    assert response.status_code == 400
    assert response.json["success"] is False


def test_agent_rejects_missing_goal(client):
    response = client.post("/api/agent/analyze", json={"text": "Some writing."})
    assert response.status_code == 400
    assert "goal" in response.json["message"].lower()


def test_agent_returns_expected_response_shape(client, monkeypatch):
    class FakeAgent:
        def __init__(self, _config):
            pass

        def analyze(self, text, goal, tone):
            return {
                "original_text": text,
                "improved_text": "Improved text.",
                "issues_identified": [{"message": "Agreement"}],
                "explanation": f"Applied goal: {goal}.",
                "tools_used": ["grammar_check", "rewrite_text"],
            }

    monkeypatch.setattr(agent_route, "AIWritingAgent", FakeAgent)
    response = client.post("/api/agent/analyze", json={
        "text": "Original text.", "goal": "Improve grammar", "tone": "Professional"
    })
    assert response.status_code == 200
    assert response.json["original_text"] == "Original text."
    assert response.json["improved_text"] == "Improved text."
    assert response.json["tools_used"] == ["grammar_check", "rewrite_text"]
    assert response.json["max_tool_rounds"] == 3
