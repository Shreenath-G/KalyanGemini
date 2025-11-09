"""Audience Targeting Agent - Identifies optimal audience segments using Vertex AI"""

import logging
import asyncio
import uuid
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from vertexai.generative_models import GenerativeModel
import vertexai

from src.models.audience import AudienceSegment, Demographics, SegmentSize
from src.services.firestore import get_firestore_service
from src.config import settings

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "audience_targeting",
        correlation_id: Optional[str] = None
    ):
        self.message_type = message_type
        self.data = data
        self.sender = sender
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_type": self.message_type,
            "data": self.data,
            "sender": self.sender,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }


class AgentResponse:
    """Response structure from agent"""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        agent_name: str = "audience_targeting"
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.agent_name = agent_name
        self.timestamp = datetime.utcnow()


class AudienceTargetingAgent:
    """
    Audience Targeting Agent
    
    Identifies optimal audience segments using Vertex AI (Gemini) by:
    - Receiving campaign goals from Campaign Orchestrator Agent
    - Identifying 3+ distinct audience segments with demographics, interests, and behaviors
    - Estimating segment sizes and conversion probabilities
    - Prioritizing segments based on potential ROI
    - Persisting audience segments to Firestore
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Audience Targeting Agent with Vertex AI"""
        self.name = "audience_targeting"
        self.firestore_service = get_firestore_service()
        
        # Initialize Vertex AI
        try:
            vertexai.init(
                project=settings.google_cloud_project,
                location=settings.vertex_ai_location
            )
            
            # Initialize Gemini model
            self.model = GenerativeModel(settings.vertex_ai_model)
            
            logger.info(
                f"Audience Targeting Agent initialized with Vertex AI",
                extra={
                    "agent_name": self.name,
                    "project": settings.google_cloud_project,
                    "location": settings.vertex_ai_location,
                    "model": settings.vertex_ai_model
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize Vertex AI",
                extra={"error": str(e)}
            )
            raise
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """
        Handle incoming messages from other agents
        
        Supported message types:
        - identify_audiences: Identify audience segments for a campaign
        
        Args:
            message: Incoming agent message
            
        Returns:
            Agent response with identified segments or error
            
        Requirements: 4.1, 11.1, 11.2
        """
        logger.info(
            f"Handling message",
            extra={
                "message_type": message.message_type,
                "correlation_id": message.correlation_id,
                "sender": message.sender
            }
        )
        
        try:
            if message.message_type == "identify_audiences":
                return await self._handle_identify_audiences(message)
            else:
                logger.warning(
                    f"Unknown message type: {message.message_type}",
                    extra={"correlation_id": message.correlation_id}
                )
                return AgentResponse(
                    success=False,
                    error=f"Unknown message type: {message.message_type}"
                )
        
        except Exception as e:
            logger.error(
                f"Error handling message",
                extra={
                    "message_type": message.message_type,
                    "correlation_id": message.correlation_id,
                    "error": str(e)
                }
            )
            return AgentResponse(
                success=False,
                error=f"Error processing message: {str(e)}"
            )
    
    async def _handle_identify_audiences(self, message: AgentMessage) -> AgentResponse:
        """
        Handle identify_audiences message
        
        Args:
            message: Message with campaign data
            
        Returns:
            Response with identified audience segments
        """
        campaign_data = message.data
        campaign_id = campaign_data.get("campaign_id")
        
        logger.info(
            f"Identifying audiences for campaign",
            extra={
                "campaign_id": campaign_id,
                "correlation_id": message.correlation_id
            }
        )
        
        # Identify audience segments
        segments = await self.identify_segments(
            description=campaign_data.get("target_audience", "general audience"),
            product=campaign_data.get("products", ["product"])[0],
            business_goal=campaign_data.get("business_goal", "increase_sales")
        )
        
        # Enrich segments with size and conversion probability estimates
        enriched_segments = await self.enrich_segments(segments, campaign_data)
        
        # Prioritize segments by potential ROI
        prioritized_segments = self.prioritize_segments(enriched_segments)
        
        # Create AudienceSegment objects
        audience_segments = []
        for i, segment in enumerate(prioritized_segments):
            segment_obj = AudienceSegment(
                segment_id=f"seg_{campaign_id}_{i}_{uuid.uuid4().hex[:8]}",
                campaign_id=campaign_id,
                name=segment["name"],
                demographics=segment["demographics"],
                interests=segment["interests"],
                behaviors=segment["behaviors"],
                estimated_size=segment["estimated_size"],
                conversion_probability=segment["conversion_probability"],
                priority_score=segment["priority_score"]
            )
            audience_segments.append(segment_obj)
        
        # Persist to Firestore
        await self.persist_segments(audience_segments)
        
        logger.info(
            f"Identified and persisted {len(audience_segments)} audience segments",
            extra={
                "campaign_id": campaign_id,
                "segment_count": len(audience_segments),
                "correlation_id": message.correlation_id
            }
        )
        
        return AgentResponse(
            success=True,
            data={
                "segments": [s.model_dump() for s in audience_segments],
                "count": len(audience_segments)
            }
        )
    
    async def identify_segments(
        self,
        description: str,
        product: str,
        business_goal: str
    ) -> List[Dict[str, Any]]:
        """
        Identify audience segments using Vertex AI
        
        This method:
        1. Constructs a prompt for the LLM with campaign context
        2. Generates 3+ distinct audience segments
        3. Parses LLM response into structured format
        4. Returns segments with demographics, interests, and behaviors
        
        Args:
            description: Target audience description
            product: Product or service being advertised
            business_goal: Campaign business goal
            
        Returns:
            List of audience segment dictionaries
            
        Requirements: 4.1, 4.2, 4.3
        """
        logger.info(
            f"Identifying audience segments",
            extra={
                "product": product,
                "business_goal": business_goal
            }
        )
        
        # Format business goal for better readability
        goal_text = business_goal.replace("_", " ").title()
        
        # Build prompt for Vertex AI
        prompt = self._build_identification_prompt(
            description=description,
            product=product,
            business_goal=goal_text
        )
        
        try:
            # Generate content using Vertex AI
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Parse the response
            segments = self._parse_llm_response(response.text)
            
            # Ensure we have at least 3 segments
            if len(segments) < 3:
                logger.warning(
                    f"Generated fewer segments than required",
                    extra={
                        "required": 3,
                        "generated": len(segments)
                    }
                )
                # Add fallback segments if needed
                while len(segments) < 3:
                    segments.extend(self._generate_fallback_segments(product, goal_text))
                    segments = segments[:3]
            
            logger.info(
                f"Successfully identified {len(segments)} segments",
                extra={"product": product}
            )
            
            return segments
            
        except Exception as e:
            logger.error(
                f"Error identifying segments with Vertex AI",
                extra={"error": str(e), "product": product}
            )
            
            # Fallback to template-based generation
            logger.warning("Falling back to template-based segment generation")
            return self._generate_fallback_segments(product, goal_text)
    
    def _build_identification_prompt(
        self,
        description: str,
        product: str,
        business_goal: str
    ) -> str:
        """
        Build prompt for Vertex AI audience identification
        
        Args:
            description: Target audience description
            product: Product or service
            business_goal: Campaign goal
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert digital marketing strategist specializing in audience targeting. Identify 3-5 distinct and valuable audience segments for the following campaign:

Product/Service: {product}
Business Goal: {business_goal}
Target Audience Description: {description}

For each segment, provide:
1. Segment Name: A clear, descriptive name for the segment
2. Demographics:
   - Age Range (e.g., "25-40")
   - Gender (e.g., "all", "male", "female")
   - Income Range (e.g., "40k-100k", "100k+")
3. Interests: List 3-5 specific interest categories
4. Behaviors: List 2-4 behavioral patterns or characteristics
5. Estimated Size: Classify as "small" (<100k users), "medium" (100k-1M users), or "large" (>1M users)

Requirements:
- Make each segment distinct and non-overlapping
- Focus on segments most likely to convert for this product
- Consider demographics, psychographics, and behavioral patterns
- Ensure segments are actionable for digital advertising platforms
- Prioritize segments with high commercial intent

Format your response as follows:

SEGMENT 1:
Name: [Segment name]
Age Range: [age range]
Gender: [gender]
Income: [income range]
Interests: [interest1, interest2, interest3, ...]
Behaviors: [behavior1, behavior2, ...]
Size: [small/medium/large]

SEGMENT 2:
[continue same format...]

Generate at least 3 distinct segments following this format strictly.
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured audience segments
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            List of parsed audience segment dictionaries
        """
        segments = []
        
        # Split response into segment blocks
        segment_blocks = re.split(r'SEGMENT\s+\d+:', response_text, flags=re.IGNORECASE)
        
        for block in segment_blocks[1:]:  # Skip first empty split
            try:
                segment = self._parse_segment_block(block)
                if segment:
                    segments.append(segment)
            except Exception as e:
                logger.warning(
                    f"Failed to parse segment block",
                    extra={"error": str(e)}
                )
                continue
        
        return segments
    
    def _parse_segment_block(self, block: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single segment block from LLM response
        
        Args:
            block: Text block for one segment
            
        Returns:
            Parsed segment dictionary or None if parsing fails
        """
        # Extract fields using regex
        name_match = re.search(r'Name:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        age_match = re.search(r'Age\s+Range:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        gender_match = re.search(r'Gender:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        income_match = re.search(r'Income:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        interests_match = re.search(r'Interests:\s*(.+?)(?:\n|Behaviors:)', block, re.IGNORECASE | re.DOTALL)
        behaviors_match = re.search(r'Behaviors:\s*(.+?)(?:\n|Size:)', block, re.IGNORECASE | re.DOTALL)
        size_match = re.search(r'Size:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        
        if not all([name_match, age_match, interests_match]):
            return None
        
        # Extract and clean text
        name = name_match.group(1).strip()
        age_range = age_match.group(1).strip()
        gender = gender_match.group(1).strip() if gender_match else "all"
        income = income_match.group(1).strip() if income_match else None
        
        # Parse interests (comma or newline separated)
        interests_text = interests_match.group(1).strip()
        interests = [i.strip() for i in re.split(r'[,\n]', interests_text) if i.strip()]
        interests = [i.lstrip('-•*').strip() for i in interests]  # Remove bullet points
        interests = [i for i in interests if i and len(i) > 2][:5]  # Keep top 5
        
        # Parse behaviors
        behaviors = []
        if behaviors_match:
            behaviors_text = behaviors_match.group(1).strip()
            behaviors = [b.strip() for b in re.split(r'[,\n]', behaviors_text) if b.strip()]
            behaviors = [b.lstrip('-•*').strip() for b in behaviors]  # Remove bullet points
            behaviors = [b for b in behaviors if b and len(b) > 2][:4]  # Keep top 4
        
        # Parse size
        size_text = size_match.group(1).strip().lower() if size_match else "medium"
        if "small" in size_text:
            size = SegmentSize.SMALL
        elif "large" in size_text:
            size = SegmentSize.LARGE
        else:
            size = SegmentSize.MEDIUM
        
        return {
            "name": name,
            "demographics": Demographics(
                age_range=age_range,
                gender=gender,
                income=income
            ),
            "interests": interests if interests else ["general"],
            "behaviors": behaviors,
            "estimated_size": size
        }
    
    def _generate_fallback_segments(
        self,
        product: str,
        business_goal: str
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback segments using templates
        
        Args:
            product: Product or service
            business_goal: Campaign goal
            
        Returns:
            List of template-based segments
        """
        segments = [
            {
                "name": f"Early Adopters - {product}",
                "demographics": Demographics(
                    age_range="25-40",
                    gender="all",
                    income="60k-120k"
                ),
                "interests": ["technology", "innovation", "productivity", "business tools"],
                "behaviors": ["early technology adoption", "online research", "software trials"],
                "estimated_size": SegmentSize.MEDIUM
            },
            {
                "name": f"Budget-Conscious Professionals",
                "demographics": Demographics(
                    age_range="30-50",
                    gender="all",
                    income="40k-80k"
                ),
                "interests": ["cost savings", "efficiency", "value", "practical solutions"],
                "behaviors": ["price comparison", "review reading", "deal seeking"],
                "estimated_size": SegmentSize.LARGE
            },
            {
                "name": f"Enterprise Decision Makers",
                "demographics": Demographics(
                    age_range="35-55",
                    gender="all",
                    income="100k+"
                ),
                "interests": ["business growth", "scalability", "ROI", "enterprise solutions"],
                "behaviors": ["B2B purchasing", "vendor evaluation", "long-term planning"],
                "estimated_size": SegmentSize.SMALL
            }
        ]
        
        return segments
    
    async def enrich_segments(
        self,
        segments: List[Dict[str, Any]],
        campaign_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Enrich segments with estimated conversion probabilities
        
        This method estimates conversion probability for each segment based on:
        - Segment characteristics
        - Product fit
        - Business goal alignment
        
        Args:
            segments: List of identified segments
            campaign_data: Campaign context data
            
        Returns:
            List of enriched segments with conversion_probability
            
        Requirements: 4.2, 4.3
        """
        logger.info(f"Enriching {len(segments)} segments with conversion estimates")
        
        enriched = []
        for segment in segments:
            # Estimate conversion probability based on segment characteristics
            conversion_prob = self._estimate_conversion_probability(
                segment=segment,
                product=campaign_data.get("products", ["product"])[0],
                business_goal=campaign_data.get("business_goal", "increase_sales")
            )
            
            segment["conversion_probability"] = conversion_prob
            enriched.append(segment)
            
            logger.debug(
                f"Enriched segment",
                extra={
                    "segment_name": segment["name"],
                    "conversion_probability": conversion_prob
                }
            )
        
        return enriched
    
    def _estimate_conversion_probability(
        self,
        segment: Dict[str, Any],
        product: str,
        business_goal: str
    ) -> float:
        """
        Estimate conversion probability for a segment
        
        Uses heuristics based on:
        - Segment size (smaller = more targeted = higher conversion)
        - Interest relevance
        - Behavioral signals
        
        Args:
            segment: Segment data
            product: Product name
            business_goal: Campaign goal
            
        Returns:
            Conversion probability between 0.0 and 1.0
        """
        base_probability = 0.08  # 8% base conversion rate
        
        # Adjust based on segment size (smaller = more targeted)
        size = segment.get("estimated_size", SegmentSize.MEDIUM)
        if size == SegmentSize.SMALL:
            size_multiplier = 1.5  # Small segments are more targeted
        elif size == SegmentSize.LARGE:
            size_multiplier = 0.8  # Large segments are broader
        else:
            size_multiplier = 1.0
        
        # Adjust based on behavioral signals
        behaviors = segment.get("behaviors", [])
        behavior_boost = 0.0
        high_intent_behaviors = [
            "purchase", "buying", "shopping", "research", "comparison",
            "trial", "demo", "evaluation", "seeking", "looking for"
        ]
        
        for behavior in behaviors:
            behavior_lower = behavior.lower()
            if any(intent in behavior_lower for intent in high_intent_behaviors):
                behavior_boost += 0.02
        
        # Calculate final probability
        probability = base_probability * size_multiplier + behavior_boost
        
        # Ensure probability is between 0.05 and 0.25 (5% to 25%)
        probability = max(0.05, min(0.25, probability))
        
        return round(probability, 3)

    def prioritize_segments(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize segments based on potential ROI
        
        This method:
        1. Calculates priority scores combining size and conversion probability
        2. Sorts segments by potential ROI
        3. Returns prioritized segment list
        
        Priority score calculation:
        - Combines segment size (reach) with conversion probability (quality)
        - Weights conversion probability higher (70%) than size (30%)
        - Higher scores indicate better potential ROI
        
        Args:
            segments: List of enriched segments
            
        Returns:
            List of segments sorted by priority score (highest first)
            
        Requirements: 4.4, 4.5
        """
        logger.info(f"Prioritizing {len(segments)} segments")
        
        prioritized = []
        for segment in segments:
            priority_score = self._calculate_priority_score(segment)
            segment["priority_score"] = priority_score
            prioritized.append(segment)
            
            logger.debug(
                f"Calculated priority score",
                extra={
                    "segment_name": segment["name"],
                    "priority_score": priority_score,
                    "conversion_probability": segment.get("conversion_probability", 0.0),
                    "estimated_size": segment.get("estimated_size", "unknown")
                }
            )
        
        # Sort by priority score (highest first)
        prioritized.sort(key=lambda s: s["priority_score"], reverse=True)
        
        logger.info(
            f"Segments prioritized",
            extra={
                "top_segment": prioritized[0]["name"] if prioritized else None,
                "top_score": prioritized[0]["priority_score"] if prioritized else None
            }
        )
        
        return prioritized
    
    def _calculate_priority_score(self, segment: Dict[str, Any]) -> float:
        """
        Calculate priority score for a segment
        
        Formula:
        - Priority = (conversion_probability * 0.7) + (size_score * 0.3)
        - Size scores: small=0.6, medium=0.8, large=1.0
        - Weights conversion quality (70%) over reach (30%)
        
        Args:
            segment: Segment data with conversion_probability and estimated_size
            
        Returns:
            Priority score between 0.0 and 1.0
        """
        conversion_prob = segment.get("conversion_probability", 0.08)
        size = segment.get("estimated_size", SegmentSize.MEDIUM)
        
        # Convert size to numeric score
        if size == SegmentSize.SMALL:
            size_score = 0.6  # Smaller reach but more targeted
        elif size == SegmentSize.LARGE:
            size_score = 1.0  # Larger reach
        else:  # MEDIUM
            size_score = 0.8
        
        # Calculate weighted priority score
        # Weight conversion probability higher (70%) than size (30%)
        priority = (conversion_prob * 0.7) + (size_score * 0.3)
        
        # Normalize to 0-1 range
        # Max possible: (0.25 * 0.7) + (1.0 * 0.3) = 0.475
        # We'll scale to make high performers reach ~0.9
        priority = min(1.0, priority * 2.0)
        
        return round(priority, 3)

    async def persist_segments(self, segments: List[AudienceSegment]) -> List[str]:
        """
        Persist audience segments to Firestore
        
        This method:
        1. Saves generated segments using FirestoreService.batch_create_segments
        2. Updates campaign with audience_segments references
        
        Args:
            segments: List of AudienceSegment objects to persist
            
        Returns:
            List of segment IDs that were persisted
            
        Requirements: 4.1, 13.1
        """
        if not segments:
            logger.warning("No segments to persist")
            return []
        
        campaign_id = segments[0].campaign_id
        
        logger.info(
            f"Persisting {len(segments)} segments to Firestore",
            extra={
                "campaign_id": campaign_id,
                "segment_count": len(segments)
            }
        )
        
        try:
            # Batch create segments in Firestore
            segment_ids = await self.firestore_service.batch_create_segments(segments)
            
            # Update campaign with audience_segments references
            # Get existing campaign data
            campaign = await self.firestore_service.get_campaign(campaign_id)
            
            if campaign:
                # Prepare segment references for campaign
                segment_refs = [s.model_dump() for s in segments]
                
                # Update campaign with new segments
                existing_segments = campaign.audience_segments or []
                updated_segments = existing_segments + segment_refs
                
                await self.firestore_service.update_campaign(
                    campaign_id,
                    {"audience_segments": updated_segments}
                )
                
                logger.info(
                    f"Successfully persisted segments and updated campaign",
                    extra={
                        "campaign_id": campaign_id,
                        "segment_ids": segment_ids,
                        "total_segments": len(updated_segments)
                    }
                )
            else:
                logger.warning(
                    f"Campaign not found, segments persisted but campaign not updated",
                    extra={"campaign_id": campaign_id}
                )
            
            return segment_ids
            
        except Exception as e:
            logger.error(
                f"Error persisting segments to Firestore",
                extra={
                    "campaign_id": campaign_id,
                    "segment_count": len(segments),
                    "error": str(e)
                }
            )
            raise



# Global agent instance
_agent_instance: Optional[AudienceTargetingAgent] = None


def get_audience_targeting_agent() -> AudienceTargetingAgent:
    """Get or create the global Audience Targeting Agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AudienceTargetingAgent()
    return _agent_instance
