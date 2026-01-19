"""
Danbooru API Plugin - Users parsing helpers
"""

from typing import Dict, Any, List, Optional

from core.models import User


class UsersParseMixin:
    """用户解析工具"""

    def parse_user(self, data: Dict[str, Any]) -> User:
        return User.from_dict(data)

    def parse_users(self, data: List[Dict[str, Any]]) -> List[User]:
        return [User.from_dict(item) for item in data]

    async def get_parsed(self, user_id: int) -> Optional[User]:
        response = await self.get(user_id)
        if response.success and response.data:
            return self.parse_user(response.data)
        return None

    async def find_by_name(self, name: str) -> Optional[User]:
        response = await self.list(name=name, limit=1)
        if response.success and isinstance(response.data, list) and len(response.data) > 0:
            return self.parse_user(response.data[0])
        return None

    @staticmethod
    def get_level_name(level: int) -> str:
        level_names = {
            0: "Anonymous",
            10: "Restricted",
            20: "Member",
            30: "Gold",
            31: "Platinum",
            32: "Builder",
            35: "Contributor",
            40: "Approver",
            50: "Moderator",
            60: "Admin",
            70: "Owner",
        }
        return level_names.get(level, f"Level {level}")
