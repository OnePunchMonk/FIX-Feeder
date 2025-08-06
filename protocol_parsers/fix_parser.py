import logging
import json
from datetime import datetime

from monitor import MESSAGES_INGESTED, PARSE_ERRORS

from .fix_tags import FIX_TAGS, MSG_TYPE_MAP, SIDE_MAP

class FixParser:
    def __init__(self, filter_config=None):
        self.logger = logging.getLogger(__name__)
        self.filter_config = filter_config or {}

    def _should_process(self, msg_dict):
        if not self.filter_config.get('enabled', False):
            return True
        
        rules = self.filter_config.get('include_only', {})
        if not rules:
            return True
            
        for tag, allowed_values in rules.items():
            tag = str(tag)
            if not allowed_values:
                continue
            
            if tag in msg_dict and msg_dict[tag] in allowed_values:
                return True
        
        self.logger.debug(f"Message filtered out: {msg_dict}")
        return False

    def _enrich(self, msg_dict):
        enriched = {"tags": {}}
        for tag, value in msg_dict.items():
            tag_str = str(tag)
            tag_name = FIX_TAGS.get(tag, f"UnknownTag_{tag}")
            
            human_readable_value = value
            if tag_name == "MsgType":
                human_readable_value = f"{value} ({MSG_TYPE_MAP.get(value, 'Unknown')})"
            elif tag_name == "Side":
                human_readable_value = f"{value} ({SIDE_MAP.get(value, 'Unknown')})"
            
            enriched["tags"][tag_name] = {
                "tag": tag,
                "value": value,
                "hr_value": human_readable_value
            }
        return enriched

    def parse(self, message_str):
        try:
            parts = message_str.strip().split('\x01')
            msg_dict = {}
            for part in parts:
                if '=' in part:
                    tag, value = part.split('=', 1)
                    msg_dict[tag] = value
            
            if not self._should_process(msg_dict):
                return None
            
            msg_dict['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            enriched_data = self._enrich(msg_dict)
            final_message = {
                "raw": msg_dict,
                "enriched": enriched_data
            }
            
            MESSAGES_INGESTED.inc()

            self.logger.debug(f"Parsed message: {final_message}")
            return final_message
        except Exception as e:

            PARSE_ERRORS.inc()
            self.logger.error(f"Failed to parse message: {message_str} - {e}")
            return None