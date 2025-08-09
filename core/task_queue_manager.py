#!/usr/bin/env python3
"""
⚡ REDIS QUEUE (RQ) TASK MANAGER ⚡
Lightweight job queuing system for horizontal scaling using Redis.

Supports Upstash Redis (10MB free tier) and handles content generation,
upload processing, analytics collection, and other background tasks.
"""

import os
import redis
import logging
import json
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import time
import pickle
import traceback
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

# Try to import RQ, fallback to basic implementation if not available
try:
    from rq import Queue, Worker, Connection, get_current_job
    from rq.job import Job
    RQ_AVAILABLE = True
except ImportError:
    print("⚠️  RQ not available, using fallback queue implementation")
    RQ_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    worker_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'worker_id': self.worker_id
        }

@dataclass
class TaskConfig:
    """Task configuration"""
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: int = 300  # 5 minutes
    priority: TaskPriority = TaskPriority.MEDIUM
    queue_name: str = "default"

class TaskQueueManager:
    """
    ⚡ REDIS QUEUE TASK MANAGER ⚡
    
    Manages background task execution with Redis queuing for horizontal scaling.
    Supports both RQ (when available) and fallback implementation.
    """
    
    def __init__(self, redis_url: Optional[str] = None, use_upstash: bool = True):
        """
        Initialize task queue manager
        
        Args:
            redis_url: Redis connection URL (optional, will use env vars)
            use_upstash: Whether to use Upstash Redis configuration
        """
        self.redis_url = redis_url or self._get_redis_url(use_upstash)
        self.redis_client = self._connect_redis()
        
        # Initialize queues based on available backend
        if RQ_AVAILABLE and self.redis_client:
            self._init_rq_backend()
        else:
            self._init_fallback_backend()
        
        # Task registry and results storage
        self.task_registry: Dict[str, Callable] = {}
        self.active_workers: Dict[str, threading.Thread] = {}
        self.shutdown_event = threading.Event()
        
        # Register built-in tasks
        self._register_builtin_tasks()
        
        logger.info(f"⚡ Task Queue Manager initialized with {self.backend_type} backend")
    
    def _get_redis_url(self, use_upstash: bool = True) -> str:
        """Get Redis connection URL from environment"""
        if use_upstash:
            # Upstash Redis configuration
            upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
            upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
            
            if upstash_url and upstash_token:
                # Convert REST URL to Redis URL format
                return upstash_url.replace('https://', f'redis://:{upstash_token}@').replace(':443', ':6379')
        
        # Standard Redis configuration
        return (os.getenv('REDIS_URL') or 
                os.getenv('REDIS_DSN') or 
                'redis://localhost:6379/0')
    
    def _connect_redis(self) -> Optional[redis.Redis]:
        """Connect to Redis server"""
        try:
            client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Test connection
            client.ping()
            logger.info(f"✅ Connected to Redis: {self.redis_url}")
            return client
            
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            return None
    
    def _init_rq_backend(self):
        """Initialize RQ (Redis Queue) backend"""
        self.backend_type = "RQ"
        self.connection = self.redis_client
        
        # Create queues with different priorities
        self.queues = {
            'urgent': Queue('urgent', connection=self.connection),
            'high': Queue('high', connection=self.connection),
            'medium': Queue('medium', connection=self.connection),
            'low': Queue('low', connection=self.connection)
        }
        
        logger.info("✅ RQ backend initialized with priority queues")
    
    def _init_fallback_backend(self):
        """Initialize fallback in-memory backend"""
        self.backend_type = "Fallback"
        
        # In-memory queues
        self.queues = {
            'urgent': queue.PriorityQueue(),
            'high': queue.PriorityQueue(),
            'medium': queue.PriorityQueue(),
            'low': queue.PriorityQueue()
        }
        
        # Task execution pools
        self.executor_pools = {
            'urgent': ThreadPoolExecutor(max_workers=4, thread_name_prefix='urgent'),
            'high': ThreadPoolExecutor(max_workers=3, thread_name_prefix='high'),
            'medium': ThreadPoolExecutor(max_workers=2, thread_name_prefix='medium'),
            'low': ThreadPoolExecutor(max_workers=1, thread_name_prefix='low')
        }
        
        logger.info("✅ Fallback backend initialized with thread pools")
    
    def _register_builtin_tasks(self):
        """Register built-in task functions"""
        @self.task(queue_name="high", max_retries=3, timeout=600)
        def generate_video_content(channel_id: str, content_config: Dict[str, Any]) -> Dict[str, Any]:
            """Generate video content for a channel"""
            from core.real_content_generator import RealContentGenerator
            
            generator = RealContentGenerator()
            result = generator.generate_optimized_content(
                niche=content_config.get('niche', 'general'),
                target_audience=content_config.get('target_audience', 'general'),
                content_type=content_config.get('content_type', 'educational'),
                duration_target=content_config.get('duration_target', 300)
            )
            
            return {
                'channel_id': channel_id,
                'content': result,
                'generated_at': datetime.now().isoformat()
            }
        
        @self.task(queue_name="medium", max_retries=2, timeout=300)
        def upload_to_platform(platform: str, content_data: Dict[str, Any], channel_config: Dict[str, Any]) -> Dict[str, Any]:
            """Upload content to a platform"""
            # This would integrate with platform-specific upload APIs
            # For now, simulate upload
            time.sleep(5)  # Simulate upload time
            
            return {
                'platform': platform,
                'upload_id': f"upload_{int(time.time())}",
                'status': 'success',
                'url': f"https://{platform}.com/watch?v=example",
                'uploaded_at': datetime.now().isoformat()
            }
        
        @self.task(queue_name="low", max_retries=1, timeout=120)
        def collect_analytics(channel_id: str, platform: str, date_range: Dict[str, str]) -> Dict[str, Any]:
            """Collect analytics data for a channel"""
            from analytics_collector import AnalyticsCollector
            
            collector = AnalyticsCollector()
            analytics_data = collector.collect_channel_analytics(
                channel_id=channel_id,
                platform=platform,
                start_date=date_range.get('start_date'),
                end_date=date_range.get('end_date')
            )
            
            return analytics_data
        
        @self.task(queue_name="medium", max_retries=2, timeout=180)
        def run_compliance_check(content_data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
            """Run compliance checks on content"""
            from core.content_policy_checker import ContentPolicyChecker
            
            checker = ContentPolicyChecker()
            compliance_result = checker.check_content(content_data, rules)
            
            return compliance_result
    
    def task(self, queue_name: str = "medium", max_retries: int = 3, timeout: int = 300, priority: TaskPriority = TaskPriority.MEDIUM):
        """
        Decorator to register a function as a queueable task
        
        Usage:
            @queue_manager.task(queue_name="high", max_retries=5)
            def my_task(arg1, arg2):
                return "result"
        """
        def decorator(func: Callable) -> Callable:
            task_name = func.__name__
            
            # Store task configuration
            func._task_config = TaskConfig(
                max_retries=max_retries,
                timeout=timeout,
                priority=priority,
                queue_name=queue_name
            )
            
            # Register task
            self.task_registry[task_name] = func
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # When called directly, execute immediately
                return func(*args, **kwargs)
            
            # Add queue method
            wrapper.queue = lambda *args, **kwargs: self.enqueue_task(
                task_name, args, kwargs, 
                queue_name=queue_name,
                max_retries=max_retries,
                timeout=timeout,
                priority=priority
            )
            
            return wrapper
        return decorator
    
    def enqueue_task(self, task_name: str, args: tuple = (), kwargs: dict = None, 
                    queue_name: str = "medium", max_retries: int = 3, 
                    timeout: int = 300, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """
        Enqueue a task for background execution
        
        Returns:
            Task ID for tracking
        """
        if kwargs is None:
            kwargs = {}
        
        task_id = f"{task_name}_{int(time.time() * 1000000)}"
        
        if self.backend_type == "RQ" and task_name in self.task_registry:
            # Use RQ backend
            queue_obj = self.queues.get(queue_name, self.queues['medium'])
            
            job = queue_obj.enqueue_call(
                func=self.task_registry[task_name],
                args=args,
                kwargs=kwargs,
                job_id=task_id,
                timeout=timeout,
                retry=max_retries
            )
            
            logger.info(f"📤 Enqueued RQ task: {task_name} ({task_id}) in queue: {queue_name}")
            return task_id
        
        else:
            # Use fallback backend
            task_data = {
                'task_id': task_id,
                'task_name': task_name,
                'args': args,
                'kwargs': kwargs,
                'max_retries': max_retries,
                'timeout': timeout,
                'priority': priority,
                'enqueued_at': time.time()
            }
            
            # Add to appropriate queue
            queue_obj = self.queues.get(queue_name, self.queues['medium'])
            queue_obj.put((priority.value, task_data))
            
            # Store task result placeholder
            self._store_task_result(TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING
            ))
            
            logger.info(f"📤 Enqueued fallback task: {task_name} ({task_id}) in queue: {queue_name}")
            return task_id
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a task by ID"""
        if self.backend_type == "RQ":
            try:
                job = Job.fetch(task_id, connection=self.connection)
                
                if job.is_finished:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.COMPLETED,
                        result=job.result,
                        started_at=job.started_at,
                        completed_at=job.ended_at
                    )
                elif job.is_failed:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        error=str(job.exc_info),
                        started_at=job.started_at,
                        completed_at=job.ended_at
                    )
                elif job.is_started:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.RUNNING,
                        started_at=job.started_at
                    )
                else:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.PENDING
                    )
                    
            except Exception as e:
                logger.error(f"Failed to fetch RQ job {task_id}: {e}")
                return None
        
        else:
            # Fallback: get from Redis storage
            return self._get_stored_task_result(task_id)
    
    def start_worker(self, queues: List[str] = None, worker_name: str = None) -> str:
        """Start a background worker"""
        if queues is None:
            queues = ['urgent', 'high', 'medium', 'low']
        
        worker_id = worker_name or f"worker_{int(time.time())}"
        
        if self.backend_type == "RQ":
            # Start RQ worker
            queue_objects = [self.queues[q] for q in queues if q in self.queues]
            
            def run_rq_worker():
                worker = Worker(queue_objects, connection=self.connection, name=worker_id)
                worker.work(with_scheduler=True)
            
            worker_thread = threading.Thread(target=run_rq_worker, name=f"rq_worker_{worker_id}")
            worker_thread.daemon = True
            worker_thread.start()
            
        else:
            # Start fallback worker
            def run_fallback_worker():
                while not self.shutdown_event.is_set():
                    try:
                        # Check each queue in priority order
                        for queue_name in ['urgent', 'high', 'medium', 'low']:
                            if queue_name not in queues:
                                continue
                                
                            queue_obj = self.queues[queue_name]
                            
                            try:
                                priority, task_data = queue_obj.get(timeout=1)
                                self._execute_fallback_task(task_data, worker_id)
                                queue_obj.task_done()
                            except:
                                continue
                    
                    except Exception as e:
                        logger.error(f"Worker {worker_id} error: {e}")
                        time.sleep(5)
            
            worker_thread = threading.Thread(target=run_fallback_worker, name=f"fallback_worker_{worker_id}")
            worker_thread.daemon = True
            worker_thread.start()
        
        self.active_workers[worker_id] = worker_thread
        logger.info(f"🔄 Started worker: {worker_id} for queues: {queues}")
        return worker_id
    
    def _execute_fallback_task(self, task_data: Dict[str, Any], worker_id: str):
        """Execute a task in the fallback backend"""
        task_id = task_data['task_id']
        task_name = task_data['task_name']
        
        # Update task status to running
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
            worker_id=worker_id
        )
        self._store_task_result(result)
        
        try:
            # Get task function
            task_func = self.task_registry.get(task_name)
            if not task_func:
                raise ValueError(f"Task function '{task_name}' not found")
            
            # Execute task
            task_result = task_func(*task_data['args'], **task_data['kwargs'])
            
            # Update result
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            result.completed_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
        
        self._store_task_result(result)
    
    def _store_task_result(self, result: TaskResult):
        """Store task result in Redis"""
        if self.redis_client:
            try:
                key = f"task_result:{result.task_id}"
                data = json.dumps(result.to_dict())
                self.redis_client.setex(key, 3600, data)  # Store for 1 hour
            except Exception as e:
                logger.error(f"Failed to store task result: {e}")
    
    def _get_stored_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get stored task result from Redis"""
        if self.redis_client:
            try:
                key = f"task_result:{task_id}"
                data = self.redis_client.get(key)
                if data:
                    result_data = json.loads(data)
                    return TaskResult(
                        task_id=result_data['task_id'],
                        status=TaskStatus(result_data['status']),
                        result=result_data.get('result'),
                        error=result_data.get('error'),
                        started_at=datetime.fromisoformat(result_data['started_at']) if result_data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(result_data['completed_at']) if result_data.get('completed_at') else None,
                        retry_count=result_data.get('retry_count', 0),
                        worker_id=result_data.get('worker_id')
                    )
            except Exception as e:
                logger.error(f"Failed to get stored task result: {e}")
        
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            'backend_type': self.backend_type,
            'active_workers': len(self.active_workers),
            'registered_tasks': len(self.task_registry),
            'queues': {}
        }
        
        if self.backend_type == "RQ":
            for name, queue_obj in self.queues.items():
                stats['queues'][name] = {
                    'pending_jobs': len(queue_obj),
                    'failed_jobs': queue_obj.failed_job_registry.count,
                    'started_jobs': queue_obj.started_job_registry.count
                }
        else:
            for name, queue_obj in self.queues.items():
                stats['queues'][name] = {
                    'pending_jobs': queue_obj.qsize()
                }
        
        return stats
    
    def shutdown(self):
        """Shutdown all workers and cleanup"""
        logger.info("🛑 Shutting down task queue manager...")
        
        self.shutdown_event.set()
        
        # Wait for workers to finish
        for worker_id, worker_thread in self.active_workers.items():
            worker_thread.join(timeout=10)
            logger.info(f"✅ Worker {worker_id} shut down")
        
        # Cleanup executor pools
        if hasattr(self, 'executor_pools'):
            for pool in self.executor_pools.values():
                pool.shutdown(wait=True)
        
        logger.info("✅ Task queue manager shut down")


# Example usage and testing
if __name__ == "__main__":
    # Initialize task queue manager
    queue_manager = TaskQueueManager()
    
    # Start a worker
    worker_id = queue_manager.start_worker(['high', 'medium'])
    
    # Example: Enqueue video generation task
    task_id = queue_manager.enqueue_task(
        'generate_video_content',
        args=('tech-focus',),
        kwargs={
            'content_config': {
                'niche': 'technology',
                'target_audience': 'tech_enthusiasts',
                'content_type': 'tutorial',
                'duration_target': 600
            }
        },
        queue_name='high'
    )
    
    print(f"📤 Enqueued task: {task_id}")
    
    # Check queue stats
    stats = queue_manager.get_queue_stats()
    print(f"📊 Queue Stats: {json.dumps(stats, indent=2)}")
    
    # Wait a bit and check result
    time.sleep(2)
    result = queue_manager.get_task_result(task_id)
    if result:
        print(f"📋 Task Status: {result.status.value}")
        if result.error:
            print(f"❌ Error: {result.error}")
    
    # Shutdown
    time.sleep(5)
    queue_manager.shutdown()
