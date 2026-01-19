"""
Danbooru API Plugin - 认证管理模块
处理API认证和凭证管理
"""

import base64
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Credentials:
    """认证凭证"""
    username: str
    api_key: str
    
    @property
    def is_valid(self) -> bool:
        """检查凭证是否有效"""
        return bool(self.username and self.api_key)
    
    def to_basic_auth(self) -> str:
        """生成Basic Auth头"""
        credentials = f"{self.username}:{self.api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def to_url_params(self) -> Dict[str, str]:
        """生成URL参数形式的认证"""
        return {
            "login": self.username,
            "api_key": self.api_key,
        }


class AuthManager:
    """认证管理器"""
    
    def __init__(self, username: str = "", api_key: str = ""):
        self._credentials: Optional[Credentials] = None
        if username and api_key:
            self.set_credentials(username, api_key)
    
    @property
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self._credentials is not None and self._credentials.is_valid
    
    @property
    def credentials(self) -> Optional[Credentials]:
        """获取当前凭证"""
        return self._credentials
    
    def set_credentials(self, username: str, api_key: str) -> bool:
        """设置认证凭证"""
        if not username or not api_key:
            return False
        
        self._credentials = Credentials(username=username, api_key=api_key)
        return True
    
    def clear_credentials(self) -> None:
        """清除认证凭证"""
        self._credentials = None
    
    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """获取认证请求头"""
        if not self.is_authenticated:
            return None
        
        return {
            "Authorization": self._credentials.to_basic_auth()
        }
    
    def get_auth_params(self) -> Optional[Dict[str, str]]:
        """获取认证URL参数"""
        if not self.is_authenticated:
            return None
        
        return self._credentials.to_url_params()
    
    def apply_auth(
        self,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        method: str = "header"
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        应用认证到请求
        
        Args:
            headers: 现有请求头
            params: 现有URL参数
            method: 认证方法 - "header" 或 "params"
        
        Returns:
            更新后的 (headers, params)
        """
        headers = headers or {}
        params = params or {}
        
        if not self.is_authenticated:
            return headers, params
        
        if method == "header":
            auth_header = self.get_auth_header()
            if auth_header:
                headers.update(auth_header)
        elif method == "params":
            auth_params = self.get_auth_params()
            if auth_params:
                params.update(auth_params)
        
        return headers, params
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """
        验证凭证格式
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self._credentials:
            return False, "未设置认证凭证"
        
        if not self._credentials.username:
            return False, "用户名不能为空"
        
        if not self._credentials.api_key:
            return False, "API Key不能为空"
        
        # Danbooru API Key 通常是特定格式
        if len(self._credentials.api_key) < 20:
            return False, "API Key格式可能不正确（长度过短）"
        
        return True, ""
    
    @staticmethod
    def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
        """
        遮蔽API Key用于显示
        
        Args:
            api_key: 原始API Key
            visible_chars: 显示的字符数
        
        Returns:
            遮蔽后的字符串
        """
        if not api_key:
            return ""
        
        if len(api_key) <= visible_chars * 2:
            return "*" * len(api_key)
        
        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars * 2) + api_key[-visible_chars:]