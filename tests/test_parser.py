import pytest
# from parser.fix_parser import FixParser
from protocol_parsers.fix_parser import FixParser
@pytest.fixture
def parser():
    return FixParser()

def test_parse_valid_fix_message(parser):
    """
    Tests that a valid FIX string is parsed correctly into a dictionary.
    """
    fix_string = "8=FIX.4.2\x019=123\x0135=D\x0155=AAPL\x0138=100\x0110=167\x01"
    parsed_msg = parser.parse(fix_string)

    assert parsed_msg is not None
    assert parsed_msg[8] == "FIX.4.2"
    assert parsed_msg[35] == "D"
    assert parsed_msg[55] == "AAPL"
    assert parsed_msg[38] == "100"
    assert 'ingestion_timestamp' in parsed_msg

def test_parse_malformed_fix_message(parser):
    """
    Tests that a malformed message returns None and doesn't crash.
    """
    fix_string = "8=FIX.4.2\x01thisisnotvalid\x0135=D"
    parsed_msg = parser.parse(fix_string)

    assert parsed_msg is None

def test_parse_empty_message(parser):
    """
    Tests that an empty string returns None.
    """
    fix_string = ""
    parsed_msg = parser.parse(fix_string)

    assert parsed_msg is None