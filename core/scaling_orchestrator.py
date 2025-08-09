#!/usr/bin/env python3
"""
🚀 SCALING ORCHESTRATOR 🚀
Advanced orchestration system for horizontal scaling across multiple channels,
platforms, and worker processes with compliance checking and queue management.

Integrates:
- Multi-channel configuration management
- Redis Queue (RQ) task management
- Content policy compliance checking
- Worker scaling and distribution
- Performance monitoring and optimization
"""

import os
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

# Import our custom modules
from core.channel_config_manager import ChannelConfigManager, ChannelConfig
from core.task_queue_manager import TaskQueueManager, TaskPriority, TaskStatus
from core.content_policy_checker import ContentPolicyChecker, ComplianceResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScalingMetrics:
    """Scaling performance metrics"""
    active_channels: int
    total_workers: int
    tasks_pending: int
    tasks_completed_last_hour: int
    average_task_duration: float
    compliance_pass_rate: float
    error_rate: float
    throughput_per_hour: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class WorkerAllocation:
    """Worker allocation configuration"""
    channel_id: str
    platform: str
    worker_count: int
    queue_names: List[str]
    priority_level: int
    resource_limits: Dict[str, Any]

class ScalingOrchestrator:
    """
    🚀 COMPREHENSIVE SCALING ORCHESTRATOR 🚀
    
    Manages horizontal scaling across multiple channels with:
    - Dynamic worker allocation
    - Queue-based task distribution
    - Compliance checking integration
    - Performance monitoring
    - Resource optimization
    """
    
    def __init__(self, 
                 channels_dir: str = "channels",
                 redis_url: Optional[str] = None,
                 max_workers_per_channel: int = 5,
                 enable_compliance_checking: bool = True):
        """
        Initialize the scaling orchestrator
        
        Args:
            channels_dir: Directory containing channel configurations
            redis_url: Redis URL for task queue (optional)
            max_workers_per_channel: Maximum workers per channel
            enable_compliance_checking: Whether to enable compliance checks
        """
        # Initialize core components
        self.config_manager = ChannelConfigManager(channels_dir)
        self.task_manager = TaskQueueManager(redis_url)
        self.policy_checker = ContentPolicyChecker() if enable_compliance_checking else None
        
        # Scaling configuration
        self.max_workers_per_channel = max_workers_per_channel
        self.enable_compliance = enable_compliance_checking
        
        # Runtime state
        self.active_workers: Dict[str, List[str]] = {}  # channel_id -> [worker_ids]
        self.worker_allocations: Dict[str, WorkerAllocation] = {}
        self.performance_metrics: Dict[str, Any] = {}
        self.shutdown_event = threading.Event()
        
        # Performance tracking
        self.metrics_history: List[ScalingMetrics] = []
        self.task_completion_times: List[float] = []
        self.compliance_results: List[bool] = []
        
        # Start background monitoring
        self._start_monitoring_thread()
        
        logger.info(f"🚀 Scaling Orchestrator initialized with {len(self.config_manager.get_all_channels())} channels")
    
    def scale_system(self, target_throughput: int = 100, optimization_strategy: str = "balanced") -> Dict[str, Any]:
        """
        Scale the entire system based on target throughput and strategy
        
        Args:
            target_throughput: Target tasks per hour
            optimization_strategy: 'performance', 'cost', 'balanced'
            
        Returns:
            Scaling results and metrics
        """
        logger.info(f"🎯 Scaling system for {target_throughput} tasks/hour with '{optimization_strategy}' strategy")
        
        start_time = time.time()
        scaling_results = {
            'target_throughput': target_throughput,
            'strategy': optimization_strategy,
            'channels_scaled': [],
            'workers_created': 0,
            'estimated_capacity': 0,
            'scaling_time': 0
        }
        
        try:
            # Get all channels and their configurations
            channels = self.config_manager.get_all_channels()
            
            # Calculate per-channel allocation based on strategy
            allocations = self._calculate_worker_allocations(
                channels, target_throughput, optimization_strategy
            )
            
            # Scale each channel
            for channel_id, allocation in allocations.items():
                channel_result = self._scale_channel(channel_id, allocation)
                scaling_results['channels_scaled'].append({
                    'channel_id': channel_id,
                    'workers': channel_result['workers_created'],
                    'queues': channel_result['queues_assigned'],
                    'estimated_throughput': channel_result['estimated_throughput']
                })
                
                scaling_results['workers_created'] += channel_result['workers_created']
                scaling_results['estimated_capacity'] += channel_result['estimated_throughput']
            
            # Start content generation for all channels
            if scaling_results['workers_created'] > 0:
                self._start_content_generation_workflows()
            
        except Exception as e:
            logger.error(f"❌ Scaling failed: {e}")
            scaling_results['error'] = str(e)
        
        scaling_results['scaling_time'] = time.time() - start_time
        logger.info(f"✅ Scaling completed: {scaling_results['workers_created']} workers, "
                   f"~{scaling_results['estimated_capacity']} tasks/hour capacity")
        
        return scaling_results
    
    def _calculate_worker_allocations(self, channels: Dict[str, ChannelConfig], 
                                    target_throughput: int, strategy: str) -> Dict[str, WorkerAllocation]:
        """Calculate optimal worker allocation across channels"""
        allocations = {}
        
        # Priority weights based on strategy
        strategy_weights = {
            'performance': {'high': 3, 'medium': 2, 'low': 1},
            'cost': {'high': 1, 'medium': 2, 'low': 3},
            'balanced': {'high': 2, 'medium': 2, 'low': 2}
        }
        weights = strategy_weights.get(strategy, strategy_weights['balanced'])
        
        # Calculate priority scores for channels
        channel_priorities = {}
        for channel_id, config in channels.items():
            scaling_config = config.scaling
            priority = scaling_config.get('worker_config', {}).get('queue_priority', 'medium')
            
            # Factor in enabled platforms and content types
            platform_count = len([p for p, s in config.platform.items() if s.get('enabled', False)])
            content_types = len(config.content.get('content_types', []))
            
            priority_score = (
                weights[priority] * 
                platform_count * 
                (1 + content_types * 0.1)
            )
            channel_priorities[channel_id] = priority_score
        
        # Normalize and allocate workers
        total_priority = sum(channel_priorities.values())
        remaining_throughput = target_throughput
        
        for channel_id, config in channels.items():
            if remaining_throughput <= 0:
                break
                
            # Calculate allocation percentage
            allocation_ratio = channel_priorities[channel_id] / total_priority
            channel_throughput = int(target_throughput * allocation_ratio)
            
            # Convert throughput to worker count (assuming ~20 tasks/hour per worker)
            tasks_per_worker_per_hour = 20
            worker_count = max(1, min(
                self.max_workers_per_channel,
                (channel_throughput + tasks_per_worker_per_hour - 1) // tasks_per_worker_per_hour
            ))
            
            # Get scaling configuration
            scaling_config = config.scaling
            worker_config = scaling_config.get('worker_config', {})
            
            # Determine queue assignment based on priority
            priority = worker_config.get('queue_priority', 'medium')
            queues = self._get_queue_assignment(priority, config.platform)
            
            allocations[channel_id] = WorkerAllocation(
                channel_id=channel_id,
                platform=','.join([p for p in config.platform.keys() if config.platform[p].get('enabled')]),
                worker_count=worker_count,
                queue_names=queues,
                priority_level=weights[priority],
                resource_limits=scaling_config.get('resource_limits', {})
            )
            
            remaining_throughput -= worker_count * tasks_per_worker_per_hour
        
        return allocations
    
    def _get_queue_assignment(self, priority: str, platforms: Dict[str, Any]) -> List[str]:
        """Get appropriate queue assignment based on priority and platforms"""
        base_queues = []
        
        # Map priority to queue names
        priority_queues = {
            'urgent': ['urgent', 'high'],
            'high': ['high', 'medium'],
            'medium': ['medium', 'low'],
            'low': ['low']
        }
        
        base_queues = priority_queues.get(priority, ['medium'])
        
        # Add platform-specific queues if needed
        enabled_platforms = [p for p, config in platforms.items() if config.get('enabled', False)]
        
        # For multi-platform channels, prioritize accordingly
        if len(enabled_platforms) > 1:
            base_queues = ['high'] + base_queues
        
        return list(set(base_queues))  # Remove duplicates
    
    def _scale_channel(self, channel_id: str, allocation: WorkerAllocation) -> Dict[str, Any]:
        """Scale a specific channel with the given allocation"""
        logger.info(f"🔄 Scaling channel {channel_id}: {allocation.worker_count} workers on {allocation.platform}")
        
        result = {
            'workers_created': 0,
            'queues_assigned': allocation.queue_names,
            'estimated_throughput': 0
        }
        
        try:
            # Get channel configuration
            config = self.config_manager.get_channel_config(channel_id)
            if not config:
                raise ValueError(f"Channel configuration not found: {channel_id}")
            
            # Create workers for this channel
            worker_ids = []
            for i in range(allocation.worker_count):
                worker_name = f"{channel_id}_worker_{i+1}"
                worker_id = self.task_manager.start_worker(
                    queues=allocation.queue_names,
                    worker_name=worker_name
                )
                worker_ids.append(worker_id)
                result['workers_created'] += 1
            
            # Store worker allocation
            self.active_workers[channel_id] = worker_ids
            self.worker_allocations[channel_id] = allocation
            
            # Calculate estimated throughput (20 tasks/hour per worker)
            result['estimated_throughput'] = allocation.worker_count * 20
            
            logger.info(f"✅ Channel {channel_id} scaled: {result['workers_created']} workers")
            
        except Exception as e:
            logger.error(f"❌ Failed to scale channel {channel_id}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _start_content_generation_workflows(self):
        """Start content generation workflows for all active channels"""
        logger.info("🎬 Starting content generation workflows...")
        
        for channel_id in self.active_workers.keys():
            self._schedule_channel_content(channel_id)
    
    def _schedule_channel_content(self, channel_id: str):
        """Schedule content generation tasks for a specific channel"""
        try:
            config = self.config_manager.get_channel_config(channel_id)
            if not config:
                return
            
            # Get content configuration
            content_config = config.content
            platforms = [p for p, s in config.platform.items() if s.get('enabled', False)]
            
            # Schedule content generation for each enabled platform
            for platform in platforms:
                # Get platform-specific specs
                platform_specs = content_config.get('video_specs', {}).get(platform, {})
                
                # Prepare content generation task
                task_config = {
                    'niche': content_config.get('niche', 'general'),
                    'target_audience': content_config.get('target_audience', 'general'),
                    'content_type': content_config.get('content_types', ['educational'])[0],
                    'duration_target': platform_specs.get('duration', [300, 600])[0],
                    'platform': platform,
                    'channel_config': asdict(config)
                }
                
                # Enqueue content generation task
                task_id = self.task_manager.enqueue_task(
                    'generate_video_content',
                    args=(channel_id,),
                    kwargs={'content_config': task_config},
                    queue_name='high',
                    priority=TaskPriority.HIGH
                )
                
                logger.info(f"📤 Scheduled content generation: {task_id} for {channel_id}/{platform}")
                
                # If compliance checking is enabled, chain compliance task
                if self.enable_compliance and self.policy_checker:
                    self._schedule_compliance_check(channel_id, task_id, task_config)
        
        except Exception as e:
            logger.error(f"❌ Failed to schedule content for {channel_id}: {e}")
    
    def _schedule_compliance_check(self, channel_id: str, content_task_id: str, content_config: Dict[str, Any]):
        """Schedule compliance check for generated content"""
        try:
            # Get compliance rules from channel config
            config = self.config_manager.get_channel_config(channel_id)
            compliance_rules = config.compliance if config else {}
            
            # Enqueue compliance check task
            compliance_task_id = self.task_manager.enqueue_task(
                'run_compliance_check',
                kwargs={
                    'content_data': {'channel_id': channel_id, 'parent_task': content_task_id},
                    'rules': compliance_rules.get('content_policy', {})
                },
                queue_name='medium',
                priority=TaskPriority.MEDIUM
            )
            
            logger.info(f"🛡️ Scheduled compliance check: {compliance_task_id} for content {content_task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule compliance check: {e}")
    
    def get_scaling_metrics(self) -> ScalingMetrics:
        """Get current scaling performance metrics"""
        try:
            # Get queue statistics
            queue_stats = self.task_manager.get_queue_stats()
            
            # Calculate metrics
            active_channels = len(self.active_workers)
            total_workers = queue_stats.get('active_workers', 0)
            
            # Count pending tasks across all queues
            pending_tasks = sum(
                queue_info.get('pending_jobs', 0) 
                for queue_info in queue_stats.get('queues', {}).values()
            )
            
            # Calculate recent performance
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            # Tasks completed in last hour (simulated for now)
            tasks_completed_last_hour = len([t for t in self.task_completion_times 
                                           if t > time.time() - 3600])
            
            # Average task duration
            recent_completion_times = self.task_completion_times[-100:]  # Last 100 tasks
            avg_duration = sum(recent_completion_times) / len(recent_completion_times) if recent_completion_times else 0
            
            # Compliance pass rate
            recent_compliance = self.compliance_results[-100:]  # Last 100 checks
            compliance_pass_rate = (sum(recent_compliance) / len(recent_compliance) * 100) if recent_compliance else 100
            
            # Error rate (simplified calculation)
            error_rate = max(0, 10 - compliance_pass_rate * 0.1)  # Inverse relationship
            
            # Throughput calculation
            throughput = tasks_completed_last_hour
            
            metrics = ScalingMetrics(
                active_channels=active_channels,
                total_workers=total_workers,
                tasks_pending=pending_tasks,
                tasks_completed_last_hour=tasks_completed_last_hour,
                average_task_duration=avg_duration,
                compliance_pass_rate=compliance_pass_rate,
                error_rate=error_rate,
                throughput_per_hour=throughput
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:  # Keep last 1000 entries
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate scaling metrics: {e}")
            return ScalingMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    def optimize_worker_allocation(self) -> Dict[str, Any]:
        """Optimize worker allocation based on performance metrics"""
        logger.info("🔧 Optimizing worker allocation...")
        
        optimization_result = {
            'changes_made': [],
            'performance_improvement': 0,
            'cost_savings': 0
        }
        
        try:
            current_metrics = self.get_scaling_metrics()
            
            # Identify underperforming channels
            for channel_id, workers in self.active_workers.items():
                allocation = self.worker_allocations.get(channel_id)
                if not allocation:
                    continue
                
                # Check if channel needs more or fewer workers
                # (Simplified logic - in production would be more sophisticated)
                
                # If pending tasks are high and workers are at capacity, scale up
                if (current_metrics.tasks_pending > 50 and 
                    allocation.worker_count < self.max_workers_per_channel):
                    
                    # Add one more worker
                    worker_name = f"{channel_id}_worker_{allocation.worker_count + 1}"
                    worker_id = self.task_manager.start_worker(
                        queues=allocation.queue_names,
                        worker_name=worker_name
                    )
                    
                    self.active_workers[channel_id].append(worker_id)
                    allocation.worker_count += 1
                    
                    optimization_result['changes_made'].append({
                        'channel': channel_id,
                        'action': 'scale_up',
                        'new_worker_count': allocation.worker_count
                    })
                    
                    logger.info(f"📈 Scaled up {channel_id}: +1 worker (total: {allocation.worker_count})")
                
                # If throughput is low and we have multiple workers, consider scaling down
                elif (current_metrics.throughput_per_hour < 10 and 
                      allocation.worker_count > 1):
                    
                    # This would require more complex worker shutdown logic
                    # For now, just log the recommendation
                    logger.info(f"💡 Recommendation: Consider scaling down {channel_id}")
                    
                    optimization_result['changes_made'].append({
                        'channel': channel_id,
                        'action': 'scale_down_recommended',
                        'current_worker_count': allocation.worker_count
                    })
            
        except Exception as e:
            logger.error(f"❌ Worker optimization failed: {e}")
            optimization_result['error'] = str(e)
        
        return optimization_result
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitor_performance():
            while not self.shutdown_event.is_set():
                try:
                    # Collect metrics
                    metrics = self.get_scaling_metrics()
                    
                    # Log periodic status
                    if len(self.metrics_history) % 12 == 0:  # Every 12 intervals (1 hour if 5min intervals)
                        logger.info(f"📊 Scaling Status - Channels: {metrics.active_channels}, "
                                   f"Workers: {metrics.total_workers}, "
                                   f"Throughput: {metrics.throughput_per_hour}/hr, "
                                   f"Compliance: {metrics.compliance_pass_rate:.1f}%")
                    
                    # Auto-optimize if performance degrades
                    if (metrics.error_rate > 15 or 
                        metrics.compliance_pass_rate < 80 or
                        metrics.tasks_pending > 100):
                        self.optimize_worker_allocation()
                    
                except Exception as e:
                    logger.error(f"❌ Monitoring error: {e}")
                
                # Sleep for 5 minutes
                self.shutdown_event.wait(300)
        
        monitor_thread = threading.Thread(target=monitor_performance, name="scaling_monitor")
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("📡 Started scaling monitoring thread")
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information for free tier services"""
        return {
            'replit_deployment': {
                'workers_per_repl': 2,
                'max_free_repls': 3,
                'total_worker_capacity': 6,
                'deployment_command': 'python core/scaling_orchestrator.py',
                'environment_variables': [
                    'REDIS_URL',
                    'UPSTASH_REDIS_REST_URL',
                    'UPSTASH_REDIS_REST_TOKEN',
                    'OPENAI_API_KEY'
                ]
            },
            'render_deployment': {
                'free_dyno_hours': 750,  # Per month
                'workers_per_dyno': 1,
                'auto_scaling': True,
                'deployment_file': 'render.yaml',
                'estimated_monthly_capacity': '1000-2000 tasks'
            },
            'upstash_redis': {
                'free_tier_limit': '10MB storage',
                'max_connections': 30,
                'suitable_for': 'Up to 10 channels with light queuing',
                'upgrade_threshold': '50+ tasks/hour sustained'
            },
            'scaling_recommendations': {
                'start_small': '1-2 channels, 2-3 workers total',
                'monitor_metrics': 'Watch compliance rate and throughput',
                'scale_gradually': 'Add workers when consistently >80% utilization',
                'upgrade_path': 'Paid Redis → Dedicated servers → Cloud orchestration'
            }
        }
    
    def create_migration_roadmap(self) -> Dict[str, Any]:
        """Create roadmap for migrating to paid tiers"""
        return {
            'phase_1_free_tier': {
                'description': 'Bootstrap with free services',
                'duration': '1-3 months',
                'services': [
                    'Upstash Redis (10MB free)',
                    'Replit hosting (3 free repls)',
                    'Render workers (750 hours/month)',
                    'OpenAI API (pay-per-use)'
                ],
                'capacity': '5-10 channels, 50-100 videos/month',
                'estimated_cost': '$20-50/month (API costs only)',
                'migration_trigger': '$500+/month revenue OR 100+ videos/month'
            },
            'phase_2_scaling': {
                'description': 'Upgrade to paid tiers',
                'duration': '3-6 months',
                'services': [
                    'Upstash Redis Pro ($10/month)',
                    'Dedicated VPS ($20-50/month)',
                    'Redis Cloud or AWS ElastiCache',
                    'Load balancer for workers'
                ],
                'capacity': '20-50 channels, 500+ videos/month',
                'estimated_cost': '$100-300/month',
                'migration_trigger': '$2000+/month revenue OR 500+ videos/month'
            },
            'phase_3_enterprise': {
                'description': 'Full cloud infrastructure',
                'duration': '6+ months',
                'services': [
                    'AWS/GCP managed Redis',
                    'Kubernetes orchestration',
                    'Auto-scaling worker pods',
                    'Dedicated compliance services',
                    'Multi-region deployment'
                ],
                'capacity': '100+ channels, 2000+ videos/month',
                'estimated_cost': '$500-2000/month',
                'migration_trigger': '$10000+/month revenue'
            },
            'migration_automation': {
                'config_migration': 'Automated YAML config transfer',
                'data_migration': 'Redis backup/restore scripts',
                'worker_migration': 'Rolling deployment with zero downtime',
                'monitoring_migration': 'Metrics and alerting transfer'
            }
        }
    
    def shutdown(self):
        """Shutdown the scaling orchestrator and all workers"""
        logger.info("🛑 Shutting down scaling orchestrator...")
        
        self.shutdown_event.set()
        
        # Shutdown task manager (which shuts down workers)
        self.task_manager.shutdown()
        
        # Clear state
        self.active_workers.clear()
        self.worker_allocations.clear()
        
        logger.info("✅ Scaling orchestrator shut down")


# Example usage and testing
if __name__ == "__main__":
    # Initialize scaling orchestrator
    orchestrator = ScalingOrchestrator()
    
    # Scale system for moderate throughput
    scaling_result = orchestrator.scale_system(
        target_throughput=50,  # 50 tasks per hour
        optimization_strategy="balanced"
    )
    
    print("🚀 Scaling Results:")
    print(json.dumps(scaling_result, indent=2))
    
    # Wait and check metrics
    time.sleep(5)
    
    metrics = orchestrator.get_scaling_metrics()
    print(f"\n📊 Current Metrics:")
    print(f"   Active Channels: {metrics.active_channels}")
    print(f"   Total Workers: {metrics.total_workers}")
    print(f"   Tasks Pending: {metrics.tasks_pending}")
    print(f"   Throughput: {metrics.throughput_per_hour}/hour")
    
    # Show deployment info
    deployment_info = orchestrator.get_deployment_info()
    print(f"\n🚀 Deployment Options:")
    print(f"   Replit Capacity: {deployment_info['replit_deployment']['total_worker_capacity']} workers")
    print(f"   Render Free Hours: {deployment_info['render_deployment']['free_dyno_hours']}/month")
    
    # Show migration roadmap
    roadmap = orchestrator.create_migration_roadmap()
    print(f"\n🗺️  Migration Roadmap:")
    for phase, details in roadmap.items():
        if phase.startswith('phase_'):
            print(f"   {phase}: {details['estimated_cost']} - {details['capacity']}")
    
    # Shutdown after testing
    time.sleep(10)
    orchestrator.shutdown()
