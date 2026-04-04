"""
DeepSeek AI Chatbot Service for Feng Shui Improvement Recommendations
Provides contextual AI-powered advice based on analysis results
"""

import requests
import json
import logging
import time
import hashlib
import re
from typing import Dict, List, Any, Optional
from config import Config

logger = logging.getLogger(__name__)


class FengShuiChatbot:
    """
    AI-powered chatbot for feng shui improvement recommendations using DeepSeek API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chatbot with DeepSeek API credentials.
        
        Args:
            api_key: DeepSeek API key (optional, can be set in config)
        """
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        self.model = Config.DEEPSEEK_MODEL
        self._improve_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_sec = 600
        self._score_cache: Dict[str, Dict[str, Any]] = {}
        self._score_cache_ttl_sec = 1800
        
        if not self.api_key or self.api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
            logger.warning("⚠ DeepSeek API key not configured. Chatbot will return mock responses.")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines the AI's role and knowledge."""
        return """You are a Feng Shui Master AI assistant. Provide specific, actionable advice based on traditional principles and modern science. Structure responses as: Quick wins, Medium-term, Long-term. Keep answers concise (150-250 words) and practical."""

    def _truncate_text(self, value: Any, max_len: int = 180) -> str:
        text = str(value) if value is not None else ''
        if len(text) <= max_len:
            return text
        return text[:max_len].rstrip() + '...'

    def _cache_key(self, analysis_data: Dict[str, Any], user_query: Optional[str]) -> str:
        raw = json.dumps({'analysis': analysis_data, 'query': user_query or ''}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _score_cache_key(self, score_context: Dict[str, Any]) -> str:
        raw = json.dumps(score_context, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _get_cached_improve(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._improve_cache.get(key)
        if not item:
            return None
        if time.time() - item.get('ts', 0) > self._cache_ttl_sec:
            self._improve_cache.pop(key, None)
            return None
        return item.get('result')

    def _set_cached_improve(self, key: str, result: Dict[str, Any]) -> None:
        self._improve_cache[key] = {
            'ts': time.time(),
            'result': result,
        }

    def _get_cached_score(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._score_cache.get(key)
        if not item:
            return None
        if time.time() - item.get('ts', 0) > self._score_cache_ttl_sec:
            self._score_cache.pop(key, None)
            return None
        return item.get('result')

    def _set_cached_score(self, key: str, result: Dict[str, Any]) -> None:
        self._score_cache[key] = {
            'ts': time.time(),
            'result': result,
        }

    def _extract_json_object(self, raw_text: str) -> Optional[Dict[str, Any]]:
        text = str(raw_text or '').strip()
        if not text:
            return None

        if text.startswith('```'):
            text = text.strip('`')
            text = text.replace('json\n', '', 1)

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        match = re.search(r'\{[\s\S]*\}', text)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

        return None

    def _clamp_score(self, value: Any) -> Optional[float]:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(100.0, parsed))

    def get_deepseek_score(self, score_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get a DeepSeek-evaluated Feng Shui score for score alignment."""
        try:
            cache_key = self._score_cache_key(score_context)
            cached = self._get_cached_score(cache_key)
            if cached:
                cached_copy = dict(cached)
                cached_copy['cached'] = True
                return cached_copy

            if not self.api_key or self.api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
                return {
                    'success': False,
                    'error': 'not_configured',
                    'message': 'DeepSeek API key not configured'
                }

            system_prompt = (
                'You are an expert Feng Shui scoring evaluator with deep knowledge of classical principles. '
                'Apply the following classical Feng Shui framework when evaluating locations:\n'
                '### Classical Principles (背山面水 - Mountain-Backed, Water-Facing):\n'
                '- 背山 (backed by mountains): Solid support from topography/buildings behind\n'
                '- 面水 (facing water): Open access to water (rivers, lakes) in front\n'
                '- 砂 (sand formations): Building heights should frame and protect, not oppress\n'
                '- 水 (water): Must flow gently, never stagnant; 朝阳水 (sun-facing water) ideal\n'
                '### Five Elements Balance (木火土金水 - Wood Fire Earth Metal Water):\n'
                '- Green space = Wood element (growth, vitality)\n'
                '- Water/rivers = Water element (flow, wealth)\n'
                '- Fire = Exposed heights, open southern views\n'
                '- Metal = Round/circular features, minerals\n'
                '- Earth = Soil stability, flatness\n'
                '### Yin-Yang Harmony:\n'
                '- Yang (brightness, openness): South-facing, open space, activity\n'
                '- Yin (darkness, density): Mountains/buildings, shade, tranquility\n'
                '- Optimal: 60% Yang in urban, 40% Yang in rural\n'
                '### Environmental Quality:\n'
                '- Air quality: Evaluate from green coverage, density, and wind flow\n'
                '- Noise: High road/traffic density = negative, isolated = positive\n'
                '- Sunlight: South-facing best in Northern Hemisphere, North in Southern\n'
                '- Flood risk: Valleys without proper drainage = hazard zone\n'
                'Return strictly valid JSON with this schema:\n'
                '{"overall_score": number, "category_scores": {"green_space": number, "water_element": number, '
                '"building_harmony": number, "road_accessibility": number, "orientation": number, '
                '"environment": number, "spiritual_energy": number, "yin_yang_balance": number, '
                '"five_elements_harmony": number, "qi_flow": number}, '
                '"confidence": number, "reason": string}. '
                'All numeric scores must be between 0 and 100. No markdown. '
                'If input.policy.reputation_floor_score is provided, overall_score must be >= that floor. '
                'If input.location_context.reputation_tier is "legendary", keep overall_score in 98-100 unless input features show extreme hazard. '
                'If input.policy.target_similarity_pct is provided, keep category_scores internally coherent with overall_score.'
            )

            user_prompt = (
                'Evaluate this location scoring context and output JSON only:\n' +
                json.dumps(score_context, ensure_ascii=False, separators=(',', ':'))
            )

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 420,
                "stream": False
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=12
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'deepseek_http_{response.status_code}',
                    'message': 'DeepSeek score request failed'
                }

            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            parsed = self._extract_json_object(content)

            if not parsed:
                # Fallback: try to parse a plain number if JSON was not followed.
                match = re.search(r'(-?\d+(?:\.\d+)?)', str(content))
                if not match:
                    return {
                        'success': False,
                        'error': 'parse_failed',
                        'message': 'Unable to parse DeepSeek score response'
                    }
                deepseek_score = self._clamp_score(match.group(1))
                if deepseek_score is None:
                    return {
                        'success': False,
                        'error': 'invalid_score',
                        'message': 'DeepSeek score was not numeric'
                    }
                response_payload = {
                    'success': True,
                    'overall_score': deepseek_score,
                    'category_scores': {},
                    'confidence': None,
                    'reason': str(content)[:280],
                    'model': self.model
                }
                self._set_cached_score(cache_key, response_payload)
                return response_payload

            deepseek_score = self._clamp_score(parsed.get('overall_score'))
            if deepseek_score is None:
                return {
                    'success': False,
                    'error': 'missing_overall_score',
                    'message': 'DeepSeek response missing overall_score'
                }

            raw_categories = parsed.get('category_scores') or {}
            category_scores: Dict[str, float] = {}
            if isinstance(raw_categories, dict):
                for key, value in raw_categories.items():
                    parsed_value = self._clamp_score(value)
                    if parsed_value is not None:
                        category_scores[str(key)] = parsed_value

            confidence = self._clamp_score(parsed.get('confidence'))

            response_payload = {
                'success': True,
                'overall_score': deepseek_score,
                'category_scores': category_scores,
                'confidence': confidence,
                'reason': str(parsed.get('reason', ''))[:280],
                'model': self.model
            }
            self._set_cached_score(cache_key, response_payload)
            return response_payload

        except requests.Timeout:
            return {
                'success': False,
                'error': 'timeout',
                'message': 'DeepSeek score request timed out'
            }
        except Exception as e:
            logger.error(f"Error requesting DeepSeek score: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'DeepSeek score request failed'
            }
    
    def _build_context_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Build context from analysis data to provide relevant recommendations."""
        context_parts = []

        if 'analysis_type' in analysis_data:
            context_parts.append(f"Analysis Type: {analysis_data['analysis_type']}")
        
        # Location info (simplified)
        if 'location' in analysis_data:
            loc = analysis_data['location']
            addr = str(loc.get('address', 'Unknown'))[:80]
            context_parts.append(f"Location: {addr}")
        
        # Overall scores (condensed)
        if 'scores' in analysis_data:
            scores = analysis_data['scores']
            if 'qi_flow' in scores and isinstance(scores.get('qi_flow'), (int, float)):
                qi = float(scores.get('qi_flow'))
                context_parts.append(f"Qi Flow: {qi:.0f}/100 - {self._get_rating(qi)}")
            elif 'overall' in scores and isinstance(scores.get('overall'), (int, float)):
                overall = float(scores.get('overall'))
                context_parts.append(f"Overall Score: {overall:.0f}/100 - {self._get_rating(overall)}")
            
            # Essential scores only
            for key in ['orientation', 'road_access', 'building_density', 'water_presence', 'green_space']:
                if key in scores:
                    context_parts.append(f"{key.replace('_', ' ').title()}: {scores[key]}")

            # Include any additional score metrics (useful for indoor analyses).
            preferred_order = [
                'overall', 'element_balance', 'energy_balance', 'space_flow', 'functional_layout',
                'lighting', 'color_harmony', 'furniture_placement', 'declutter',
                'wood', 'fire', 'earth', 'metal', 'water'
            ]

            for key in preferred_order:
                if key in scores and key not in ['qi_flow', 'orientation', 'road_access', 'building_density', 'water_presence', 'green_space']:
                    context_parts.append(f"{key.replace('_', ' ').title()}: {scores[key]}")

            # Fallback: include any numeric score fields not covered above.
            for key, value in scores.items():
                if key in ['qi_flow', 'orientation', 'road_access', 'building_density', 'water_presence', 'green_space']:
                    continue
                if key in preferred_order:
                    continue
                if isinstance(value, (int, float)):
                    context_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Key issues and strengths (brief)
        if 'issues' in analysis_data:
            context_parts.append(f"Issues: {str(analysis_data['issues'])[:150]}")
        
        if 'strengths' in analysis_data:
            context_parts.append(f"Strengths: {str(analysis_data['strengths'])[:150]}")

        if 'features' in analysis_data:
            feature_blob = self._truncate_text(json.dumps(analysis_data['features'], ensure_ascii=False), 260)
            context_parts.append(f"Features: {feature_blob}")
        
        return "; ".join(context_parts)
    
    def _get_rating(self, score: float) -> str:
        """Convert numeric score to rating label."""
        try:
            score_value = float(score)
        except (TypeError, ValueError):
            return "Unknown"

        if score_value >= 80:
            return "Excellent"
        elif score_value >= 60:
            return "Good"
        elif score_value >= 40:
            return "Fair"
        elif score_value >= 20:
            return "Poor"
        else:
            return "Critical"
    
    def get_improvement_suggestions(
        self, 
        analysis_data: Dict[str, Any], 
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered improvement suggestions based on analysis data.
        
        Args:
            analysis_data: Complete feng shui analysis results
            user_query: Optional specific question from user
        
        Returns:
            Dict containing AI response and metadata
        """
        try:
            cache_key = self._cache_key(analysis_data, user_query)
            cached = self._get_cached_improve(cache_key)
            if cached:
                cached_copy = dict(cached)
                cached_copy['cached'] = True
                return cached_copy

            # Build the conversation
            messages = [
                {
                    "role": "system",
                    "content": self._build_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"{self._build_context_prompt(analysis_data)}\n\n" +
                              f"User Question: {user_query or 'How can I improve this location based on the analysis above?'}"
                }
            ]
            
            # Check if API key is configured
            if not self.api_key or self.api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
                return self._get_mock_response(analysis_data)
            
            # Make API request to DeepSeek
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300,
                "stream": False
            }
            
            logger.info(f"Sending request to DeepSeek API: {self.api_url}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_message = result['choices'][0]['message']['content']
                
                result_payload = {
                    'success': True,
                    'response': ai_message,
                    'model': self.model,
                    'usage': result.get('usage', {}),
                    'timestamp': result.get('created', None)
                }
                self._set_cached_improve(cache_key, result_payload)
                return result_payload
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'response': "I apologize, but I'm having trouble connecting to the AI service. Please try again later."
                }
        
        except requests.Timeout:
            logger.error("DeepSeek API timeout")
            return {
                'success': False,
                'error': 'timeout',
                'response': "The AI service timed out. Please try again."
            }
        except Exception as e:
            logger.error(f"Error in chatbot service: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'response': f"Error: {str(e)}"
            }
    
    def _get_mock_response(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a mock response when API key is not configured.
        For development and testing purposes.
        """
        scores = analysis_data.get('scores', {})
        qi_flow = scores.get('qi_flow', 0)
        
        mock_suggestions = f"""Based on your Feng Shui analysis (Qi Flow: {qi_flow}/100), here are my recommendations:

## 🎯 Quick Wins (Immediate Actions)

1. **Improve Entry Point Clarity**
   - Clear any obstacles blocking the main entrance
   - Add better signage or markers to define the entry
   - *Why*: Smooth Qi flow starts with an unobstructed entrance

2. **Enhance Natural Light**
   - Open curtains/blinds during peak hours
   - Clean windows for maximum light transmission
   - *Why*: Natural light activates positive Yang energy

## 🏗️ Medium-Term Improvements

1. **Create Visual Flow Pathways**
   - Arrange furniture/plants to guide movement
   - Remove clutter from high-traffic areas
   - *Why*: Continuous pathways prevent energy stagnation

2. **Balance Elements**
   - Add water features (fountains) if space allows
   - Introduce plants to increase Wood element
   - *Why*: Five Elements balance creates harmony

## 🌟 Long-Term Optimizations

1. **Modify Building Orientation Access**
   - Consider secondary entrance if main alignment is poor
   - Install reflective surfaces to redirect energy
   - *Why*: Proper orientation maximizes beneficial Qi

2. **Comprehensive Landscape Design**
   - Professional assessment of drainage patterns
   - Strategic placement of trees and structures
   - *Why*: External environment deeply affects internal energy

**Note:** This is a sample response. Configure your DeepSeek API key for personalized AI-powered recommendations.

**Next Steps:** Focus on the Quick Wins first, then reassess your space after 2-3 weeks."""
        
        return {
            'success': True,
            'response': mock_suggestions,
            'model': 'mock',
            'is_mock': True,
            'message': 'Using mock response. Add your DeepSeek API key for AI-powered suggestions.'
        }
    
    def chat(
        self, 
        message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        General chat interface with conversation history support.
        
        Args:
            message: User's message
            conversation_history: Previous messages in the conversation
            analysis_context: Optional analysis data for context
        
        Returns:
            Dict containing AI response
        """
        try:
            messages = [{"role": "system", "content": self._build_system_prompt()}]
            
            # Add analysis context if available
            if analysis_context:
                context_msg = f"Current Location Analysis:\n{self._build_context_prompt(analysis_context)}"
                messages.append({"role": "system", "content": context_msg})
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Check API key
            if not self.api_key or self.api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
                return {
                    'success': True,
                    'response': "I'd be happy to help! However, the DeepSeek API key hasn't been configured yet. Please add your API key to receive AI-powered feng shui advice.",
                    'is_mock': True
                }
            
            # Make API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 350,
                "stream": False
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result['choices'][0]['message']['content'],
                    'usage': result.get('usage', {})
                }
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'response': "I'm having trouble processing your request. Please try again."
                }
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'response': "An error occurred. Please try again."
            }


# Singleton instance
_chatbot_instance = None

def get_chatbot() -> FengShuiChatbot:
    """Get or create the singleton chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = FengShuiChatbot()
    return _chatbot_instance
