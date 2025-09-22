"""Tests for polling metadata functionality."""

from __future__ import annotations

from server.tools.polling import build_poll_metadata


def test_build_poll_metadata_returns_correct_structure() -> None:
    """Test that build_poll_metadata returns the expected TypedDict structure."""
    
    poll_interval = 42
    result = build_poll_metadata(poll_interval)
    
    # Check that all required keys are present
    assert "poll_interval_seconds" in result
    assert "poll_instructions" in result
    assert "reply_tool" in result
    assert "reply_resource_template" in result
    
    # Check that values have the expected types and contents
    assert result["poll_interval_seconds"] == poll_interval
    assert isinstance(result["poll_interval_seconds"], int)
    
    assert isinstance(result["poll_instructions"], str)
    assert f"{poll_interval} seconds" in result["poll_instructions"]
    
    assert result["reply_tool"] == "get_reply"
    assert isinstance(result["reply_tool"], str)
    
    assert result["reply_resource_template"] == "resource://get_reply/{question_id}/{auth_key}"
    assert isinstance(result["reply_resource_template"], str)


def test_poll_metadata_typed_dict_structure() -> None:
    """Test that PollMetadata TypedDict enforces the correct structure."""
    
    # This test mainly serves to validate the TypedDict definition
    # and would catch issues during type checking
    result = build_poll_metadata(30)
    
    # Type checker should recognize these as valid assignments
    poll_interval: int = result["poll_interval_seconds"]
    poll_instructions: str = result["poll_instructions"]
    reply_tool: str = result["reply_tool"]
    reply_resource_template: str = result["reply_resource_template"]
    
    # Verify the values are as expected
    assert poll_interval == 30
    assert "30 seconds" in poll_instructions
    assert reply_tool == "get_reply"
    assert reply_resource_template.startswith("resource://")


def test_poll_metadata_different_intervals() -> None:
    """Test that build_poll_metadata works with different interval values."""
    
    test_intervals = [1, 5, 30, 60, 300]
    
    for interval in test_intervals:
        result = build_poll_metadata(interval)
        
        assert result["poll_interval_seconds"] == interval
        assert f"{interval} seconds" in result["poll_instructions"]
        
        # Other fields should remain constant regardless of interval
        assert result["reply_tool"] == "get_reply"
        assert result["reply_resource_template"] == "resource://get_reply/{question_id}/{auth_key}"