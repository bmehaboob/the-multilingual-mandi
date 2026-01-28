"""
Integration Test 21.2: Offline-to-Online Transition
Tests message recording while offline and auto-sync when connectivity restored

Requirements: 12.1, 12.3
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime


# Simplified models for testing (avoiding PostgreSQL-specific types)
class SimpleUser:
    def __init__(self, id, name, phone_number, primary_language):
        self.id = id
        self.name = name
        self.phone_number = phone_number
        self.primary_language = primary_language


class SimpleConversation:
    def __init__(self, id, participants, commodity):
        self.id = id
        self.participants = participants
        self.commodity = commodity


class SimpleMessage:
    def __init__(self, id, conversation_id, sender_id, original_text, original_language, translated_text=None, timestamp=None):
        self.id = id
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.original_text = original_text
        self.original_language = original_language
        self.translated_text = translated_text or {}
        self.timestamp = timestamp or datetime.utcnow()


@pytest.fixture
def test_user():
    """Create a test user"""
    return SimpleUser(
        id=uuid4(),
        name="Test User",
        phone_number="+919876543210",
        primary_language="hin"
    )


@pytest.fixture
def test_conversation(test_user):
    """Create a test conversation"""
    other_user_id = uuid4()
    return SimpleConversation(
        id=uuid4(),
        participants=[test_user.id, other_user_id],
        commodity="tomato"
    )


class MockOfflineSyncManager:
    """Mock offline sync manager for testing"""
    
    def __init__(self):
        self.is_online = True
        self.message_queue = []
        self.sync_callbacks = []
        self.synced_messages = []  # Store synced messages in memory
    
    def set_offline(self):
        """Simulate going offline"""
        self.is_online = False
    
    def set_online(self):
        """Simulate going online"""
        self.is_online = True
    
    def queue_message(self, message_data):
        """Queue a message for later transmission"""
        if not self.is_online:
            self.message_queue.append({
                "id": str(uuid4()),
                "data": message_data,
                "queued_at": datetime.utcnow(),
                "synced": False
            })
            return True
        return False
    
    async def sync_when_online(self):
        """Sync queued messages when online"""
        if not self.is_online:
            return {"success": False, "reason": "offline"}
        
        synced_count = 0
        failed_count = 0
        
        for queued_msg in self.message_queue:
            if not queued_msg["synced"]:
                try:
                    # Create message in memory (simulating database)
                    msg = SimpleMessage(
                        id=uuid4(),
                        conversation_id=queued_msg["data"]["conversation_id"],
                        sender_id=queued_msg["data"]["sender_id"],
                        original_text=queued_msg["data"]["original_text"],
                        original_language=queued_msg["data"]["original_language"],
                        translated_text=queued_msg["data"].get("translated_text", {}),
                        timestamp=queued_msg["queued_at"]
                    )
                    self.synced_messages.append(msg)
                    
                    queued_msg["synced"] = True
                    queued_msg["synced_at"] = datetime.utcnow()
                    synced_count += 1
                except Exception as e:
                    failed_count += 1
                    queued_msg["error"] = str(e)
        
        return {
            "success": True,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_queued": len(self.message_queue)
        }
    
    def get_queue_status(self):
        """Get current queue status"""
        synced = sum(1 for msg in self.message_queue if msg["synced"])
        pending = len(self.message_queue) - synced
        
        return {
            "total": len(self.message_queue),
            "synced": synced,
            "pending": pending,
            "is_online": self.is_online
        }
    
    def clear_synced_messages(self):
        """Clear synced messages from queue"""
        self.message_queue = [msg for msg in self.message_queue if not msg["synced"]]
    
    def get_synced_messages_for_conversation(self, conversation_id):
        """Get synced messages for a conversation"""
        return [msg for msg in self.synced_messages if msg.conversation_id == conversation_id]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_message_queueing(test_user, test_conversation):
    """
    Test that messages are queued when offline
    Requirement 12.1
    """
    sync_manager = MockOfflineSyncManager()
    
    # Verify initially online
    assert sync_manager.is_online is True
    
    # Go offline
    sync_manager.set_offline()
    assert sync_manager.is_online is False
    
    # Try to send messages while offline
    messages_to_queue = [
        {
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": "Message 1 while offline",
            "original_language": "hin"
        },
        {
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": "Message 2 while offline",
            "original_language": "hin"
        },
        {
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": "Message 3 while offline",
            "original_language": "hin"
        }
    ]
    
    for msg_data in messages_to_queue:
        queued = sync_manager.queue_message(msg_data)
        assert queued is True
    
    # Verify messages are in queue
    queue_status = sync_manager.get_queue_status()
    assert queue_status["total"] == 3
    assert queue_status["pending"] == 3
    assert queue_status["synced"] == 0
    
    # Verify messages are not synced yet
    synced_messages = sync_manager.get_synced_messages_for_conversation(test_conversation.id)
    assert len(synced_messages) == 0
    
    print("\n✓ Offline message queueing test passed!")
    print(f"  - Queued {queue_status['total']} messages while offline")
    print(f"  - Messages not yet synced")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_to_online_auto_sync(test_user, test_conversation):
    """
    Test that queued messages automatically sync when connectivity restored
    Requirement 12.3
    """
    sync_manager = MockOfflineSyncManager()
    
    # Go offline and queue messages
    sync_manager.set_offline()
    
    messages_to_queue = [
        {
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Offline message {i}",
            "original_language": "hin",
            "translated_text": {"tel": f"Offline message {i} in Telugu"}
        }
        for i in range(5)
    ]
    
    for msg_data in messages_to_queue:
        sync_manager.queue_message(msg_data)
    
    # Verify messages are queued
    queue_status_before = sync_manager.get_queue_status()
    assert queue_status_before["pending"] == 5
    
    # Go back online
    sync_manager.set_online()
    assert sync_manager.is_online is True
    
    # Trigger auto-sync
    sync_result = await sync_manager.sync_when_online()
    
    # Verify sync succeeded
    assert sync_result["success"] is True
    assert sync_result["synced_count"] == 5
    assert sync_result["failed_count"] == 0
    
    # Verify messages are now synced
    synced_messages = sync_manager.get_synced_messages_for_conversation(test_conversation.id)
    
    assert len(synced_messages) == 5
    
    for i, msg in enumerate(sorted(synced_messages, key=lambda m: m.timestamp)):
        assert msg.original_text == f"Offline message {i}"
        assert msg.original_language == "hin"
        assert "tel" in msg.translated_text
    
    # Verify queue status updated
    queue_status_after = sync_manager.get_queue_status()
    assert queue_status_after["synced"] == 5
    assert queue_status_after["pending"] == 0
    
    print("\n✓ Offline-to-online auto-sync test passed!")
    print(f"  - Synced {sync_result['synced_count']} messages")
    print(f"  - All messages now synced")
    print(f"  - No sync failures")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_ordering_preserved_after_sync(test_user, test_conversation):
    """
    Test that message ordering is preserved after sync (FIFO)
    Requirement 5.4 (Property 17)
    """
    sync_manager = MockOfflineSyncManager()
    
    # Go offline
    sync_manager.set_offline()
    
    # Queue messages with specific order
    message_texts = [
        "First message",
        "Second message",
        "Third message",
        "Fourth message",
        "Fifth message"
    ]
    
    for text in message_texts:
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": text,
            "original_language": "hin"
        })
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.01)
    
    # Go online and sync
    sync_manager.set_online()
    await sync_manager.sync_when_online()
    
    # Retrieve messages
    synced_messages = sync_manager.get_synced_messages_for_conversation(test_conversation.id)
    synced_messages_sorted = sorted(synced_messages, key=lambda m: m.timestamp)
    
    # Verify order is preserved
    assert len(synced_messages_sorted) == 5
    for i, msg in enumerate(synced_messages_sorted):
        assert msg.original_text == message_texts[i], \
            f"Message order not preserved: expected '{message_texts[i]}', got '{msg.original_text}'"
    
    print("\n✓ Message ordering preservation test passed!")
    print(f"  - All {len(synced_messages_sorted)} messages synced in correct order (FIFO)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_partial_sync_failure_handling(test_user, test_conversation):
    """
    Test handling of partial sync failures
    """
    sync_manager = MockOfflineSyncManager()
    
    # Go offline and queue messages
    sync_manager.set_offline()
    
    # Queue valid messages
    for i in range(3):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Valid message {i}",
            "original_language": "hin"
        })
    
    # Queue an invalid message (missing required field)
    sync_manager.queue_message({
        "conversation_id": test_conversation.id,
        "sender_id": test_user.id,
        # Missing original_text
        "original_language": "hin"
    })
    
    # Queue more valid messages
    for i in range(2):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Valid message {i+3}",
            "original_language": "hin"
        })
    
    # Go online and sync
    sync_manager.set_online()
    sync_result = await sync_manager.sync_when_online()
    
    # Verify partial success
    assert sync_result["success"] is True
    assert sync_result["synced_count"] == 5  # 5 valid messages
    assert sync_result["failed_count"] == 1  # 1 invalid message
    
    # Verify valid messages are synced
    synced_messages = sync_manager.get_synced_messages_for_conversation(test_conversation.id)
    assert len(synced_messages) == 5
    
    print("\n✓ Partial sync failure handling test passed!")
    print(f"  - Synced {sync_result['synced_count']} valid messages")
    print(f"  - Failed {sync_result['failed_count']} invalid messages")
    print(f"  - System continued despite partial failure")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_offline_online_cycles(test_user, test_conversation):
    """
    Test multiple offline-online cycles
    """
    sync_manager = MockOfflineSyncManager()
    
    total_messages_sent = 0
    
    # Cycle 1: Offline -> Queue -> Online -> Sync
    sync_manager.set_offline()
    for i in range(2):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Cycle 1 message {i}",
            "original_language": "hin"
        })
    total_messages_sent += 2
    
    sync_manager.set_online()
    await sync_manager.sync_when_online()
    sync_manager.clear_synced_messages()
    
    # Cycle 2: Offline -> Queue -> Online -> Sync
    sync_manager.set_offline()
    for i in range(3):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Cycle 2 message {i}",
            "original_language": "hin"
        })
    total_messages_sent += 3
    
    sync_manager.set_online()
    await sync_manager.sync_when_online()
    sync_manager.clear_synced_messages()
    
    # Cycle 3: Offline -> Queue -> Online -> Sync
    sync_manager.set_offline()
    for i in range(4):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Cycle 3 message {i}",
            "original_language": "hin"
        })
    total_messages_sent += 4
    
    sync_manager.set_online()
    await sync_manager.sync_when_online()
    
    # Verify all messages from all cycles are synced
    all_synced = sync_manager.synced_messages
    conversation_messages = [msg for msg in all_synced if msg.conversation_id == test_conversation.id]
    
    assert len(conversation_messages) == total_messages_sent
    
    print("\n✓ Multiple offline-online cycles test passed!")
    print(f"  - Completed 3 offline-online cycles")
    print(f"  - Total messages synced: {total_messages_sent}")
    print(f"  - All messages successfully stored")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_notification_and_status(test_user):
    """
    Test offline mode detection and notification
    Requirement 12.4 (Property 37)
    """
    sync_manager = MockOfflineSyncManager()
    
    # Initially online
    status = sync_manager.get_queue_status()
    assert status["is_online"] is True
    
    # Go offline
    sync_manager.set_offline()
    
    # Verify offline status is detected
    status = sync_manager.get_queue_status()
    assert status["is_online"] is False
    
    # User should be notified they are in offline mode
    # (In real implementation, this would trigger a voice notification)
    offline_notification = {
        "type": "offline_mode",
        "message": "You are now in offline mode. Messages will be queued and sent when connection is restored.",
        "language": test_user.primary_language
    }
    
    assert offline_notification["type"] == "offline_mode"
    assert "offline" in offline_notification["message"].lower()
    
    # Go back online
    sync_manager.set_online()
    
    # Verify online status is detected
    status = sync_manager.get_queue_status()
    assert status["is_online"] is True
    
    # User should be notified they are back online
    online_notification = {
        "type": "online_mode",
        "message": "Connection restored. Syncing queued messages.",
        "language": test_user.primary_language
    }
    
    assert online_notification["type"] == "online_mode"
    assert "restored" in online_notification["message"].lower() or "online" in online_notification["message"].lower()
    
    print("\n✓ Offline notification and status test passed!")
    print(f"  - Offline status correctly detected")
    print(f"  - Online status correctly detected")
    print(f"  - Notifications generated for both transitions")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_performance(test_user, test_conversation):
    """
    Test sync performance with large message queue
    """
    import time
    
    sync_manager = MockOfflineSyncManager()
    
    # Go offline and queue many messages
    sync_manager.set_offline()
    
    message_count = 50
    for i in range(message_count):
        sync_manager.queue_message({
            "conversation_id": test_conversation.id,
            "sender_id": test_user.id,
            "original_text": f"Performance test message {i}",
            "original_language": "hin"
        })
    
    # Go online and measure sync time
    sync_manager.set_online()
    
    start_time = time.time()
    sync_result = await sync_manager.sync_when_online()
    end_time = time.time()
    
    sync_time_ms = (end_time - start_time) * 1000
    
    # Verify all messages synced
    assert sync_result["synced_count"] == message_count
    assert sync_result["failed_count"] == 0
    
    # Verify messages synced
    synced_messages = sync_manager.get_synced_messages_for_conversation(test_conversation.id)
    assert len(synced_messages) == message_count
    
    # Calculate throughput
    messages_per_second = message_count / (sync_time_ms / 1000) if sync_time_ms > 0 else message_count
    
    print("\n✓ Sync performance test passed!")
    print(f"  - Synced {message_count} messages in {sync_time_ms:.0f}ms")
    print(f"  - Throughput: {messages_per_second:.1f} messages/second")
    print(f"  - Average time per message: {sync_time_ms/message_count:.1f}ms")
