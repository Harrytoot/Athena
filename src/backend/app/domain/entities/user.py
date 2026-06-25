from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[str] = None
    username: str = ""
    email: str = ""
    display_name: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True
