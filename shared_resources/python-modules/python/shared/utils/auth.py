import json
import base64
import os
import jwt
import requests
from functools import lru_cache


class PermissionError(Exception):
    pass


@lru_cache(maxsize=1)
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys (JWKS)."""
    AWS_REGION = os.environ["AWS_REGION"]
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    
    if not user_pool_id:
        raise PermissionError("COGNITO_USER_POOL_ID environment variable not set")
    
    jwks_url = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    return response.json()


def get_signing_key(token: str):
    """Get the signing key for a given token from Cognito JWKS."""
    jwks = get_cognito_public_keys()
    unverified_header = jwt.get_unverified_header(token)
    
    for key in jwks.get("keys", []):
        if key["kid"] == unverified_header["kid"]:
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    
    raise PermissionError("Unable to find matching signing key")


def decode_jwt(token: str) -> dict:
    """Decode and verify JWT token against Cognito public keys."""
    try:
        signing_key = get_signing_key(token)
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Cognito doesn't always set aud
        )
    except jwt.ExpiredSignatureError:
        raise PermissionError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise PermissionError(f"Invalid token: {e}")


# Keep for backward compatibility but mark as unsafe
def decode_jwt_no_verify(token: str) -> dict:
    """
    DEPRECATED: Use decode_jwt() instead.
    WARNING: This does not verify the token signature.
    Only use if token was already verified by API Gateway/ALB.
    """
    parts = token.split(".")
    if len(parts) < 2:
        raise PermissionError("Invalid token format")

    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload + padding)
    return json.loads(decoded)


def get_permissions_from_event(event: dict) -> list:
    headers = event.get("headers") or {}

    token = headers.get("X-Permissions-Token") or headers.get("x-permissions-token")

    if not token:
        raise PermissionError("Missing X-Permissions-Token header")

    # Use verified decoding
    payload = decode_jwt(token)

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
