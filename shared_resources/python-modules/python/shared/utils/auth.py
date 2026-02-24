import json
import base64


class PermissionError(Exception):
    pass


def base64url_decode(input_str: str) -> bytes:
    padding = "=" * (-len(input_str) % 4)
    return base64.urlsafe_b64decode(input_str + padding)


def decode_jwt_no_verify(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        raise PermissionError("Invalid token format")

    payload = parts[1]
    decoded = base64url_decode(payload)
    return json.loads(decoded)


def get_permissions_from_event(event: dict) -> list:
    headers = event.get("headers") or {}

    token = headers.get("X-Permissions-Token") or headers.get("x-permissions-token")

    if not token:
        raise PermissionError("Missing X-Permissions-Token header")

    payload = decode_jwt_no_verify(token)

    permissions = payload.get("permissions")
    if not isinstance(permissions, list):
        raise PermissionError("Invalid permissions format")

    return permissions


def require_permission(event: dict, permission: str):
    permissions = get_permissions_from_event(event)

    if permission not in permissions:
        raise PermissionError(f"Missing permission: {permission}")


def require_any_permission(event: dict, required_permissions: list):
    """Check if user has at least one of the required permissions."""
    permissions = get_permissions_from_event(event)

    if not any(perm in permissions for perm in required_permissions):
        raise PermissionError(
            f"Missing permission: {' or '.join(required_permissions)}"
        )
