"""Authentication and credential handling."""

import hashlib
from typing import Any, Optional

from ..schemas.base import ApiModel


class Credentials(ApiModel):
    """Authentication credentials for Book-A-Limo API."""

    id: str
    password_hash: str
    is_customer: bool = False

    @classmethod
    def create_hash(cls, password: str, user_id: str) -> str:
        """Create password hash as required by API: Sha256(Sha256(Password) + LowerCase(Id))"""
        inner_hash = hashlib.sha256(password.encode()).hexdigest()
        full_string = inner_hash + user_id.lower()
        return hashlib.sha256(full_string.encode()).hexdigest()

    @classmethod
    def create(
        cls, user_id: str, password: str, is_customer: bool = False
    ) -> "Credentials":
        """Create credentials with automatic password hashing."""
        return cls(
            id=user_id,
            password_hash=cls.create_hash(password, user_id),
            is_customer=is_customer,
        )


def inject_credentials(
    data: dict[str, Any], credentials: Optional[Credentials]
) -> dict[str, Any]:
    """Inject credentials into request data if provided."""
    if credentials:
        data["credentials"] = credentials.model_dump()
    return data
