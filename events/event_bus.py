"""
Danbooru API Plugin - 事件总线模块
核心事件分发和订阅机制
"""

import asyncio
from typing import (
    Dict, List, Callable, Any, Optional, Set, 
    Awaitable, Union
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
import uuid
from collections import defaultdict

from astrbot.api import logger


class EventPriority(IntEnum):
    """事件处理优先级"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    MONITOR = 200  # 仅监控，不修改事件


@dataclass
class Event:
    """基础事件类"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 事件控制
    _cancelled: bool = field(default=False, repr=False)
    _propagation_stopped: bool = field(default=False, repr=False)
    _results: List[Any] = field(default_factory=list, repr=False)
    
    @property
    def is_cancelled(self) -> bool:
        """事件是否已取消"""
        return self._cancelled
    
    def cancel(self) -> None:
        """取消事件"""
        self._cancelled = True
    
    def stop_propagation(self) -> None:
        """停止事件传播"""
        self._propagation_stopped = True
    
    @property
    def is_propagation_stopped(self) -> bool:
        """事件传播是否已停止"""
        return self._propagation_stopped
    
    def add_result(self, result: Any) -> None:
        """添加处理结果"""
        self._results.append(result)
    
    @property
    def results(self) -> List[Any]:
        """获取所有处理结果"""
        return self._results.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "is_cancelled": self._cancelled,
        }


# 事件处理器类型
EventHandler = Callable[[Event], Awaitable[Optional[Any]]]


@dataclass
class HandlerRegistration:
    """处理器注册信息"""
    handler: EventHandler
    priority: EventPriority
    event_types: Set[str]
    once: bool = False  # 是否只执行一次
    filter_func: Optional[Callable[[Event], bool]] = None
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def matches(self, event: Event) -> bool:
        """检查是否匹配事件"""
        # 检查事件类型
        if self.event_types and event.event_type not in self.event_types:
            if "*" not in self.event_types:  # 通配符匹配所有
                return False
        
        # 检查过滤器
        if self.filter_func and not self.filter_func(event):
            return False
        
        return True


class EventBus:
    """事件总线 - 核心事件分发机制"""
    
    _instance: Optional['EventBus'] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._handlers: Dict[str, List[HandlerRegistration]] = defaultdict(list)
        self._global_handlers: List[HandlerRegistration] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._is_running: bool = False
        self._processor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # 统计信息
        self._event_count: int = 0
        self._handler_count: int = 0
        
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（用于测试）"""
        cls._instance = None
    
    # ==================== 处理器注册 ====================
    
    def subscribe(
        self,
        event_types: Union[str, List[str], Set[str]],
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        """
        订阅事件
        
        Args:
            event_types: 事件类型（字符串或列表）
            handler: 事件处理器
            priority: 处理优先级
            once: 是否只执行一次
            filter_func: 事件过滤函数
        
        Returns:
            处理器ID
        """
        # 规范化事件类型
        if isinstance(event_types, str):
            event_types = {event_types}
        elif isinstance(event_types, list):
            event_types = set(event_types)
        
        registration = HandlerRegistration(
            handler=handler,
            priority=priority,
            event_types=event_types,
            once=once,
            filter_func=filter_func,
        )
        
        # 注册到对应的事件类型
        for event_type in event_types:
            self._handlers[event_type].append(registration)
            # 按优先级排序（高优先级在前）
            self._handlers[event_type].sort(key=lambda x: -x.priority)
        
        # 如果是通配符，添加到全局处理器
        if "*" in event_types:
            self._global_handlers.append(registration)
            self._global_handlers.sort(key=lambda x: -x.priority)
        
        self._handler_count += 1
        return registration.handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """
        取消订阅
        
        Args:
            handler_id: 处理器ID
        
        Returns:
            是否成功取消
        """
        found = False
        
        # 从所有事件类型中移除
        for event_type in list(self._handlers.keys()):
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] 
                if h.handler_id != handler_id
            ]
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            else:
                found = True
        
        # 从全局处理器中移除
        original_len = len(self._global_handlers)
        self._global_handlers = [
            h for h in self._global_handlers 
            if h.handler_id != handler_id
        ]
        if len(self._global_handlers) < original_len:
            found = True
        
        if found:
            self._handler_count -= 1
        
        return found
    
    def on(
        self,
        event_types: Union[str, List[str]],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ):
        """
        装饰器方式订阅事件
        
        Usage:
            @event_bus.on("post.created")
            async def handle_post_created(event):
                ...
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_types, handler, priority, once, filter_func)
            return handler
        return decorator
    
    def once(
        self,
        event_types: Union[str, List[str]],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ):
        """一次性订阅装饰器"""
        return self.on(event_types, priority, once=True, filter_func=filter_func)
    
    # ==================== 事件发布 ====================
    
    async def emit(self, event: Event) -> Event:
        """
        同步发布事件（立即处理）
        
        Args:
            event: 事件对象
        
        Returns:
            处理后的事件
        """
        self._event_count += 1
        
        # 收集匹配的处理器
        handlers: List[HandlerRegistration] = []
        
        # 特定类型的处理器
        if event.event_type in self._handlers:
            handlers.extend(self._handlers[event.event_type])
        
        # 全局处理器
        handlers.extend(self._global_handlers)
        
        # 去重并按优先级排序
        seen_ids = set()
        unique_handlers = []
        for h in handlers:
            if h.handler_id not in seen_ids:
                seen_ids.add(h.handler_id)
                unique_handlers.append(h)
        
        unique_handlers.sort(key=lambda x: -x.priority)
        
        # 需要移除的一次性处理器
        handlers_to_remove = []
        
        # 执行处理器
        for registration in unique_handlers:
            if event.is_propagation_stopped:
                break
            
            if not registration.matches(event):
                continue
            
            try:
                result = await registration.handler(event)
                if result is not None:
                    event.add_result(result)
                
                if registration.once:
                    handlers_to_remove.append(registration.handler_id)
                    
            except Exception as e:
                # 发布错误事件
                error_event = Event(
                    event_type="error.handler",
                    source="event_bus",
                    data={
                        "original_event": event.to_dict(),
                        "handler_id": registration.handler_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                # 避免无限递归
                if event.event_type != "error.handler":
                    await self.emit(error_event)
        
        # 移除一次性处理器
        for handler_id in handlers_to_remove:
            self.unsubscribe(handler_id)
        
        return event
    
    async def emit_async(self, event: Event) -> None:
        """
        异步发布事件（放入队列）
        
        Args:
            event: 事件对象
        """
        await self._event_queue.put(event)
    
    def emit_nowait(self, event: Event) -> None:
        """
        非阻塞发布事件
        
        Args:
            event: 事件对象
        """
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # 队列满时丢弃事件
    
    # ==================== 事件处理器 ====================
    
    async def start(self) -> None:
        """启动事件处理器"""
        if self._is_running:
            return
        
        self._is_running = True
        self._processor_task = asyncio.create_task(self._process_events())
    
    async def stop(self) -> None:
        """停止事件处理器"""
        self._is_running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None
    
    async def _process_events(self) -> None:
        """事件处理循环"""
        while self._is_running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self.emit(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但继续运行
                logger.error(f"事件处理错误: {e}")
    
    # ==================== 工具方法 ====================
    
    def clear(self) -> None:
        """清除所有处理器"""
        self._handlers.clear()
        self._global_handlers.clear()
        self._handler_count = 0
    
    def get_handlers(self, event_type: str) -> List[HandlerRegistration]:
        """获取指定事件类型的处理器"""
        return self._handlers.get(event_type, []).copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "event_count": self._event_count,
            "handler_count": self._handler_count,
            "event_types": list(self._handlers.keys()),
            "queue_size": self._event_queue.qsize(),
            "is_running": self._is_running,
        }
    
    async def wait_for(
        self,
        event_type: str,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ) -> Optional[Event]:
        """
        等待特定事件
        
        Args:
            event_type: 事件类型
            timeout: 超时时间（秒）
            filter_func: 过滤函数
        
        Returns:
            匹配的事件，超时返回None
        """
        future: asyncio.Future = asyncio.Future()
        
        async def handler(event: Event) -> None:
            if not future.done():
                future.set_result(event)
        
        handler_id = self.subscribe(
            event_type,
            handler,
            priority=EventPriority.HIGHEST,
            once=True,
            filter_func=filter_func,
        )
        
        try:
            if timeout:
                return await asyncio.wait_for(future, timeout)
            else:
                return await future
        except asyncio.TimeoutError:
            self.unsubscribe(handler_id)
            return None


# 全局事件总线实例
event_bus = EventBus.get_instance()