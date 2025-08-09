#!/usr/bin/env python3
"""
🎛️ MULTI-CHANNEL CONFIGURATION MANAGER 🎛️
Advanced per-channel configuration system with dynamic loading and validation.

Manages individual channel configurations with platform-specific settings,
content optimization, compliance rules, and scaling parameters.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChannelConfig:
    """Complete channel configuration"""
    channel_id: str
    channel_name: str
    platform: Dict[str, Any]
    content: Dict[str, Any]
    seo: Dict[str, Any]
    monetization: Dict[str, Any]
    compliance: Dict[str, Any]
    analytics: Dict[str, Any]
    scaling: Dict[str, Any]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration integrity"""
        required_fields = ['channel_id', 'channel_name', 'platform', 'content']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required field '{field}' is missing or empty")
        
        # Validate platform configurations
        if not self.platform:
            raise ValueError("At least one platform must be configured")
        
        for platform_name, platform_config in self.platform.items():
            if not platform_config.get('enabled', False):
                continue
            
            # Validate required platform fields
            if platform_name == 'youtube' and not platform_config.get('channel_id'):
                logger.warning(f"YouTube channel_id missing for {self.channel_id}")
            elif platform_name == 'tiktok' and not platform_config.get('username'):
                logger.warning(f"TikTok username missing for {self.channel_id}")

@dataclass
class PlatformSettings:
    """Platform-specific settings"""
    enabled: bool
    upload_defaults: Dict[str, Any]
    scheduling: Dict[str, Any]
    api_config: Optional[Dict[str, Any]] = None
    custom_settings: Optional[Dict[str, Any]] = None

class ChannelConfigManager:
    """
    🎛️ MULTI-CHANNEL CONFIGURATION MANAGER 🎛️
    
    Manages configuration for multiple channels with platform-specific
    optimization, compliance rules, and scaling parameters.
    """
    
    def __init__(self, config_directory: str = "channels"):
        """
        Initialize the configuration manager
        
        Args:
            config_directory: Directory containing channel config files
        """
        self.config_directory = Path(config_directory)
        self.channels: Dict[str, ChannelConfig] = {}
        self.config_cache: Dict[str, tuple] = {}  # (config, hash, timestamp)
        self.cache_duration = 300  # 5 minutes
        
        # Ensure config directory exists
        self.config_directory.mkdir(exist_ok=True)
        
        # Load all configurations
        self.load_all_configurations()
        
        logger.info(f"🎛️ Channel Config Manager initialized with {len(self.channels)} channels")
    
    def load_all_configurations(self):
        """Load all channel configurations from the config directory"""
        config_files = list(self.config_directory.glob("*.yaml")) + list(self.config_directory.glob("*.yml"))
        
        for config_file in config_files:
            try:
                channel_id = config_file.stem
                config = self.load_channel_config(channel_id)
                if config:
                    self.channels[channel_id] = config
                    logger.info(f"✅ Loaded configuration for channel: {channel_id}")
            except Exception as e:
                logger.error(f"❌ Failed to load configuration for {config_file}: {e}")
    
    def load_channel_config(self, channel_id: str) -> Optional[ChannelConfig]:
        """
        Load configuration for a specific channel
        
        Args:
            channel_id: Unique identifier for the channel
            
        Returns:
            ChannelConfig object or None if not found/invalid
        """
        config_file = self.config_directory / f"{channel_id}.yaml"
        if not config_file.exists():
            config_file = self.config_directory / f"{channel_id}.yml"
        
        if not config_file.exists():
            logger.warning(f"Configuration file not found for channel: {channel_id}")
            return None
        
        # Check cache
        file_hash = self._calculate_file_hash(config_file)
        if channel_id in self.config_cache:
            cached_config, cached_hash, timestamp = self.config_cache[channel_id]
            if (cached_hash == file_hash and 
                datetime.now().timestamp() - timestamp < self.cache_duration):
                return cached_config
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Create configuration object
            config = ChannelConfig(
                channel_id=config_data.get('channel_id', channel_id),
                channel_name=config_data.get('channel_name', f"Channel {channel_id}"),
                platform=config_data.get('platform', {}),
                content=config_data.get('content', {}),
                seo=config_data.get('seo', {}),
                monetization=config_data.get('monetization', {}),
                compliance=config_data.get('compliance', {}),
                analytics=config_data.get('analytics', {}),
                scaling=config_data.get('scaling', {})
            )
            
            # Update cache
            self.config_cache[channel_id] = (config, file_hash, datetime.now().timestamp())
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration for {channel_id}: {e}")
            return None
    
    def get_channel_config(self, channel_id: str) -> Optional[ChannelConfig]:
        """Get configuration for a specific channel"""
        if channel_id in self.channels:
            # Check if we need to reload
            config_file = self.config_directory / f"{channel_id}.yaml"
            if not config_file.exists():
                config_file = self.config_directory / f"{channel_id}.yml"
            
            if config_file.exists():
                current_hash = self._calculate_file_hash(config_file)
                if channel_id in self.config_cache:
                    _, cached_hash, _ = self.config_cache[channel_id]
                    if current_hash != cached_hash:
                        # Reload configuration
                        updated_config = self.load_channel_config(channel_id)
                        if updated_config:
                            self.channels[channel_id] = updated_config
                            return updated_config
            
            return self.channels[channel_id]
        
        # Try to load if not in memory
        config = self.load_channel_config(channel_id)
        if config:
            self.channels[channel_id] = config
        return config
    
    def get_all_channels(self) -> Dict[str, ChannelConfig]:
        """Get all loaded channel configurations"""
        return self.channels.copy()
    
    def get_channels_by_platform(self, platform: str) -> Dict[str, ChannelConfig]:
        """Get all channels that have a specific platform enabled"""
        filtered_channels = {}
        for channel_id, config in self.channels.items():
            if (platform in config.platform and 
                config.platform[platform].get('enabled', False)):
                filtered_channels[channel_id] = config
        return filtered_channels
    
    def get_platform_settings(self, channel_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Get platform-specific settings for a channel"""
        config = self.get_channel_config(channel_id)
        if not config:
            return None
        
        return config.platform.get(platform, {})
    
    def get_upload_defaults(self, channel_id: str, platform: str) -> Dict[str, Any]:
        """Get upload defaults for a specific channel and platform"""
        platform_settings = self.get_platform_settings(channel_id, platform)
        if not platform_settings:
            return {}
        
        return platform_settings.get('upload_defaults', {})
    
    def get_scheduling_config(self, channel_id: str, platform: str) -> Dict[str, Any]:
        """Get scheduling configuration for a channel and platform"""
        platform_settings = self.get_platform_settings(channel_id, platform)
        if not platform_settings:
            return {}
        
        return platform_settings.get('scheduling', {})
    
    def get_content_specs(self, channel_id: str, platform: str = None) -> Dict[str, Any]:
        """Get content specifications for a channel"""
        config = self.get_channel_config(channel_id)
        if not config:
            return {}
        
        content_config = config.content
        if platform and 'video_specs' in content_config:
            return content_config['video_specs'].get(platform, {})
        
        return content_config
    
    def get_seo_config(self, channel_id: str, platform: str = None) -> Dict[str, Any]:
        """Get SEO configuration for a channel"""
        config = self.get_channel_config(channel_id)
        if not config:
            return {}
        
        seo_config = config.seo
        if platform and 'hashtags' in seo_config:
            hashtags = seo_config['hashtags'].get(platform, [])
            return {**seo_config, 'platform_hashtags': hashtags}
        
        return seo_config
    
    def get_compliance_rules(self, channel_id: str) -> Dict[str, Any]:
        """Get compliance rules for a channel"""
        config = self.get_channel_config(channel_id)
        if not config:
            return {}
        
        return config.compliance
    
    def get_scaling_config(self, channel_id: str) -> Dict[str, Any]:
        """Get scaling configuration for a channel"""
        config = self.get_channel_config(channel_id)
        if not config:
            return {}
        
        return config.scaling
    
    def validate_channel_config(self, channel_id: str) -> Dict[str, List[str]]:
        """
        Validate a channel configuration and return any issues
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        config = self.get_channel_config(channel_id)
        if not config:
            return {'errors': ['Configuration not found'], 'warnings': []}
        
        errors = []
        warnings = []
        
        # Check platform configurations
        enabled_platforms = [p for p, c in config.platform.items() if c.get('enabled', False)]
        if not enabled_platforms:
            errors.append("No platforms are enabled")
        
        # Check content configuration
        if not config.content.get('niche'):
            warnings.append("No content niche specified")
        
        if not config.content.get('target_audience'):
            warnings.append("No target audience specified")
        
        # Check compliance rules
        if not config.compliance.get('content_policy', {}).get('copyright_check', False):
            warnings.append("Copyright checking is disabled")
        
        return {'errors': errors, 'warnings': warnings}
    
    def create_channel_template(self, channel_id: str, platform: str, niche: str = "general") -> str:
        """Create a configuration template for a new channel"""
        template_data = {
            'channel_id': channel_id,
            'channel_name': f"Channel {channel_id.title()}",
            'platform': {
                platform: {
                    'enabled': True,
                    'upload_defaults': {
                        'privacy': 'public',
                        'language': 'en'
                    },
                    'scheduling': {
                        'upload_time': '10:00',
                        'frequency': 'daily',
                        'max_uploads_per_day': 1
                    }
                }
            },
            'content': {
                'niche': niche,
                'target_audience': 'general',
                'content_types': ['educational', 'entertainment']
            },
            'seo': {
                'keywords': {
                    'primary': [niche],
                    'secondary': ['content', 'videos']
                },
                'hashtags': {
                    platform: [f'#{niche}', '#content']
                }
            },
            'compliance': {
                'content_policy': {
                    'copyright_check': True,
                    'profanity_filter': True,
                    'coppa_compliant': True,
                    'advertiser_friendly': True
                },
                'safety_checks': [
                    'copyright_detection',
                    'profanity_check'
                ]
            },
            'scaling': {
                'worker_config': {
                    'max_concurrent_uploads': 1,
                    'queue_priority': 'medium',
                    'retry_attempts': 2,
                    'timeout': 300
                }
            }
        }
        
        template_file = self.config_directory / f"{channel_id}.yaml"
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(template_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"✅ Created configuration template: {template_file}")
        return str(template_file)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file for caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def reload_configurations(self):
        """Reload all configurations from disk"""
        logger.info("🔄 Reloading all channel configurations...")
        self.channels.clear()
        self.config_cache.clear()
        self.load_all_configurations()
        logger.info(f"✅ Reloaded {len(self.channels)} channel configurations")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about loaded channels"""
        total_channels = len(self.channels)
        platforms_count = {}
        niches_count = {}
        
        for config in self.channels.values():
            # Count platforms
            for platform, settings in config.platform.items():
                if settings.get('enabled', False):
                    platforms_count[platform] = platforms_count.get(platform, 0) + 1
            
            # Count niches
            niche = config.content.get('niche', 'unknown')
            niches_count[niche] = niches_count.get(niche, 0) + 1
        
        return {
            'total_channels': total_channels,
            'platforms': platforms_count,
            'niches': niches_count,
            'config_directory': str(self.config_directory)
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize configuration manager
    config_manager = ChannelConfigManager()
    
    # Display summary
    stats = config_manager.get_summary_stats()
    print(f"📊 Channel Configuration Summary:")
    print(f"   Total Channels: {stats['total_channels']}")
    print(f"   Platforms: {stats['platforms']}")
    print(f"   Niches: {stats['niches']}")
    
    # Test loading specific channel
    if stats['total_channels'] > 0:
        channel_ids = list(config_manager.get_all_channels().keys())
        test_channel = channel_ids[0]
        
        print(f"\n🔍 Testing channel: {test_channel}")
        
        # Get platform settings
        youtube_settings = config_manager.get_platform_settings(test_channel, 'youtube')
        if youtube_settings:
            print(f"   YouTube enabled: {youtube_settings.get('enabled', False)}")
        
        # Get content specs
        content_specs = config_manager.get_content_specs(test_channel)
        print(f"   Niche: {content_specs.get('niche', 'Not specified')}")
        
        # Validate configuration
        validation_result = config_manager.validate_channel_config(test_channel)
        print(f"   Validation: {len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings")
