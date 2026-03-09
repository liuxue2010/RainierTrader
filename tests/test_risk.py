import pytest
from unittest.mock import patch, AsyncMock

from rainier_trader.nodes.risk import _reject


def test_reject_returns_correct_structure():
    result = _reject("Test reason")
    assert result["risk_approved"] is False
    assert result["risk_note"] == "Test reason"


# Integration-style risk tests require mocking settings + broker
# See test_workflow.py for end-to-end tests
