import pytest
import json
from unittest.mock import MagicMock, patch

from rainier_trader.models.signal import Decision


def test_decision_dataclass():
    d = Decision(action="buy", confidence=0.8, reasoning="Strong bullish signal")
    assert d.action == "buy"
    assert d.confidence == 0.8


def test_decision_hold_on_low_confidence():
    d = Decision(action="hold", confidence=0.3, reasoning="Uncertain")
    assert d.action == "hold"
