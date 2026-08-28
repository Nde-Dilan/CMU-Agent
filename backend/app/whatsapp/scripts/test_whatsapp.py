import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.whatsapp.waha_service import WahaService
from app.whatsapp.waha_client import WahaClient
from app.config import settings

client = TestClient(app)


def test_root_and_health():
    """Verify FastAPI root and healthcheck endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"
    assert res_root.json()["active_engine"] == "waha"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    print("[PASS] Root and Healthcheck tests passed.")


def test_waha_webhook_health():
    """Verify WAHA Webhook info endpoint."""
    res = client.get("/webhook/waha")
    assert res.status_code == 200
    assert res.json()["status"] == "active"
    assert "WAHA" in res.json()["engine"]
    print("[PASS] WAHA Webhook health endpoint passed.")


def test_waha_service_logic():
    """Test WahaService event parsing, deduplication, group filtering, and chat history."""
    mock_client = WahaClient()
    mock_client.send_text = AsyncMock(return_value={"status": "sent"})
    mock_client.send_seen = AsyncMock(return_value={"status": "seen"})

    service = WahaService(client=mock_client)

    # 1. Test incoming private message from student
    event_payload = {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "msg_001_unique",
            "from": "237690000000@c.us",
            "to": "bot@c.us",
            "body": "What are CMU scholarship opportunities?",
            "fromMe": False,
            "hasMedia": False,
        },
    }

    with patch("app.whatsapp.waha_service.agent_chat", return_value="CMU offers merit and need-based scholarships."):
        reply = asyncio.run(service.handle_webhook_event(event_payload))
        assert reply == "CMU offers merit and need-based scholarships."
        assert mock_client.send_text.called

        # 2. Test deduplication - sending identical message ID should be ignored
        duplicate_reply = asyncio.run(service.handle_webhook_event(event_payload))
        assert duplicate_reply is None

        # 3. Test bot's own messages (fromMe = True) should be ignored
        bot_event = {
            "event": "message",
            "session": "default",
            "payload": {
                "id": "msg_002_bot",
                "from": "237690000000@c.us",
                "body": "I am a bot message",
                "fromMe": True,
            },
        }
        bot_reply = asyncio.run(service.handle_webhook_event(bot_event))
        assert bot_reply is None

        # 4. Test group chat message (@g.us) -> MUST be silently ignored
        group_event = {
            "event": "message",
            "session": "default",
            "payload": {
                "id": "msg_004_group",
                "from": "120363028394829384@g.us",
                "participant": "237699999999@c.us",
                "body": "Hello everyone in this group!",
                "fromMe": False,
                "isGroup": True,
            },
        }
        group_reply = asyncio.run(service.handle_webhook_event(group_event))
        assert group_reply is None, "Group message should be ignored!"

        # 5. Test status/broadcast update -> MUST be ignored
        status_event = {
            "event": "message",
            "session": "default",
            "payload": {
                "id": "msg_005_status",
                "from": "status@broadcast",
                "body": "Status story update",
                "fromMe": False,
            },
        }
        status_reply = asyncio.run(service.handle_webhook_event(status_event))
        assert status_reply is None, "Broadcast status should be ignored!"

        # 6. Test /reset command in private DM
        reset_event = {
            "event": "message",
            "session": "default",
            "payload": {
                "id": "msg_003_reset",
                "from": "237690000000@c.us",
                "body": "/reset",
                "fromMe": False,
            },
        }
        reset_reply = asyncio.run(service.handle_webhook_event(reset_event))
        assert "Welcome to the CMU Student Support Assistant" in reset_reply

    print("[PASS] WAHA Service logic, deduplication, group filtering, and session tests passed.")


def test_waha_webhook_post_endpoint():
    """Verify POST /webhook/waha endpoint accepts WAHA event delivery."""
    event_payload = {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "msg_post_test",
            "from": "237690000000@c.us",
            "body": "Hello from WAHA test",
            "fromMe": False,
        },
    }
    res = client.post("/webhook/waha", json=event_payload)
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    print("[PASS] POST /webhook/waha delivery test passed.")


def test_test_message_endpoint():
    """Test POST /webhook/test-message endpoint."""
    with patch("app.whatsapp.waha_service.agent_chat", return_value="Here is student help."):
        res = client.post("/webhook/test-message", params={"sender": "237690000000", "text": "Hi"})
        assert res.status_code == 200
        assert res.json()["reply"] == "Here is student help."
    print("[PASS] POST /webhook/test-message test passed.")


if __name__ == "__main__":
    print("Running WAHA WhatsApp integration tests...")
    test_root_and_health()
    test_waha_webhook_health()
    test_waha_service_logic()
    test_waha_webhook_post_endpoint()
    test_test_message_endpoint()
    print("\nALL WAHA TESTS PASSED SUCCESSFULLY!")
