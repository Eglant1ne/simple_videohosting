def token_payload_is_access(payload: dict) -> bool:
    return payload['token_type'] == 'access'


def token_payload_is_refresh(payload: dict) -> bool:
    return payload['token_type'] == 'refresh'
