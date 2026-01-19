"""
Danbooru API Plugin - Moderation 服务
管理/审核相关的所有API操作
"""

from .base import BaseService
from .moderation_modqueue import ModerationModqueueMixin
from .moderation_appeals import ModerationAppealsMixin
from .moderation_flags import ModerationFlagsMixin
from .moderation_approvals import ModerationApprovalsMixin
from .moderation_mod_actions import ModerationModActionsMixin
from .moderation_reports import ModerationReportsMixin
from .moderation_bans import ModerationBansMixin
from .moderation_feedbacks import ModerationFeedbacksMixin
from .moderation_bulk_updates import ModerationBulkUpdatesMixin


class ModerationService(
    ModerationModqueueMixin,
    ModerationAppealsMixin,
    ModerationFlagsMixin,
    ModerationApprovalsMixin,
    ModerationModActionsMixin,
    ModerationReportsMixin,
    ModerationBansMixin,
    ModerationFeedbacksMixin,
    ModerationBulkUpdatesMixin,
    BaseService,
):
    """管理服务 - 处理所有审核/管理相关的API操作"""

    _endpoint_prefix = ""
