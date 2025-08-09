#!/usr/bin/env python3
"""
🛡️ CONTENT POLICY CHECKER 🛡️
Advanced content compliance system for copyright, profanity, COPPA, and policy violations.

Checks content before upload to prevent policy violations and ensure
advertiser-friendly content across all platforms.
"""

import re
import json
import logging
import requests
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
from pathlib import Path
import difflib
import time
from urllib.parse import urlparse
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComplianceResult:
    """Result of compliance checking"""
    content_id: str
    overall_score: float  # 0-100, higher is better
    is_compliant: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    recommendations: List[str]
    checked_at: datetime
    check_duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'content_id': self.content_id,
            'overall_score': self.overall_score,
            'is_compliant': self.is_compliant,
            'violations': self.violations,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'checked_at': self.checked_at.isoformat(),
            'check_duration': self.check_duration
        }

@dataclass
class PolicyViolation:
    """Individual policy violation"""
    violation_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    location: Optional[str] = None  # Where in content
    confidence: float = 1.0  # 0-1
    suggested_fix: Optional[str] = None

class ContentPolicyChecker:
    """
    🛡️ COMPREHENSIVE CONTENT POLICY CHECKER 🛡️
    
    Checks content against various compliance requirements:
    - Copyright detection
    - Profanity filtering
    - COPPA compliance
    - Advertiser-friendly guidelines
    - Spam detection
    - Misinformation checks
    """
    
    def __init__(self, db_path: str = "compliance_data.db"):
        """
        Initialize policy checker
        
        Args:
            db_path: Database path for storing violation patterns and results
        """
        self.db_path = db_path
        self._initialize_database()
        self._load_violation_patterns()
        self._load_copyright_database()
        
        # Compliance thresholds
        self.thresholds = {
            'overall_compliance': 70.0,  # Minimum score for compliance
            'copyright_similarity': 0.85,  # Threshold for copyright detection
            'profanity_confidence': 0.8,   # Threshold for profanity detection
            'spam_score': 0.7,             # Threshold for spam detection
        }
        
        logger.info("🛡️ Content Policy Checker initialized")
    
    def _initialize_database(self):
        """Initialize compliance database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compliance results
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_results (
            content_id TEXT PRIMARY KEY,
            overall_score REAL,
            is_compliant BOOLEAN,
            violations TEXT,
            warnings TEXT,
            recommendations TEXT,
            checked_at TEXT,
            check_duration REAL
        )
        ''')
        
        # Copyright database
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS copyright_content (
            content_hash TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            source TEXT,
            owner TEXT,
            added_at TEXT
        )
        ''')
        
        # Known profanity patterns
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profanity_patterns (
            pattern TEXT PRIMARY KEY,
            severity TEXT,
            language TEXT,
            category TEXT,
            added_at TEXT
        )
        ''')
        
        # Violation history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS violation_history (
            violation_id TEXT PRIMARY KEY,
            content_id TEXT,
            violation_type TEXT,
            severity TEXT,
            description TEXT,
            detected_at TEXT,
            resolved BOOLEAN DEFAULT FALSE
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Compliance database initialized")
    
    def _load_violation_patterns(self):
        """Load violation patterns from database and files"""
        # Profanity patterns (basic set - in production would be more comprehensive)
        self.profanity_patterns = [
            # Mild profanity
            (r'\b(damn|hell|crap|stupid|idiot)\b', 'low'),
            # Strong profanity (censored examples)
            (r'\b(f[*\w]*k|sh[*\w]*t|b[*\w]*ch)\b', 'high'),
            # Offensive terms
            (r'\b(hate|kill|die|murder)\b', 'medium'),
        ]
        
        # Spam patterns
        self.spam_patterns = [
            (r'\b(click here|subscribe now|buy now|limited time|act fast)\b', 0.6),
            (r'(!!!|🔥🔥🔥|💰💰💰)', 0.4),
            (r'\b(free money|get rich|work from home|make money fast)\b', 0.8),
            (r'(\$\$\$|€€€|£££)', 0.5),
        ]
        
        # COPPA-related patterns (content targeting children)
        self.coppa_patterns = [
            (r'\b(kids|children|child|toddler|baby)\b', 0.7),
            (r'\b(toy|game|cartoon|animated|fun|play)\b', 0.5),
            (r'\b(education|learning|school|teacher)\b', 0.4),
        ]
        
        # Misinformation indicators
        self.misinformation_patterns = [
            (r'\b(conspiracy|hoax|fake news|cover[- ]?up)\b', 0.6),
            (r'\b(miracle cure|secret|they don\'t want you to know)\b', 0.8),
            (r'\b(100% proven|guaranteed|never fails)\b', 0.5),
        ]
    
    def _load_copyright_database(self):
        """Load known copyrighted content patterns"""
        # In production, this would load from a comprehensive database
        self.copyright_signatures = {}
        
        # Example signatures for known copyrighted content
        known_content = [
            {
                'title': 'Popular Song Title',
                'signature': 'signature_hash_example',
                'owner': 'Record Label',
                'type': 'audio'
            },
            {
                'title': 'Movie Title',
                'signature': 'movie_signature_hash',
                'owner': 'Studio Name',
                'type': 'video'
            }
        ]
        
        for item in known_content:
            self.copyright_signatures[item['signature']] = item
    
    def check_content(self, content_data: Dict[str, Any], rules: Dict[str, Any] = None) -> ComplianceResult:
        """
        Run comprehensive compliance check on content
        
        Args:
            content_data: Content to check (title, description, script, etc.)
            rules: Custom compliance rules to apply
            
        Returns:
            ComplianceResult with detailed analysis
        """
        start_time = time.time()
        content_id = content_data.get('id', f"content_{int(time.time())}")
        
        # Initialize results
        violations = []
        warnings = []
        recommendations = []
        scores = {}
        
        # Apply default rules if none provided
        if rules is None:
            rules = {
                'copyright_check': True,
                'profanity_filter': True,
                'coppa_compliant': True,
                'advertiser_friendly': True,
                'spam_detection': True,
                'misinformation_check': True
            }
        
        try:
            # Copyright check
            if rules.get('copyright_check', True):
                copyright_result = self._check_copyright(content_data)
                scores['copyright'] = copyright_result['score']
                violations.extend(copyright_result['violations'])
                warnings.extend(copyright_result['warnings'])
                recommendations.extend(copyright_result['recommendations'])
            
            # Profanity check
            if rules.get('profanity_filter', True):
                profanity_result = self._check_profanity(content_data)
                scores['profanity'] = profanity_result['score']
                violations.extend(profanity_result['violations'])
                warnings.extend(profanity_result['warnings'])
                recommendations.extend(profanity_result['recommendations'])
            
            # COPPA compliance
            if rules.get('coppa_compliant', True):
                coppa_result = self._check_coppa_compliance(content_data)
                scores['coppa'] = coppa_result['score']
                violations.extend(coppa_result['violations'])
                warnings.extend(coppa_result['warnings'])
                recommendations.extend(coppa_result['recommendations'])
            
            # Advertiser-friendly check
            if rules.get('advertiser_friendly', True):
                advertiser_result = self._check_advertiser_friendly(content_data)
                scores['advertiser_friendly'] = advertiser_result['score']
                violations.extend(advertiser_result['violations'])
                warnings.extend(advertiser_result['warnings'])
                recommendations.extend(advertiser_result['recommendations'])
            
            # Spam detection
            if rules.get('spam_detection', True):
                spam_result = self._check_spam(content_data)
                scores['spam'] = spam_result['score']
                violations.extend(spam_result['violations'])
                warnings.extend(spam_result['warnings'])
            
            # Misinformation check
            if rules.get('misinformation_check', True):
                misinfo_result = self._check_misinformation(content_data)
                scores['misinformation'] = misinfo_result['score']
                violations.extend(misinfo_result['violations'])
                warnings.extend(misinfo_result['warnings'])
                recommendations.extend(misinfo_result['recommendations'])
            
            # Calculate overall score
            overall_score = sum(scores.values()) / len(scores) if scores else 100.0
            
            # Determine compliance status
            is_compliant = (overall_score >= self.thresholds['overall_compliance'] and 
                          not any(v['severity'] == 'critical' for v in violations))
            
            # Add general recommendations
            if overall_score < 90:
                recommendations.append("Consider reviewing content for better compliance")
            if len(violations) > 0:
                recommendations.append("Address all violations before publishing")
            
        except Exception as e:
            logger.error(f"Error during compliance check: {e}")
            violations.append({
                'violation_type': 'system_error',
                'severity': 'high',
                'description': f"System error during compliance check: {str(e)}",
                'confidence': 1.0
            })
            overall_score = 0.0
            is_compliant = False
        
        # Create result
        check_duration = time.time() - start_time
        result = ComplianceResult(
            content_id=content_id,
            overall_score=overall_score,
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            checked_at=datetime.now(),
            check_duration=check_duration
        )
        
        # Store result in database
        self._store_compliance_result(result)
        
        logger.info(f"🛡️ Compliance check completed for {content_id}: "
                   f"Score {overall_score:.1f}, Compliant: {is_compliant}")
        
        return result
    
    def _check_copyright(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for copyright violations"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        # Check title and description for known copyrighted content
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')}"
        
        # Simple similarity check against known content
        for signature, known_item in self.copyright_signatures.items():
            similarity = self._calculate_text_similarity(
                text_content.lower(), 
                known_item.get('title', '').lower()
            )
            
            if similarity > self.thresholds['copyright_similarity']:
                violations.append({
                    'violation_type': 'copyright_infringement',
                    'severity': 'critical',
                    'description': f"Content appears to infringe on '{known_item['title']}' owned by {known_item['owner']}",
                    'confidence': similarity,
                    'suggested_fix': f"Remove or replace content similar to '{known_item['title']}'"
                })
                score = 0.0
        
        # Check for common copyright indicators
        copyright_indicators = [
            (r'\b(soundtrack|theme song|movie clip|tv show)\b', 'medium'),
            (r'\b(copyright|©|\(c\)|all rights reserved)\b', 'low'),
            (r'\b(cover song|remix|parody|tribute)\b', 'medium'),
        ]
        
        for pattern, severity in copyright_indicators:
            matches = re.finditer(pattern, text_content.lower())
            for match in matches:
                if severity == 'medium':
                    warnings.append({
                        'violation_type': 'potential_copyright',
                        'severity': severity,
                        'description': f"Potential copyright content detected: '{match.group()}'",
                        'location': f"Position {match.start()}-{match.end()}",
                        'confidence': 0.7
                    })
                    score = min(score, 80.0)
        
        if not violations and not warnings:
            recommendations.append("Content appears free of copyright violations")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _check_profanity(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for profanity and offensive language"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        # Combine text content
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')} {content_data.get('script', '')}"
        
        profanity_count = 0
        total_severity_score = 0
        
        for pattern, severity in self.profanity_patterns:
            matches = re.finditer(pattern, text_content.lower(), re.IGNORECASE)
            for match in matches:
                profanity_count += 1
                
                severity_scores = {'low': 10, 'medium': 25, 'high': 50}
                penalty = severity_scores.get(severity, 25)
                total_severity_score += penalty
                
                violation = {
                    'violation_type': 'profanity',
                    'severity': severity,
                    'description': f"Profanity detected: '{match.group()}'",
                    'location': f"Position {match.start()}-{match.end()}",
                    'confidence': 0.9,
                    'suggested_fix': f"Replace or remove '{match.group()}'"
                }
                
                if severity in ['high', 'critical']:
                    violations.append(violation)
                else:
                    warnings.append(violation)
        
        # Calculate score penalty
        if total_severity_score > 0:
            score = max(0, 100 - total_severity_score)
        
        if profanity_count == 0:
            recommendations.append("Content is free of profanity")
        else:
            recommendations.append(f"Remove or replace {profanity_count} instances of profanity")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _check_coppa_compliance(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check COPPA compliance for child-directed content"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')}"
        
        child_targeting_score = 0
        for pattern, weight in self.coppa_patterns:
            matches = len(re.findall(pattern, text_content.lower(), re.IGNORECASE))
            child_targeting_score += matches * weight
        
        # If content appears to target children
        if child_targeting_score > 2.0:
            # Check for COPPA violations
            coppa_violations = [
                (r'\b(personal info|email|phone|address|full name)\b', 'Request for personal information'),
                (r'\b(buy|purchase|credit card|payment)\b', 'Commercial content targeting children'),
                (r'\b(meet|contact|private message)\b', 'Inappropriate contact suggestions'),
            ]
            
            for pattern, description in coppa_violations:
                if re.search(pattern, text_content.lower()):
                    violations.append({
                        'violation_type': 'coppa_violation',
                        'severity': 'critical',
                        'description': f"COPPA violation: {description}",
                        'confidence': 0.8,
                        'suggested_fix': f"Remove {description.lower()} from child-directed content"
                    })
                    score = 0.0
            
            # General COPPA compliance check
            if not content_data.get('coppa_compliant', False):
                warnings.append({
                    'violation_type': 'coppa_compliance',
                    'severity': 'medium',
                    'description': 'Content may be directed at children - ensure COPPA compliance',
                    'confidence': min(child_targeting_score / 5.0, 1.0),
                    'suggested_fix': 'Mark as child-directed and ensure COPPA compliance'
                })
                score = min(score, 75.0)
        
        if child_targeting_score > 2.0:
            recommendations.append("Content appears to target children - ensure COPPA compliance")
        else:
            recommendations.append("Content does not appear to specifically target children")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _check_advertiser_friendly(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if content is advertiser-friendly"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')}"
        
        # Advertiser-unfriendly topics
        unfriendly_patterns = [
            (r'\b(violence|violent|fight|attack|war|weapon)\b', 'Violence-related content', 30),
            (r'\b(drug|alcohol|smoking|addiction|substance)\b', 'Substance-related content', 25),
            (r'\b(sex|sexual|adult|mature|explicit)\b', 'Adult content', 40),
            (r'\b(politics|political|election|government|controversy)\b', 'Political content', 15),
            (r'\b(tragedy|disaster|death|accident|crisis)\b', 'Sensitive events', 35),
            (r'\b(hate|discrimination|racist|sexist)\b', 'Hate speech', 50),
        ]
        
        total_penalty = 0
        for pattern, description, penalty in unfriendly_patterns:
            matches = len(re.findall(pattern, text_content.lower(), re.IGNORECASE))
            if matches > 0:
                total_penalty += penalty
                
                severity = 'high' if penalty >= 40 else 'medium' if penalty >= 25 else 'low'
                
                warning = {
                    'violation_type': 'advertiser_unfriendly',
                    'severity': severity,
                    'description': f"Potentially advertiser-unfriendly content: {description}",
                    'confidence': min(matches * 0.3, 1.0),
                    'suggested_fix': f"Consider removing or moderating {description.lower()}"
                }
                
                if severity == 'high':
                    violations.append(warning)
                else:
                    warnings.append(warning)
        
        # Apply penalty to score
        score = max(0, 100 - total_penalty)
        
        if total_penalty == 0:
            recommendations.append("Content appears advertiser-friendly")
        else:
            recommendations.append("Review content for advertiser-friendliness")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _check_spam(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for spam patterns"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')}"
        
        spam_score = 0
        for pattern, weight in self.spam_patterns:
            matches = len(re.findall(pattern, text_content, re.IGNORECASE))
            spam_score += matches * weight
        
        if spam_score > self.thresholds['spam_score']:
            violations.append({
                'violation_type': 'spam_content',
                'severity': 'high',
                'description': f"Content appears to be spam (score: {spam_score:.2f})",
                'confidence': min(spam_score, 1.0),
                'suggested_fix': "Remove spammy language and promotional content"
            })
            score = max(0, 100 - spam_score * 50)
        elif spam_score > 0.3:
            warnings.append({
                'violation_type': 'potential_spam',
                'severity': 'medium',
                'description': f"Content may appear spammy (score: {spam_score:.2f})",
                'confidence': spam_score,
                'suggested_fix': "Reduce promotional language"
            })
            score = max(50, 100 - spam_score * 30)
        
        if spam_score == 0:
            recommendations.append("Content is free of spam indicators")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _check_misinformation(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for potential misinformation patterns"""
        violations = []
        warnings = []
        recommendations = []
        score = 100.0
        
        text_content = f"{content_data.get('title', '')} {content_data.get('description', '')}"
        
        misinfo_score = 0
        for pattern, weight in self.misinformation_patterns:
            matches = len(re.findall(pattern, text_content.lower(), re.IGNORECASE))
            misinfo_score += matches * weight
        
        if misinfo_score > 0.6:
            violations.append({
                'violation_type': 'potential_misinformation',
                'severity': 'high',
                'description': f"Content may contain misinformation (score: {misinfo_score:.2f})",
                'confidence': min(misinfo_score, 1.0),
                'suggested_fix': "Verify claims and provide credible sources"
            })
            score = max(0, 100 - misinfo_score * 60)
        elif misinfo_score > 0.3:
            warnings.append({
                'violation_type': 'verify_claims',
                'severity': 'medium',
                'description': f"Some claims may need verification (score: {misinfo_score:.2f})",
                'confidence': misinfo_score,
                'suggested_fix': "Provide sources for significant claims"
            })
            score = max(70, 100 - misinfo_score * 40)
        
        if misinfo_score == 0:
            recommendations.append("Content appears factual")
        else:
            recommendations.append("Verify all significant claims with credible sources")
        
        return {
            'score': score,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _store_compliance_result(self, result: ComplianceResult):
        """Store compliance result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO compliance_results 
            (content_id, overall_score, is_compliant, violations, warnings, recommendations, checked_at, check_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.content_id,
                result.overall_score,
                result.is_compliant,
                json.dumps(result.violations),
                json.dumps(result.warnings),
                json.dumps(result.recommendations),
                result.checked_at.isoformat(),
                result.check_duration
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store compliance result: {e}")
    
    def get_compliance_history(self, content_id: str) -> Optional[ComplianceResult]:
        """Get compliance history for content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM compliance_results WHERE content_id = ?
            ORDER BY checked_at DESC LIMIT 1
            ''', (content_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ComplianceResult(
                    content_id=row[0],
                    overall_score=row[1],
                    is_compliant=bool(row[2]),
                    violations=json.loads(row[3]),
                    warnings=json.loads(row[4]),
                    recommendations=json.loads(row[5]),
                    checked_at=datetime.fromisoformat(row[6]),
                    check_duration=row[7]
                )
            
        except Exception as e:
            logger.error(f"Failed to get compliance history: {e}")
        
        return None
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute('SELECT COUNT(*), AVG(overall_score), SUM(is_compliant) FROM compliance_results')
            total_checks, avg_score, compliant_count = cursor.fetchone()
            
            # Recent violations
            cursor.execute('''
            SELECT violation_type, COUNT(*) 
            FROM (
                SELECT json_extract(value, '$.violation_type') as violation_type
                FROM compliance_results, json_each(violations)
                WHERE checked_at > datetime('now', '-7 days')
            )
            GROUP BY violation_type
            ORDER BY COUNT(*) DESC
            ''')
            recent_violations = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_checks': total_checks or 0,
                'average_score': avg_score or 0,
                'compliance_rate': (compliant_count / total_checks * 100) if total_checks else 0,
                'recent_violations': recent_violations
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance stats: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Initialize policy checker
    checker = ContentPolicyChecker()
    
    # Test content
    test_content = {
        'id': 'test_video_123',
        'title': 'Amazing Tech Tutorial - Learn Programming Fast!',
        'description': 'In this video, we explore advanced programming techniques. Subscribe now for more content!',
        'script': 'Welcome everyone to this educational programming tutorial...',
        'coppa_compliant': True
    }
    
    # Run compliance check
    result = checker.check_content(test_content)
    
    # Display results
    print(f"🛡️ Compliance Check Results:")
    print(f"   Content ID: {result.content_id}")
    print(f"   Overall Score: {result.overall_score:.1f}/100")
    print(f"   Compliant: {'✅ Yes' if result.is_compliant else '❌ No'}")
    print(f"   Violations: {len(result.violations)}")
    print(f"   Warnings: {len(result.warnings)}")
    print(f"   Check Duration: {result.check_duration:.3f}s")
    
    if result.violations:
        print(f"\n⚠️  Violations:")
        for v in result.violations:
            print(f"   - {v['violation_type']}: {v['description']}")
    
    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")
    
    # Get stats
    stats = checker.get_compliance_stats()
    print(f"\n📊 Compliance Statistics:")
    print(f"   Total Checks: {stats.get('total_checks', 0)}")
    print(f"   Average Score: {stats.get('average_score', 0):.1f}")
    print(f"   Compliance Rate: {stats.get('compliance_rate', 0):.1f}%")
