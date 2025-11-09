"""Creative Generator Agent - Generates ad copy variations using Vertex AI"""

import logging
import asyncio
import uuid
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from vertexai.generative_models import GenerativeModel
import vertexai

from src.models.creative import CreativeVariant, CreativeHeadlines, CreativeStatus
from src.services.firestore import get_firestore_service
from src.config import settings

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "creative_generator",
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
        agent_name: str = "creative_generator"
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.agent_name = agent_name
        self.timestamp = datetime.utcnow()


class CreativeGeneratorAgent:
    """
    Creative Generator Agent
    
    Generates ad copy variations using Vertex AI (Gemini) by:
    - Receiving campaign briefs from Campaign Orchestrator Agent
    - Generating 5+ distinct ad copy variations with headlines, body, and CTAs
    - Validating compliance with advertising platform policies
    - Persisting validated creative variants to Firestore
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Creative Generator Agent with Vertex AI"""
        self.name = "creative_generator"
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
                f"Creative Generator Agent initialized with Vertex AI",
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
        - generate_creatives: Generate creative variations for a campaign
        - generate_new_variants: Generate new variants for optimization
        
        Args:
            message: Incoming agent message
            
        Returns:
            Agent response with generated creatives or error
            
        Requirements: 3.1, 11.1, 11.2
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
            if message.message_type == "generate_creatives":
                return await self._handle_generate_creatives(message)
            elif message.message_type == "generate_new_variants":
                return await self._handle_generate_new_variants(message)
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
    
    async def _handle_generate_creatives(self, message: AgentMessage) -> AgentResponse:
        """
        Handle generate_creatives message
        
        Args:
            message: Message with campaign data
            
        Returns:
            Response with generated creative variations
        """
        campaign_data = message.data
        campaign_id = campaign_data.get("campaign_id")
        
        logger.info(
            f"Generating creatives for campaign",
            extra={
                "campaign_id": campaign_id,
                "correlation_id": message.correlation_id
            }
        )
        
        # Generate creative variations
        variations = await self.generate_variations(
            product=campaign_data.get("products", ["product"])[0],
            business_goal=campaign_data.get("business_goal", "increase_sales"),
            target_audience=campaign_data.get("target_audience", "general audience"),
            count=5
        )
        
        # Validate compliance
        validated_variations = self.validate_compliance(variations)
        
        # Create CreativeVariant objects
        creative_variants = []
        for i, variation in enumerate(validated_variations):
            variant = CreativeVariant(
                variant_id=f"var_{campaign_id}_{i}_{uuid.uuid4().hex[:8]}",
                campaign_id=campaign_id,
                status=CreativeStatus.TESTING,
                headlines=variation["headlines"],
                body=variation["body"],
                cta=variation["cta"],
                compliance_score=variation["compliance_score"]
            )
            creative_variants.append(variant)
        
        # Persist to Firestore
        await self.persist_variants(creative_variants)
        
        logger.info(
            f"Generated and persisted {len(creative_variants)} creative variants",
            extra={
                "campaign_id": campaign_id,
                "variant_count": len(creative_variants),
                "correlation_id": message.correlation_id
            }
        )
        
        return AgentResponse(
            success=True,
            data={
                "variations": [v.model_dump() for v in creative_variants],
                "count": len(creative_variants)
            }
        )
    
    async def _handle_generate_new_variants(self, message: AgentMessage) -> AgentResponse:
        """
        Handle generate_new_variants message for optimization
        
        Args:
            message: Message with campaign data and existing variants
            
        Returns:
            Response with new creative variations
        """
        campaign_data = message.data
        campaign_id = campaign_data.get("campaign_id")
        existing_variants = campaign_data.get("existing_variants", [])
        
        logger.info(
            f"Generating new variants for optimization",
            extra={
                "campaign_id": campaign_id,
                "existing_count": len(existing_variants),
                "correlation_id": message.correlation_id
            }
        )
        
        # Generate new variations with context of existing ones
        variations = await self.generate_variations(
            product=campaign_data.get("products", ["product"])[0],
            business_goal=campaign_data.get("business_goal", "increase_sales"),
            target_audience=campaign_data.get("target_audience", "general audience"),
            count=3,
            avoid_similar_to=existing_variants
        )
        
        # Validate compliance
        validated_variations = self.validate_compliance(variations)
        
        # Create CreativeVariant objects
        creative_variants = []
        for i, variation in enumerate(validated_variations):
            variant = CreativeVariant(
                variant_id=f"var_{campaign_id}_opt_{i}_{uuid.uuid4().hex[:8]}",
                campaign_id=campaign_id,
                status=CreativeStatus.TESTING,
                headlines=variation["headlines"],
                body=variation["body"],
                cta=variation["cta"],
                compliance_score=variation["compliance_score"]
            )
            creative_variants.append(variant)
        
        # Persist to Firestore
        await self.persist_variants(creative_variants)
        
        logger.info(
            f"Generated {len(creative_variants)} new optimization variants",
            extra={
                "campaign_id": campaign_id,
                "variant_count": len(creative_variants),
                "correlation_id": message.correlation_id
            }
        )
        
        return AgentResponse(
            success=True,
            data={
                "variations": [v.model_dump() for v in creative_variants],
                "count": len(creative_variants),
                "applied_actions": [
                    {
                        "type": "generate_new_variants",
                        "success": True,
                        "variant_count": len(creative_variants)
                    }
                ]
            }
        )

    async def generate_variations(
        self,
        product: str,
        business_goal: str,
        target_audience: str = "general audience",
        count: int = 5,
        avoid_similar_to: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate creative variations using Vertex AI
        
        This method:
        1. Constructs a prompt for the LLM with campaign context
        2. Generates multiple ad copy variations
        3. Parses LLM response into structured format
        4. Ensures variations align with campaign objectives
        
        Args:
            product: Product or service being advertised
            business_goal: Campaign business goal (e.g., "increase_sales")
            target_audience: Description of target audience
            count: Number of variations to generate (default: 5)
            avoid_similar_to: Existing variants to avoid similarity with
            
        Returns:
            List of creative variation dictionaries with headlines, body, and CTA
            
        Requirements: 3.1, 3.2, 3.3
        """
        logger.info(
            f"Generating {count} creative variations",
            extra={
                "product": product,
                "business_goal": business_goal,
                "target_audience": target_audience
            }
        )
        
        # Format business goal for better readability
        goal_text = business_goal.replace("_", " ").title()
        
        # Build prompt for Vertex AI
        prompt = self._build_generation_prompt(
            product=product,
            business_goal=goal_text,
            target_audience=target_audience,
            count=count,
            avoid_similar_to=avoid_similar_to
        )
        
        try:
            # Generate content using Vertex AI
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Parse the response
            variations = self._parse_llm_response(response.text)
            
            # Ensure we have at least the requested count
            if len(variations) < count:
                logger.warning(
                    f"Generated fewer variations than requested",
                    extra={
                        "requested": count,
                        "generated": len(variations)
                    }
                )
            
            logger.info(
                f"Successfully generated {len(variations)} variations",
                extra={"product": product}
            )
            
            return variations[:count]  # Return exactly the requested count
            
        except Exception as e:
            logger.error(
                f"Error generating variations with Vertex AI",
                extra={"error": str(e), "product": product}
            )
            
            # Fallback to template-based generation
            logger.warning("Falling back to template-based generation")
            return self._generate_template_variations(
                product=product,
                business_goal=goal_text,
                count=count
            )
    
    def _build_generation_prompt(
        self,
        product: str,
        business_goal: str,
        target_audience: str,
        count: int,
        avoid_similar_to: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build prompt for Vertex AI creative generation
        
        Args:
            product: Product or service
            business_goal: Campaign goal
            target_audience: Target audience description
            count: Number of variations
            avoid_similar_to: Existing variants to avoid
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert advertising copywriter. Generate {count} distinct and compelling ad copy variations for the following campaign:

Product/Service: {product}
Business Goal: {business_goal}
Target Audience: {target_audience}

For each variation, provide:
1. Three headlines of different lengths:
   - Short headline (exactly 30 characters or less)
   - Medium headline (exactly 60 characters or less)
   - Long headline (exactly 90 characters or less)
2. Body copy (exactly 150 characters or less)
3. Call-to-action (exactly 20 characters or less)

Requirements:
- Make each variation unique and distinct from the others
- Align messaging with the business goal
- Use persuasive, action-oriented language
- Avoid prohibited terms (e.g., "guaranteed", "miracle", "free money")
- Avoid excessive punctuation (max 2 exclamation marks per variation)
- Keep tone professional yet engaging
- Focus on benefits and value proposition

"""
        
        if avoid_similar_to:
            prompt += "\nAvoid creating variations similar to these existing ones:\n"
            for i, existing in enumerate(avoid_similar_to[:3], 1):  # Show max 3 examples
                if isinstance(existing, dict):
                    headlines = existing.get("headlines", {})
                    if isinstance(headlines, dict):
                        prompt += f"{i}. {headlines.get('medium', 'N/A')}\n"
        
        prompt += f"""
Format your response as follows for each variation:

VARIATION 1:
Short: [30 char headline]
Medium: [60 char headline]
Long: [90 char headline]
Body: [150 char body copy]
CTA: [20 char call-to-action]

VARIATION 2:
[continue same format...]

Generate exactly {count} variations following this format strictly.
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured creative variations
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            List of parsed creative variation dictionaries
        """
        variations = []
        
        # Split response into variation blocks
        variation_blocks = re.split(r'VARIATION\s+\d+:', response_text, flags=re.IGNORECASE)
        
        for block in variation_blocks[1:]:  # Skip first empty split
            try:
                variation = self._parse_variation_block(block)
                if variation:
                    variations.append(variation)
            except Exception as e:
                logger.warning(
                    f"Failed to parse variation block",
                    extra={"error": str(e)}
                )
                continue
        
        return variations
    
    def _parse_variation_block(self, block: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single variation block from LLM response
        
        Args:
            block: Text block for one variation
            
        Returns:
            Parsed variation dictionary or None if parsing fails
        """
        # Extract fields using regex
        short_match = re.search(r'Short:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        medium_match = re.search(r'Medium:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        long_match = re.search(r'Long:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        body_match = re.search(r'Body:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        cta_match = re.search(r'CTA:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        
        if not all([short_match, medium_match, long_match, body_match, cta_match]):
            return None
        
        # Extract and clean text
        short = short_match.group(1).strip()[:30]
        medium = medium_match.group(1).strip()[:60]
        long = long_match.group(1).strip()[:90]
        body = body_match.group(1).strip()[:150]
        cta = cta_match.group(1).strip()[:20]
        
        return {
            "headlines": CreativeHeadlines(
                short=short,
                medium=medium,
                long=long
            ),
            "body": body,
            "cta": cta
        }
    
    def _generate_template_variations(
        self,
        product: str,
        business_goal: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate template-based variations as fallback
        
        Args:
            product: Product or service
            business_goal: Campaign goal
            count: Number of variations
            
        Returns:
            List of template-based variations
        """
        templates = [
            {
                "short": f"{business_goal} Now",
                "medium": f"{business_goal} with {product}",
                "long": f"Achieve {business_goal} with {product} - Start Today",
                "body": f"Transform your business with {product}. Easy setup, powerful results, proven success.",
                "cta": "Get Started"
            },
            {
                "short": f"Try {product}",
                "medium": f"Discover {product} - {business_goal}",
                "long": f"Unlock Your Potential: {business_goal} with {product}",
                "body": f"Join thousands who achieved {business_goal}. {product} makes it simple and effective.",
                "cta": "Start Free Trial"
            },
            {
                "short": f"{product} Works",
                "medium": f"Real Results with {product}",
                "long": f"See Real Results: {business_goal} Made Easy with {product}",
                "body": f"No complexity, just results. {product} helps you {business_goal} faster than ever.",
                "cta": "Learn More"
            },
            {
                "short": f"Save Time Today",
                "medium": f"{product}: Your Path to {business_goal}",
                "long": f"Stop Struggling: {business_goal} is Easier with {product}",
                "body": f"Streamline your workflow and {business_goal}. {product} delivers what you need.",
                "cta": "See How"
            },
            {
                "short": f"Join Us Now",
                "medium": f"Trusted Solution for {business_goal}",
                "long": f"Trusted by Thousands: {product} Helps You {business_goal}",
                "body": f"Don't miss out on the tool that's changing how businesses {business_goal}.",
                "cta": "Sign Up Free"
            }
        ]
        
        variations = []
        for i in range(min(count, len(templates))):
            template = templates[i]
            variations.append({
                "headlines": CreativeHeadlines(
                    short=template["short"][:30],
                    medium=template["medium"][:60],
                    long=template["long"][:90]
                ),
                "body": template["body"][:150],
                "cta": template["cta"][:20]
            })
        
        return variations
    
    def validate_compliance(self, variations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate creative variations for compliance with advertising platform policies
        
        This method:
        1. Checks for prohibited terms
        2. Validates character limits
        3. Checks for excessive punctuation
        4. Assigns compliance scores
        5. Filters out non-compliant variations
        
        Args:
            variations: List of creative variation dictionaries
            
        Returns:
            List of validated variations with compliance scores
            
        Requirements: 3.4, 3.5
        """
        logger.info(
            f"Validating compliance for {len(variations)} variations"
        )
        
        validated_variations = []
        
        for variation in variations:
            compliance_score = self._calculate_compliance_score(variation)
            
            # Only include variations with compliance score >= 0.7
            if compliance_score >= 0.7:
                variation["compliance_score"] = compliance_score
                validated_variations.append(variation)
                
                logger.debug(
                    f"Variation passed compliance",
                    extra={"compliance_score": compliance_score}
                )
            else:
                logger.warning(
                    f"Variation failed compliance check",
                    extra={
                        "compliance_score": compliance_score,
                        "body": variation.get("body", "")[:50]
                    }
                )
        
        logger.info(
            f"Compliance validation complete",
            extra={
                "input_count": len(variations),
                "validated_count": len(validated_variations),
                "filtered_count": len(variations) - len(validated_variations)
            }
        )
        
        return validated_variations
    
    def _calculate_compliance_score(self, variation: Dict[str, Any]) -> float:
        """
        Calculate compliance score for a creative variation
        
        Checks:
        - Prohibited terms
        - Character limits
        - Excessive punctuation
        - Required fields
        
        Args:
            variation: Creative variation dictionary
            
        Returns:
            Compliance score between 0.0 and 1.0
        """
        score = 1.0
        penalties = []
        
        # Extract content
        headlines = variation.get("headlines")
        body = variation.get("body", "")
        cta = variation.get("cta", "")
        
        # Check if headlines is CreativeHeadlines object or dict
        if isinstance(headlines, CreativeHeadlines):
            short = headlines.short
            medium = headlines.medium
            long = headlines.long
        elif isinstance(headlines, dict):
            short = headlines.get("short", "")
            medium = headlines.get("medium", "")
            long = headlines.get("long", "")
        else:
            # Missing headlines - major penalty
            penalties.append(("missing_headlines", 0.5))
            short = medium = long = ""
        
        # Combine all text for prohibited term checking
        all_text = f"{short} {medium} {long} {body} {cta}".lower()
        
        # Check for prohibited terms
        prohibited_terms = [
            "guaranteed", "guarantee", "miracle", "free money",
            "get rich quick", "no risk", "100% effective",
            "cure", "medical breakthrough", "secret formula",
            "limited time only", "act now", "don't wait",
            "click here", "buy now", "order now"
        ]
        
        for term in prohibited_terms:
            if term in all_text:
                penalties.append((f"prohibited_term_{term}", 0.1))
        
        # Check for excessive punctuation
        exclamation_count = all_text.count("!")
        if exclamation_count > 2:
            penalties.append(("excessive_exclamation", 0.15))
        
        question_count = all_text.count("?")
        if question_count > 2:
            penalties.append(("excessive_questions", 0.1))
        
        # Check character limits
        if len(short) > 30:
            penalties.append(("short_headline_too_long", 0.2))
        
        if len(medium) > 60:
            penalties.append(("medium_headline_too_long", 0.2))
        
        if len(long) > 90:
            penalties.append(("long_headline_too_long", 0.2))
        
        if len(body) > 150:
            penalties.append(("body_too_long", 0.2))
        
        if len(cta) > 20:
            penalties.append(("cta_too_long", 0.2))
        
        # Check for empty required fields
        if not short or not medium or not long:
            penalties.append(("missing_headline", 0.3))
        
        if not body:
            penalties.append(("missing_body", 0.3))
        
        if not cta:
            penalties.append(("missing_cta", 0.3))
        
        # Check for all caps (shouting)
        if short.isupper() or medium.isupper() or long.isupper():
            penalties.append(("all_caps_headline", 0.1))
        
        # Apply penalties
        for penalty_type, penalty_value in penalties:
            score -= penalty_value
            logger.debug(
                f"Compliance penalty applied",
                extra={
                    "penalty_type": penalty_type,
                    "penalty_value": penalty_value
                }
            )
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score
    
    async def persist_variants(self, variants: List[CreativeVariant]) -> List[str]:
        """
        Persist creative variants to Firestore
        
        This method:
        1. Saves generated variants using FirestoreService.batch_create_variants
        2. Updates campaign with creative_variants references
        
        Args:
            variants: List of CreativeVariant objects to persist
            
        Returns:
            List of variant IDs that were persisted
            
        Requirements: 3.1, 13.1
        """
        if not variants:
            logger.warning("No variants to persist")
            return []
        
        campaign_id = variants[0].campaign_id
        
        logger.info(
            f"Persisting {len(variants)} variants to Firestore",
            extra={
                "campaign_id": campaign_id,
                "variant_count": len(variants)
            }
        )
        
        try:
            # Batch create variants in Firestore
            variant_ids = await self.firestore_service.batch_create_variants(variants)
            
            # Update campaign with creative_variants references
            # Get existing campaign data
            campaign = await self.firestore_service.get_campaign(campaign_id)
            
            if campaign:
                # Prepare variant references for campaign
                variant_refs = [v.model_dump() for v in variants]
                
                # Update campaign with new variants
                existing_variants = campaign.creative_variants or []
                updated_variants = existing_variants + variant_refs
                
                await self.firestore_service.update_campaign(
                    campaign_id,
                    {"creative_variants": updated_variants}
                )
                
                logger.info(
                    f"Successfully persisted variants and updated campaign",
                    extra={
                        "campaign_id": campaign_id,
                        "variant_ids": variant_ids,
                        "total_variants": len(updated_variants)
                    }
                )
            else:
                logger.warning(
                    f"Campaign not found, variants persisted but campaign not updated",
                    extra={"campaign_id": campaign_id}
                )
            
            return variant_ids
            
        except Exception as e:
            logger.error(
                f"Error persisting variants to Firestore",
                extra={
                    "campaign_id": campaign_id,
                    "variant_count": len(variants),
                    "error": str(e)
                }
            )
            raise


# Global agent instance
_agent_instance: Optional[CreativeGeneratorAgent] = None


def get_creative_generator_agent() -> CreativeGeneratorAgent:
    """Get or create the global Creative Generator Agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CreativeGeneratorAgent()
    return _agent_instance
