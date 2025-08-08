#!/usr/bin/env python3
"""
🧠 PSYCHOLOGICAL OPTIMIZATION ENGINE 🧠
Advanced Viewer Psychology & Manipulation System

This system uses neuroscience, behavioral psychology, and data analysis
to create addictive content that maximizes viewer engagement and retention.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import sqlite3
import re
import logging
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import random
import time
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ViewerProfile:
    """Individual viewer psychological profile"""
    viewer_id: str
    demographics: Dict[str, Any]
    behavioral_patterns: Dict[str, float]
    psychological_triggers: List[str]
    attention_span: float
    addiction_susceptibility: float
    engagement_history: List[Dict[str, Any]]
    optimal_content_length: Tuple[int, int]
    peak_viewing_times: List[int]
    emotional_preferences: Dict[str, float]
    retention_patterns: Dict[str, float]
    conversion_likelihood: float

@dataclass
class PsychologicalStrategy:
    """Psychological manipulation strategy"""
    strategy_id: str
    name: str
    trigger_type: str
    effectiveness_score: float
    target_emotions: List[str]
    implementation_method: str
    optimal_timing: List[float]  # Percentage through video
    success_rate: float
    psychological_principle: str

class PsychologicalOptimizer:
    """
    🎭 ADVANCED PSYCHOLOGICAL MANIPULATION ENGINE 🎭
    
    Uses cutting-edge neuroscience and behavioral psychology to create
    content that hijacks viewer attention and creates addiction patterns.
    """
    
    def __init__(self, db_path: str = "psychological_engine.db"):
        self.db_path = db_path
        self.viewer_profiles = {}
        self.psychological_strategies = self._load_psychological_strategies()
        self.addiction_patterns = self._load_addiction_patterns()
        self.neural_triggers = self._load_neural_triggers()
        self.dopamine_schedules = {}
        
        # Initialize database
        self._initialize_database()
        
        # Load pre-trained models
        self._load_behavioral_models()
        
        logger.info("🧠 Psychological Optimizer initialized")
    
    def _initialize_database(self):
        """Initialize psychological analysis database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Viewer profiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS viewer_profiles (
            viewer_id TEXT PRIMARY KEY,
            demographics TEXT,
            behavioral_patterns TEXT,
            psychological_triggers TEXT,
            attention_span REAL,
            addiction_susceptibility REAL,
            optimal_content_length TEXT,
            emotional_preferences TEXT,
            last_updated TEXT
        )
        ''')
        
        # Engagement analytics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS engagement_analytics (
            session_id TEXT PRIMARY KEY,
            viewer_id TEXT,
            content_id TEXT,
            watch_time REAL,
            engagement_score REAL,
            psychological_triggers_used TEXT,
            effectiveness_score REAL,
            timestamp TEXT
        )
        ''')
        
        # A/B testing results
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS psychological_testing (
            test_id TEXT PRIMARY KEY,
            strategy_type TEXT,
            control_group_performance REAL,
            test_group_performance REAL,
            improvement_percentage REAL,
            confidence_level REAL,
            test_date TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Psychological database initialized")
    
    def _load_psychological_strategies(self) -> Dict[str, PsychologicalStrategy]:
        """Load advanced psychological manipulation strategies"""
        strategies = {}
        
        # Dopamine Optimization Strategy
        strategies["dopamine_peaks"] = PsychologicalStrategy(
            strategy_id="dopamine_peaks",
            name="Dopamine Peak Optimization",
            trigger_type="neurochemical",
            effectiveness_score=0.92,
            target_emotions=["excitement", "anticipation", "reward"],
            implementation_method="Variable reward timing with peak scheduling",
            optimal_timing=[0.05, 0.15, 0.35, 0.55, 0.75, 0.90],
            success_rate=0.89,
            psychological_principle="Variable ratio reinforcement creates addiction"
        )
        
        # Attention Hijacking Strategy
        strategies["attention_hijack"] = PsychologicalStrategy(
            strategy_id="attention_hijack",
            name="Attention Hijacking Protocol",
            trigger_type="cognitive",
            effectiveness_score=0.88,
            target_emotions=["curiosity", "urgency", "fear"],
            implementation_method="Pattern interrupts and attention grabbers",
            optimal_timing=[0.0, 0.12, 0.25, 0.40, 0.65, 0.85],
            success_rate=0.85,
            psychological_principle="Attention is finite resource - hijack before competitors"
        )
        
        # Social Proof Amplification
        strategies["social_proof"] = PsychologicalStrategy(
            strategy_id="social_proof",
            name="Social Proof Amplification",
            trigger_type="social",
            effectiveness_score=0.86,
            target_emotions=["belonging", "validation", "trust"],
            implementation_method="Highlight popularity and social acceptance",
            optimal_timing=[0.10, 0.30, 0.70],
            success_rate=0.83,
            psychological_principle="People follow crowd behavior - amplify social signals"
        )
        
        # Fear of Missing Out (FOMO)
        strategies["fomo_creation"] = PsychologicalStrategy(
            strategy_id="fomo_creation",
            name="FOMO Creation Engine",
            trigger_type="emotional",
            effectiveness_score=0.91,
            target_emotions=["anxiety", "urgency", "regret_avoidance"],
            implementation_method="Scarcity language and time pressure",
            optimal_timing=[0.05, 0.45, 0.95],
            success_rate=0.87,
            psychological_principle="Loss aversion stronger than gain motivation"
        )
        
        # Identity Reinforcement
        strategies["identity_mirror"] = PsychologicalStrategy(
            strategy_id="identity_mirror",
            name="Identity Mirroring System",
            trigger_type="identity",
            effectiveness_score=0.84,
            target_emotions=["pride", "belonging", "self_worth"],
            implementation_method="Mirror viewer's self-concept and values",
            optimal_timing=[0.20, 0.60],
            success_rate=0.81,
            psychological_principle="People engage with content that reflects their identity"
        )
        
        # Curiosity Gap Exploitation
        strategies["curiosity_gaps"] = PsychologicalStrategy(
            strategy_id="curiosity_gaps",
            name="Curiosity Gap Engineering",
            trigger_type="cognitive",
            effectiveness_score=0.90,
            target_emotions=["curiosity", "anticipation", "completion_drive"],
            implementation_method="Create information gaps requiring resolution",
            optimal_timing=[0.08, 0.28, 0.48, 0.68, 0.88],
            success_rate=0.86,
            psychological_principle="Open loops in mind demand closure"
        )
        
        return strategies
    
    def _load_addiction_patterns(self) -> Dict[str, Any]:
        """Load psychological addiction patterns"""
        return {
            "variable_ratio_schedule": {
                "description": "Unpredictable rewards create strongest addiction",
                "implementation": "Random timing of high-value content",
                "effectiveness": 0.94,
                "addiction_potential": 0.92
            },
            "escalating_commitment": {
                "description": "Small initial commitments lead to larger ones",
                "implementation": "Start with small asks, gradually increase",
                "effectiveness": 0.87,
                "addiction_potential": 0.85
            },
            "sunk_cost_fallacy": {
                "description": "Time invested creates commitment to continue",
                "implementation": "Acknowledge time viewer has already spent",
                "effectiveness": 0.82,
                "addiction_potential": 0.78
            },
            "intermittent_reinforcement": {
                "description": "Irregular rewards maintain engagement longer",
                "implementation": "Mix valuable and less valuable content unpredictably",
                "effectiveness": 0.89,
                "addiction_potential": 0.88
            },
            "near_miss_effect": {
                "description": "Almost achieving goal increases motivation",
                "implementation": "Show progress toward goal without completion",
                "effectiveness": 0.85,
                "addiction_potential": 0.83
            }
        }
    
    def _load_neural_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Load neuroscience-based triggers"""
        return {
            "dopamine_triggers": {
                "unexpected_rewards": {"timing": "random", "intensity": 0.9},
                "progress_indicators": {"timing": "regular", "intensity": 0.7},
                "achievement_unlocks": {"timing": "milestone", "intensity": 0.8},
                "social_recognition": {"timing": "contextual", "intensity": 0.85}
            },
            "serotonin_triggers": {
                "belonging_signals": {"timing": "early", "intensity": 0.8},
                "status_elevation": {"timing": "middle", "intensity": 0.75},
                "gratitude_expression": {"timing": "late", "intensity": 0.7},
                "community_connection": {"timing": "throughout", "intensity": 0.8}
            },
            "norepinephrine_triggers": {
                "urgency_creation": {"timing": "peaks", "intensity": 0.9},
                "challenge_presentation": {"timing": "early", "intensity": 0.8},
                "competition_element": {"timing": "middle", "intensity": 0.85},
                "deadline_pressure": {"timing": "late", "intensity": 0.9}
            },
            "oxytocin_triggers": {
                "personal_stories": {"timing": "early", "intensity": 0.8},
                "vulnerability_sharing": {"timing": "middle", "intensity": 0.85},
                "mutual_understanding": {"timing": "throughout", "intensity": 0.75},
                "collective_identity": {"timing": "late", "intensity": 0.8}
            }
        }
    
    def _load_behavioral_models(self):
        """Load pre-trained behavioral analysis models"""
        # This would load actual ML models in production
        # For now, creating structured behavioral analysis
        
        self.behavioral_segments = {
            "dopamine_seekers": {
                "characteristics": ["high novelty seeking", "reward sensitive", "impulsive"],
                "optimal_strategies": ["dopamine_peaks", "curiosity_gaps"],
                "content_preferences": ["fast-paced", "surprising", "rewarding"],
                "attention_span": (30, 180),  # seconds
                "addiction_susceptibility": 0.85
            },
            "social_validators": {
                "characteristics": ["peer influenced", "status conscious", "community oriented"],
                "optimal_strategies": ["social_proof", "identity_mirror"],
                "content_preferences": ["trending", "popular", "community-focused"],
                "attention_span": (60, 300),
                "addiction_susceptibility": 0.78
            },
            "fear_motivated": {
                "characteristics": ["loss averse", "security seeking", "risk aware"],
                "optimal_strategies": ["fomo_creation", "attention_hijack"],
                "content_preferences": ["educational", "problem-solving", "protective"],
                "attention_span": (120, 600),
                "addiction_susceptibility": 0.82
            },
            "achievement_oriented": {
                "characteristics": ["goal focused", "improvement seeking", "competitive"],
                "optimal_strategies": ["dopamine_peaks", "identity_mirror"],
                "content_preferences": ["tutorial", "skill-building", "success-focused"],
                "attention_span": (180, 900),
                "addiction_susceptibility": 0.75
            }
        }
        
        logger.info("✅ Behavioral models loaded")
    
    async def analyze_viewer_psychology(
        self,
        viewer_data: Dict[str, Any],
        viewing_history: List[Dict[str, Any]]
    ) -> ViewerProfile:
        """Perform deep psychological analysis of individual viewer"""
        
        logger.info(f"🧠 Analyzing viewer psychology: {viewer_data.get('viewer_id', 'unknown')}")
        
        viewer_id = viewer_data.get('viewer_id', self._generate_viewer_id())
        
        # Extract behavioral patterns
        behavioral_patterns = self._extract_behavioral_patterns(viewing_history)
        
        # Identify psychological triggers
        psychological_triggers = self._identify_psychological_triggers(behavioral_patterns, viewing_history)
        
        # Calculate attention span
        attention_span = self._calculate_attention_span(viewing_history)
        
        # Assess addiction susceptibility
        addiction_susceptibility = self._assess_addiction_susceptibility(behavioral_patterns)
        
        # Determine optimal content characteristics
        optimal_length = self._determine_optimal_content_length(viewing_history)
        peak_times = self._identify_peak_viewing_times(viewing_history)
        
        # Analyze emotional preferences
        emotional_preferences = self._analyze_emotional_preferences(viewing_history)
        
        # Calculate retention patterns
        retention_patterns = self._analyze_retention_patterns(viewing_history)
        
        # Predict conversion likelihood
        conversion_likelihood = self._predict_conversion_likelihood(behavioral_patterns)
        
        # Create comprehensive profile
        profile = ViewerProfile(
            viewer_id=viewer_id,
            demographics=viewer_data.get('demographics', {}),
            behavioral_patterns=behavioral_patterns,
            psychological_triggers=psychological_triggers,
            attention_span=attention_span,
            addiction_susceptibility=addiction_susceptibility,
            engagement_history=viewing_history,
            optimal_content_length=optimal_length,
            peak_viewing_times=peak_times,
            emotional_preferences=emotional_preferences,
            retention_patterns=retention_patterns,
            conversion_likelihood=conversion_likelihood
        )
        
        # Store profile
        self._store_viewer_profile(profile)
        
        logger.info(f"✅ Viewer psychology analyzed - Susceptibility: {addiction_susceptibility:.2f}")
        return profile
    
    def _extract_behavioral_patterns(self, viewing_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract behavioral patterns from viewing history"""
        
        if not viewing_history:
            return self._default_behavioral_patterns()
        
        patterns = {}
        
        # Session patterns
        session_lengths = [v.get('watch_time', 0) for v in viewing_history]
        patterns['avg_session_length'] = np.mean(session_lengths) if session_lengths else 0
        patterns['session_consistency'] = 1 - (np.std(session_lengths) / (np.mean(session_lengths) + 1))
        
        # Engagement patterns
        engagement_scores = [v.get('engagement_score', 0) for v in viewing_history]
        patterns['avg_engagement'] = np.mean(engagement_scores) if engagement_scores else 0
        patterns['engagement_trend'] = self._calculate_trend(engagement_scores)
        
        # Content preferences
        content_types = [v.get('content_type', '') for v in viewing_history]
        patterns['content_diversity'] = len(set(content_types)) / max(len(content_types), 1)
        
        # Timing patterns
        viewing_times = [v.get('viewing_hour', 12) for v in viewing_history]
        patterns['peak_hour_consistency'] = self._calculate_peak_consistency(viewing_times)
        
        # Retention patterns
        completion_rates = [v.get('completion_rate', 0) for v in viewing_history]
        patterns['avg_completion_rate'] = np.mean(completion_rates) if completion_rates else 0
        patterns['completion_improvement'] = self._calculate_trend(completion_rates)
        
        # Binge behavior
        same_day_sessions = self._count_same_day_sessions(viewing_history)
        patterns['binge_tendency'] = same_day_sessions / max(len(viewing_history), 1)
        
        # Social behavior
        social_actions = [v.get('social_actions', 0) for v in viewing_history]
        patterns['social_engagement'] = np.mean(social_actions) if social_actions else 0
        
        return patterns
    
    def _identify_psychological_triggers(
        self,
        behavioral_patterns: Dict[str, float],
        viewing_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify most effective psychological triggers for viewer"""
        
        triggers = []
        
        # Dopamine seekers
        if (behavioral_patterns.get('avg_engagement', 0) > 0.7 and 
            behavioral_patterns.get('content_diversity', 0) > 0.6):
            triggers.extend(['novelty_seeking', 'reward_anticipation', 'surprise_elements'])
        
        # Social validators
        if behavioral_patterns.get('social_engagement', 0) > 0.5:
            triggers.extend(['social_proof', 'peer_validation', 'status_signals'])
        
        # Binge watchers
        if behavioral_patterns.get('binge_tendency', 0) > 0.3:
            triggers.extend(['addiction_hooks', 'cliffhangers', 'series_connection'])
        
        # Achievement oriented
        if behavioral_patterns.get('completion_improvement', 0) > 0:
            triggers.extend(['progress_tracking', 'skill_development', 'mastery_goals'])
        
        # Loss averse
        if behavioral_patterns.get('avg_completion_rate', 0) > 0.8:
            triggers.extend(['fomo_triggers', 'scarcity_signals', 'deadline_pressure'])
        
        # Default triggers if none identified
        if not triggers:
            triggers = ['curiosity_gaps', 'value_promise', 'social_proof']
        
        return triggers
    
    def _calculate_attention_span(self, viewing_history: List[Dict[str, Any]]) -> float:
        """Calculate viewer's attention span in seconds"""
        
        if not viewing_history:
            return 120.0  # Default 2 minutes
        
        # Analyze dropout points
        dropout_times = []
        for view in viewing_history:
            watch_time = view.get('watch_time', 0)
            video_length = view.get('video_length', 1)
            if video_length > 0:
                completion_rate = watch_time / video_length
                if completion_rate < 1.0:  # Didn't finish
                    dropout_times.append(watch_time)
        
        if dropout_times:
            attention_span = np.percentile(dropout_times, 75)  # 75th percentile
        else:
            # Use average watch time as proxy
            watch_times = [v.get('watch_time', 0) for v in viewing_history]
            attention_span = np.mean(watch_times) if watch_times else 120.0
        
        return max(min(attention_span, 1800), 30)  # Clamp between 30s and 30min
    
    def _assess_addiction_susceptibility(self, behavioral_patterns: Dict[str, float]) -> float:
        """Assess viewer's susceptibility to content addiction"""
        
        # Factors that indicate higher addiction susceptibility
        factors = {
            'binge_tendency': behavioral_patterns.get('binge_tendency', 0) * 0.3,
            'session_consistency': behavioral_patterns.get('session_consistency', 0) * 0.2,
            'engagement_trend': max(behavioral_patterns.get('engagement_trend', 0), 0) * 0.2,
            'avg_engagement': behavioral_patterns.get('avg_engagement', 0) * 0.15,
            'completion_rate': behavioral_patterns.get('avg_completion_rate', 0) * 0.15
        }
        
        susceptibility = sum(factors.values())
        
        # Normalize to 0-1 scale
        return min(max(susceptibility, 0.1), 0.95)
    
    def _determine_optimal_content_length(
        self,
        viewing_history: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """Determine optimal content length for viewer"""
        
        if not viewing_history:
            return (180, 480)  # Default 3-8 minutes
        
        # Analyze completion rates by length
        length_performance = {}
        
        for view in viewing_history:
            length = view.get('video_length', 0)
            completion = view.get('completion_rate', 0)
            
            if length > 0:
                length_bucket = self._get_length_bucket(length)
                if length_bucket not in length_performance:
                    length_performance[length_bucket] = []
                length_performance[length_bucket].append(completion)
        
        # Find optimal length range
        best_performance = 0
        optimal_range = (180, 480)
        
        for length_range, completions in length_performance.items():
            avg_completion = np.mean(completions)
            if avg_completion > best_performance:
                best_performance = avg_completion
                optimal_range = length_range
        
        return optimal_range
    
    def _identify_peak_viewing_times(self, viewing_history: List[Dict[str, Any]]) -> List[int]:
        """Identify viewer's peak viewing hours"""
        
        if not viewing_history:
            return [19, 20, 21]  # Default evening hours
        
        viewing_hours = [v.get('viewing_hour', 12) for v in viewing_history]
        
        # Count frequency by hour
        hour_counts = {}
        for hour in viewing_hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Get top 3 hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [hour for hour, count in sorted_hours[:3]]
        
        return peak_hours if peak_hours else [19, 20, 21]
    
    def _analyze_emotional_preferences(
        self,
        viewing_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze viewer's emotional content preferences"""
        
        # Default emotional preferences
        emotions = {
            'excitement': 0.5,
            'curiosity': 0.6,
            'humor': 0.4,
            'inspiration': 0.3,
            'fear': 0.2,
            'anger': 0.1,
            'sadness': 0.1,
            'surprise': 0.7,
            'trust': 0.5,
            'anticipation': 0.8
        }
        
        # Analyze content emotional tags and engagement
        for view in viewing_history:
            content_emotions = view.get('emotional_tags', [])
            engagement = view.get('engagement_score', 0.5)
            
            for emotion in content_emotions:
                if emotion in emotions:
                    emotions[emotion] = emotions[emotion] * 0.8 + engagement * 0.2
        
        return emotions
    
    def _analyze_retention_patterns(
        self,
        viewing_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze viewer retention patterns"""
        
        patterns = {
            'hook_sensitivity': 0.5,     # How much first 15s matters
            'mid_point_drop': 0.3,       # Tendency to drop at midpoint
            'end_completion': 0.6,       # Likelihood to watch till end
            'comeback_rate': 0.4,        # Return after dropping off
            'attention_decay': 0.2       # How fast attention decays
        }
        
        if not viewing_history:
            return patterns
        
        # Analyze retention curves
        retention_curves = []
        for view in viewing_history:
            retention_data = view.get('retention_curve', [])
            if retention_data:
                retention_curves.append(retention_data)
        
        if retention_curves:
            # Average retention patterns
            avg_retention = np.mean(retention_curves, axis=0)
            
            if len(avg_retention) > 3:
                patterns['hook_sensitivity'] = 1 - avg_retention[0] if avg_retention[0] < 1 else 0.5
                patterns['mid_point_drop'] = avg_retention[len(avg_retention)//2]
                patterns['end_completion'] = avg_retention[-1]
                patterns['attention_decay'] = self._calculate_decay_rate(avg_retention)
        
        return patterns
    
    def _predict_conversion_likelihood(self, behavioral_patterns: Dict[str, float]) -> float:
        """Predict likelihood of viewer taking desired actions"""
        
        # Factors that indicate higher conversion likelihood
        factors = [
            behavioral_patterns.get('avg_engagement', 0) * 0.3,
            behavioral_patterns.get('avg_completion_rate', 0) * 0.25,
            behavioral_patterns.get('social_engagement', 0) * 0.2,
            behavioral_patterns.get('session_consistency', 0) * 0.15,
            behavioral_patterns.get('binge_tendency', 0) * 0.1
        ]
        
        conversion_score = sum(factors)
        return min(max(conversion_score, 0.05), 0.95)
    
    async def optimize_content_psychology(
        self,
        content: Dict[str, Any],
        target_profiles: List[ViewerProfile]
    ) -> Dict[str, Any]:
        """Optimize content for psychological manipulation"""
        
        logger.info("🎭 Optimizing content psychology...")
        
        if not target_profiles:
            return content
        
        # Analyze target audience psychology
        audience_analysis = self._analyze_audience_psychology(target_profiles)
        
        # Select optimal strategies
        optimal_strategies = self._select_optimal_strategies(audience_analysis)
        
        # Apply psychological optimization
        optimized_content = await self._apply_psychological_optimization(
            content, optimal_strategies, audience_analysis
        )
        
        # Calculate psychological effectiveness
        effectiveness_score = self._calculate_psychological_effectiveness(
            optimized_content, audience_analysis
        )
        
        optimized_content['psychological_optimization'] = {
            'strategies_applied': [s.name for s in optimal_strategies],
            'effectiveness_score': effectiveness_score,
            'target_emotions': audience_analysis['dominant_emotions'],
            'manipulation_intensity': audience_analysis['avg_susceptibility']
        }
        
        logger.info(f"✅ Content psychology optimized - Score: {effectiveness_score:.2f}")
        return optimized_content
    
    def _analyze_audience_psychology(self, profiles: List[ViewerProfile]) -> Dict[str, Any]:
        """Analyze collective audience psychology"""
        
        analysis = {
            'avg_attention_span': np.mean([p.attention_span for p in profiles]),
            'avg_susceptibility': np.mean([p.addiction_susceptibility for p in profiles]),
            'dominant_triggers': self._find_dominant_triggers(profiles),
            'dominant_emotions': self._find_dominant_emotions(profiles),
            'optimal_length_range': self._find_optimal_length_range(profiles),
            'peak_viewing_times': self._find_common_peak_times(profiles),
            'behavioral_segments': self._segment_audience(profiles)
        }
        
        return analysis
    
    def _find_dominant_triggers(self, profiles: List[ViewerProfile]) -> List[str]:
        """Find most common psychological triggers"""
        
        trigger_counts = {}
        for profile in profiles:
            for trigger in profile.psychological_triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        # Get top triggers
        sorted_triggers = sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)
        return [trigger for trigger, count in sorted_triggers[:5]]
    
    def _find_dominant_emotions(self, profiles: List[ViewerProfile]) -> List[str]:
        """Find most preferred emotions across audience"""
        
        emotion_scores = {}
        for profile in profiles:
            for emotion, score in profile.emotional_preferences.items():
                if emotion not in emotion_scores:
                    emotion_scores[emotion] = []
                emotion_scores[emotion].append(score)
        
        # Average scores and rank
        avg_emotions = {emotion: np.mean(scores) for emotion, scores in emotion_scores.items()}
        sorted_emotions = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)
        
        return [emotion for emotion, score in sorted_emotions[:3]]
    
    def _select_optimal_strategies(
        self,
        audience_analysis: Dict[str, Any]
    ) -> List[PsychologicalStrategy]:
        """Select most effective psychological strategies"""
        
        dominant_triggers = audience_analysis.get('dominant_triggers', [])
        avg_susceptibility = audience_analysis.get('avg_susceptibility', 0.5)
        
        selected_strategies = []
        
        # High susceptibility audience - use stronger strategies
        if avg_susceptibility > 0.7:
            selected_strategies.extend([
                self.psychological_strategies['dopamine_peaks'],
                self.psychological_strategies['fomo_creation'],
                self.psychological_strategies['attention_hijack']
            ])
        
        # Medium susceptibility - balanced approach
        elif avg_susceptibility > 0.4:
            selected_strategies.extend([
                self.psychological_strategies['curiosity_gaps'],
                self.psychological_strategies['social_proof'],
                self.psychological_strategies['dopamine_peaks']
            ])
        
        # Lower susceptibility - gentle persuasion
        else:
            selected_strategies.extend([
                self.psychological_strategies['social_proof'],
                self.psychological_strategies['identity_mirror'],
                self.psychological_strategies['curiosity_gaps']
            ])
        
        # Add trigger-specific strategies
        for trigger in dominant_triggers:
            if 'social' in trigger.lower() and 'social_proof' not in [s.strategy_id for s in selected_strategies]:
                selected_strategies.append(self.psychological_strategies['social_proof'])
            elif 'novelty' in trigger.lower():
                selected_strategies.append(self.psychological_strategies['attention_hijack'])
        
        return selected_strategies[:4]  # Limit to top 4 strategies
    
    async def _apply_psychological_optimization(
        self,
        content: Dict[str, Any],
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply psychological optimization to content"""
        
        optimized_content = content.copy()
        
        # Optimize title
        optimized_content['title'] = self._optimize_title_psychology(
            content.get('title', ''), strategies, audience_analysis
        )
        
        # Optimize description
        optimized_content['description'] = self._optimize_description_psychology(
            content.get('description', ''), strategies, audience_analysis
        )
        
        # Optimize script structure
        optimized_content['script'] = await self._optimize_script_psychology(
            content.get('script', ''), strategies, audience_analysis
        )
        
        # Create dopamine schedule
        optimized_content['dopamine_schedule'] = self._create_dopamine_schedule(
            strategies, audience_analysis
        )
        
        # Add psychological timing cues
        optimized_content['psychological_cues'] = self._generate_psychological_cues(
            strategies, audience_analysis
        )
        
        # Add retention hooks
        optimized_content['retention_hooks'] = self._generate_retention_hooks(
            strategies, audience_analysis
        )
        
        return optimized_content
    
    def _optimize_title_psychology(
        self,
        title: str,
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> str:
        """Optimize title with psychological triggers"""
        
        optimized_title = title
        
        # Apply strategy-specific optimizations
        for strategy in strategies:
            if strategy.strategy_id == 'curiosity_gaps':
                optimized_title = self._add_curiosity_elements(optimized_title)
            elif strategy.strategy_id == 'fomo_creation':
                optimized_title = self._add_urgency_elements(optimized_title)
            elif strategy.strategy_id == 'social_proof':
                optimized_title = self._add_social_elements(optimized_title)
            elif strategy.strategy_id == 'dopamine_peaks':
                optimized_title = self._add_reward_elements(optimized_title)
        
        return optimized_title
    
    def _add_curiosity_elements(self, title: str) -> str:
        """Add curiosity gap elements to title"""
        
        curiosity_prefixes = [
            "The Secret Behind", "What Nobody Tells You About", "The Hidden Truth About",
            "Why Everyone's Wrong About", "The Real Reason", "What Happens When"
        ]
        
        curiosity_suffixes = [
            "(You Won't Believe What Happened)", "(The Answer Will Shock You)",
            "(This Changes Everything)", "(Mind-Blowing Results)"
        ]
        
        # Add prefix if title doesn't already have curiosity elements
        if not any(prefix.lower() in title.lower() for prefix in curiosity_prefixes):
            if len(title) < 45:  # Only if there's room
                prefix = random.choice(curiosity_prefixes)
                title = f"{prefix} {title}"
        
        return title
    
    def _add_urgency_elements(self, title: str) -> str:
        """Add urgency/FOMO elements to title"""
        
        urgency_words = ["NOW", "TODAY", "URGENT", "LAST CHANCE", "LIMITED TIME"]
        
        # Check if urgency already exists
        if not any(word in title.upper() for word in urgency_words):
            if len(title) < 50:
                urgency_word = random.choice(urgency_words)
                title = f"{urgency_word}: {title}"
        
        return title
    
    def _add_social_elements(self, title: str) -> str:
        """Add social proof elements to title"""
        
        social_elements = [
            "Everyone's Talking About", "Millions Are Watching", "Trending:",
            "Viral:", "Popular:", "Everyone Needs to Know"
        ]
        
        if not any(element.lower() in title.lower() for element in social_elements):
            if len(title) < 45:
                social_element = random.choice(social_elements)
                title = f"{social_element} {title}"
        
        return title
    
    def _add_reward_elements(self, title: str) -> str:
        """Add reward anticipation elements to title"""
        
        reward_words = ["AMAZING", "INCREDIBLE", "LIFE-CHANGING", "GAME-CHANGING", "BREAKTHROUGH"]
        
        if not any(word in title.upper() for word in reward_words):
            if len(title) < 50:
                reward_word = random.choice(reward_words)
                title = f"{reward_word} {title}"
        
        return title
    
    async def _optimize_script_psychology(
        self,
        script: str,
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> str:
        """Optimize script with psychological manipulation"""
        
        if not script:
            return script
        
        lines = script.split('\n')
        optimized_lines = []
        
        avg_attention_span = audience_analysis.get('avg_attention_span', 120)
        
        for i, line in enumerate(lines):
            optimized_line = line
            
            # Add psychological triggers based on timing
            progress = i / max(len(lines), 1)
            
            # Apply strategy-specific optimizations
            for strategy in strategies:
                if progress in [t for t in strategy.optimal_timing if abs(t - progress) < 0.1]:
                    optimized_line = self._apply_strategy_to_line(optimized_line, strategy)
            
            # Add attention hooks at critical points
            if i == 0:  # Opening hook
                optimized_line = self._add_opening_hook(optimized_line, audience_analysis)
            elif progress > 0.3 and progress < 0.4:  # Mid-point retention
                optimized_line = self._add_retention_hook(optimized_line)
            elif progress > 0.8:  # End engagement
                optimized_line = self._add_engagement_hook(optimized_line)
            
            optimized_lines.append(optimized_line)
        
        return '\n'.join(optimized_lines)
    
    def _create_dopamine_schedule(
        self,
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create dopamine release schedule for video"""
        
        # Base schedule for dopamine peaks
        base_schedule = [0.05, 0.15, 0.35, 0.55, 0.75, 0.90]
        
        avg_susceptibility = audience_analysis.get('avg_susceptibility', 0.5)
        avg_attention_span = audience_analysis.get('avg_attention_span', 120)
        
        # Adjust frequency based on attention span
        if avg_attention_span < 60:  # Short attention span
            schedule = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95]
        elif avg_attention_span > 300:  # Long attention span
            schedule = [0.08, 0.25, 0.45, 0.65, 0.85]
        else:
            schedule = base_schedule
        
        # Adjust intensity based on susceptibility
        intensity_multiplier = 0.5 + (avg_susceptibility * 0.5)
        
        dopamine_schedule = {
            'peak_times': schedule,
            'intensity_multiplier': intensity_multiplier,
            'trigger_types': {
                timing: self._select_dopamine_trigger(timing, strategies)
                for timing in schedule
            }
        }
        
        return dopamine_schedule
    
    def _generate_psychological_cues(
        self,
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate psychological timing cues for video"""
        
        cues = []
        
        # Generate cues for each strategy
        for strategy in strategies:
            for timing in strategy.optimal_timing:
                cue = {
                    'timing': timing,
                    'strategy': strategy.name,
                    'trigger_type': strategy.trigger_type,
                    'implementation': self._get_implementation_cue(strategy),
                    'intensity': self._calculate_cue_intensity(strategy, audience_analysis)
                }
                cues.append(cue)
        
        # Sort by timing
        cues.sort(key=lambda x: x['timing'])
        
        return cues
    
    def _generate_retention_hooks(
        self,
        strategies: List[PsychologicalStrategy],
        audience_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate retention hooks for video"""
        
        avg_attention_span = audience_analysis.get('avg_attention_span', 120)
        
        hooks = []
        
        # Critical retention points
        critical_points = [0.15, 0.30, 0.50, 0.70]  # Where people typically drop off
        
        for point in critical_points:
            if point * 600 < avg_attention_span:  # Only if within attention span
                hook = {
                    'timing': point,
                    'hook_type': self._select_hook_type(point, strategies),
                    'intensity': 'high' if point < 0.3 else 'medium',
                    'message': self._generate_hook_message(point, audience_analysis)
                }
                hooks.append(hook)
        
        return hooks
    
    # Helper methods continue...
    
    def _default_behavioral_patterns(self) -> Dict[str, float]:
        """Default behavioral patterns for new viewers"""
        return {
            'avg_session_length': 120.0,
            'session_consistency': 0.5,
            'avg_engagement': 0.5,
            'engagement_trend': 0.0,
            'content_diversity': 0.5,
            'peak_hour_consistency': 0.6,
            'avg_completion_rate': 0.6,
            'completion_improvement': 0.0,
            'binge_tendency': 0.3,
            'social_engagement': 0.4
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction (-1 to 1)"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope, _, r_value, _, _ = stats.linregress(x, values)
        
        return np.clip(slope * r_value, -1, 1)
    
    def _calculate_peak_consistency(self, hours: List[int]) -> float:
        """Calculate consistency of peak viewing hours"""
        if not hours:
            return 0.5
        
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        max_count = max(hour_counts.values())
        return max_count / len(hours)
    
    def _count_same_day_sessions(self, viewing_history: List[Dict[str, Any]]) -> int:
        """Count sessions on same days (binge indicator)"""
        dates = [v.get('date', '').split()[0] for v in viewing_history if v.get('date')]
        date_counts = {}
        
        for date in dates:
            date_counts[date] = date_counts.get(date, 0) + 1
        
        return sum(1 for count in date_counts.values() if count > 1)
    
    def _get_length_bucket(self, length: int) -> Tuple[int, int]:
        """Get length bucket for video duration"""
        if length < 120:
            return (0, 120)
        elif length < 300:
            return (120, 300)
        elif length < 600:
            return (300, 600)
        elif length < 1200:
            return (600, 1200)
        else:
            return (1200, 3600)
    
    def _calculate_decay_rate(self, retention_curve: List[float]) -> float:
        """Calculate attention decay rate from retention curve"""
        if len(retention_curve) < 2:
            return 0.2
        
        # Calculate average decay between points
        decays = []
        for i in range(1, len(retention_curve)):
            decay = retention_curve[i-1] - retention_curve[i]
            decays.append(max(decay, 0))
        
        return np.mean(decays) if decays else 0.2
    
    def _generate_viewer_id(self) -> str:
        """Generate unique viewer ID"""
        timestamp = str(int(time.time()))
        random_suffix = str(random.randint(10000, 99999))
        return f"viewer_{timestamp}_{random_suffix}"
    
    def _store_viewer_profile(self, profile: ViewerProfile):
        """Store viewer profile in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO viewer_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.viewer_id,
            json.dumps(profile.demographics),
            json.dumps(profile.behavioral_patterns),
            json.dumps(profile.psychological_triggers),
            profile.attention_span,
            profile.addiction_susceptibility,
            json.dumps(profile.optimal_content_length),
            json.dumps(profile.emotional_preferences),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def run_psychological_experiment(
        self,
        strategy_a: str,
        strategy_b: str,
        audience_sample: List[ViewerProfile],
        content_variations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run A/B testing for psychological strategies"""
        
        logger.info(f"🧪 Running psychological experiment: {strategy_a} vs {strategy_b}")
        
        # Split audience randomly
        random.shuffle(audience_sample)
        group_size = len(audience_sample) // 2
        
        group_a = audience_sample[:group_size]
        group_b = audience_sample[group_size:group_size*2]
        
        # Apply strategies
        content_a = await self.optimize_content_psychology(
            content_variations[0],
            group_a
        )
        
        content_b = await self.optimize_content_psychology(
            content_variations[1] if len(content_variations) > 1 else content_variations[0],
            group_b
        )
        
        # Simulate performance (in production, this would be real metrics)
        performance_a = self._simulate_performance(content_a, group_a)
        performance_b = self._simulate_performance(content_b, group_b)
        
        # Calculate statistical significance
        significance = self._calculate_statistical_significance(performance_a, performance_b)
        
        # Store results
        experiment_results = {
            'strategy_a': strategy_a,
            'strategy_b': strategy_b,
            'performance_a': performance_a,
            'performance_b': performance_b,
            'improvement': ((performance_b - performance_a) / performance_a) * 100,
            'confidence_level': significance,
            'winner': strategy_b if performance_b > performance_a else strategy_a,
            'sample_size': len(audience_sample)
        }
        
        self._store_experiment_results(experiment_results)
        
        logger.info(f"✅ Experiment complete - Winner: {experiment_results['winner']}")
        return experiment_results

# USAGE EXAMPLE
if __name__ == "__main__":
    async def main():
        # Initialize psychological optimizer
        optimizer = PsychologicalOptimizer()
        
        # Sample viewer data
        viewer_data = {
            'viewer_id': 'test_viewer_001',
            'demographics': {'age': 25, 'location': 'US'}
        }
        
        viewing_history = [
            {'watch_time': 180, 'engagement_score': 0.8, 'content_type': 'tutorial'},
            {'watch_time': 240, 'engagement_score': 0.7, 'content_type': 'entertainment'},
            {'watch_time': 150, 'engagement_score': 0.9, 'content_type': 'tutorial'}
        ]
        
        # Analyze viewer psychology
        profile = await optimizer.analyze_viewer_psychology(viewer_data, viewing_history)
        
        print("🧠 Viewer Psychology Analysis:")
        print(f"Attention Span: {profile.attention_span:.0f}s")
        print(f"Addiction Susceptibility: {profile.addiction_susceptibility:.2f}")
        print(f"Top Triggers: {profile.psychological_triggers[:3]}")
    
    # Run the psychological optimizer
    asyncio.run(main())
