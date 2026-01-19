"""
Danbooru API Plugin - Users 服务
用户相关的所有API操作
"""

from .base import SearchableService
from .users_core import UsersCoreMixin
from .users_profile import UsersProfileMixin
from .users_email import UsersEmailMixin
from .users_password import UsersPasswordMixin
from .users_api_key import UsersApiKeyMixin
from .users_feedbacks import UsersFeedbacksMixin
from .users_name_change import UsersNameChangeMixin
from .users_parse import UsersParseMixin


class UsersService(
    UsersCoreMixin,
    UsersProfileMixin,
    UsersEmailMixin,
    UsersPasswordMixin,
    UsersApiKeyMixin,
    UsersFeedbacksMixin,
    UsersNameChangeMixin,
    UsersParseMixin,
    SearchableService,
):
    """用户服务 - 处理所有用户相关的API操作"""

    _endpoint_prefix = "users"
