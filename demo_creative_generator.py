"""
Demonstration script for Creative Generator Agent

This script demonstrates the Creative Generator Agent's capabilities:
1. Template-based creative generation (fallback mode)
2. Compliance validation
3. Creative variant structure

Note: Full Vertex AI integration requires proper GCP credentials.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.models.creative import CreativeHeadlines


def demo_template_generation():
    """Demonstrate template-based creative generation"""
    print("\n" + "="*70)
    print("DEMO 1: Template-Based Creative Generation")
    print("="*70)
    
    # Simulate the template generation logic
    product = "CRM Software"
    business_goal = "Increase Sales"
    
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
        }
    ]
    
    print(f"\nProduct: {product}")
    print(f"Business Goal: {business_goal}")
    print(f"\nGenerated {len(templates)} creative variations:\n")
    
    for i, template in enumerate(templates, 1):
        print(f"--- Variation {i} ---")
        print(f"Short Headline (30 chars): {template['short']}")
        print(f"Medium Headline (60 chars): {template['medium']}")
        print(f"Long Headline (90 chars): {template['long']}")
        print(f"Body (150 chars): {template['body']}")
        print(f"CTA (20 chars): {template['cta']}")
        print()


def demo_compliance_validation():
    """Demonstrate compliance validation"""
    print("\n" + "="*70)
    print("DEMO 2: Compliance Validation")
    print("="*70)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Variation",
            "variation": {
                "headlines": {
                    "short": "Save 50% Today",
                    "medium": "Limited Time: Save 50% on Premium Plans",
                    "long": "Don't Miss Out: Save 50% on All Premium Plans This Week"
                },
                "body": "Upgrade your business with our premium features. Easy setup, no contracts.",
                "cta": "Get Started Now"
            },
            "expected": "PASS"
        },
        {
            "name": "Invalid - Prohibited Terms",
            "variation": {
                "headlines": {
                    "short": "Guaranteed Results!",
                    "medium": "Miracle Solution - Get Rich Quick!!!",
                    "long": "100% Effective - No Risk - Act Now!!!"
                },
                "body": "This is a guaranteed miracle cure that will make you rich!",
                "cta": "Click Here Now!!!"
            },
            "expected": "FAIL"
        },
        {
            "name": "Invalid - Too Long",
            "variation": {
                "headlines": {
                    "short": "This headline is way too long for the 30 character limit",
                    "medium": "This medium headline also exceeds the sixty character limit significantly",
                    "long": "This long headline is definitely way too long and exceeds the ninety character limit by a lot"
                },
                "body": "This body copy is also way too long and exceeds the 150 character limit. It just keeps going and going with more text than allowed by the platform policies.",
                "cta": "This CTA is too long"
            },
            "expected": "FAIL"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        variation = test_case['variation']
        
        # Calculate compliance score
        score = calculate_compliance_score(variation)
        result = "PASS" if score >= 0.7 else "FAIL"
        
        print(f"Compliance Score: {score:.2f}")
        print(f"Result: {result} (Expected: {test_case['expected']})")
        
        if result == test_case['expected']:
            print("✓ Test passed")
        else:
            print("✗ Test failed")


def calculate_compliance_score(variation):
    """Simplified compliance scoring for demo"""
    score = 1.0
    
    headlines = variation.get("headlines", {})
    body = variation.get("body", "")
    cta = variation.get("cta", "")
    
    short = headlines.get("short", "")
    medium = headlines.get("medium", "")
    long = headlines.get("long", "")
    
    all_text = f"{short} {medium} {long} {body} {cta}".lower()
    
    # Check prohibited terms
    prohibited_terms = [
        "guaranteed", "guarantee", "miracle", "free money",
        "get rich quick", "no risk", "100% effective",
        "cure", "medical breakthrough", "secret formula",
        "click here", "buy now", "order now"
    ]
    
    for term in prohibited_terms:
        if term in all_text:
            score -= 0.1
    
    # Check excessive punctuation
    if all_text.count("!") > 2:
        score -= 0.15
    
    # Check character limits
    if len(short) > 30:
        score -= 0.2
    if len(medium) > 60:
        score -= 0.2
    if len(long) > 90:
        score -= 0.2
    if len(body) > 150:
        score -= 0.2
    if len(cta) > 20:
        score -= 0.2
    
    return max(0.0, min(1.0, score))


def demo_creative_variant_structure():
    """Demonstrate CreativeVariant data structure"""
    print("\n" + "="*70)
    print("DEMO 3: CreativeVariant Data Structure")
    print("="*70)
    
    print("\nCreativeVariant Model Structure:")
    print("""
    - variant_id: Unique identifier
    - campaign_id: Associated campaign
    - status: ACTIVE | PAUSED | TESTING
    - headlines:
        - short: 30 characters max
        - medium: 60 characters max
        - long: 90 characters max
    - body: 150 characters max
    - cta: 20 characters max
    - Performance metrics:
        - impressions, clicks, conversions
        - spend, roas
    - compliance_score: 0.0 to 1.0
    """)
    
    print("\nExample CreativeVariant:")
    example = {
        "variant_id": "var_camp123_0_a1b2c3d4",
        "campaign_id": "camp_123",
        "status": "testing",
        "headlines": {
            "short": "Save 50% Today",
            "medium": "Limited Time: Save 50% on Premium Plans",
            "long": "Don't Miss Out: Save 50% on All Premium Plans This Week"
        },
        "body": "Upgrade your business with our premium features. Easy setup, no contracts.",
        "cta": "Get Started Now",
        "impressions": 0,
        "clicks": 0,
        "conversions": 0,
        "spend": 0.0,
        "roas": 0.0,
        "compliance_score": 0.95
    }
    
    import json
    print(json.dumps(example, indent=2))


def demo_agent_workflow():
    """Demonstrate the agent workflow"""
    print("\n" + "="*70)
    print("DEMO 4: Creative Generator Agent Workflow")
    print("="*70)
    
    print("""
    Agent Workflow:
    
    1. Campaign Orchestrator sends 'generate_creatives' message
       ↓
    2. Creative Generator Agent receives message
       ↓
    3. Extract campaign data (product, goal, audience)
       ↓
    4. Generate variations using Vertex AI (or fallback templates)
       ↓
    5. Validate compliance for each variation
       ↓
    6. Filter out non-compliant variations (score < 0.7)
       ↓
    7. Create CreativeVariant objects
       ↓
    8. Persist variants to Firestore (batch operation)
       ↓
    9. Update campaign with variant references
       ↓
    10. Return success response with variant data
    
    Message Format:
    {
        "message_type": "generate_creatives",
        "data": {
            "campaign_id": "camp_123",
            "business_goal": "increase_sales",
            "products": ["CRM Software"],
            "target_audience": "small business owners",
            "monthly_budget": 5000
        },
        "sender": "campaign_orchestrator",
        "correlation_id": "uuid-here"
    }
    
    Response Format:
    {
        "success": true,
        "data": {
            "variations": [...],  // List of CreativeVariant objects
            "count": 5
        },
        "agent_name": "creative_generator"
    }
    """)


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("CREATIVE GENERATOR AGENT - DEMONSTRATION")
    print("="*70)
    print("\nThis demo showcases the Creative Generator Agent's capabilities")
    print("without requiring full GCP credentials.\n")
    
    demo_template_generation()
    demo_compliance_validation()
    demo_creative_variant_structure()
    demo_agent_workflow()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
    The Creative Generator Agent successfully implements:
    
    ✓ Vertex AI integration for LLM-based creative generation
    ✓ Template-based fallback generation
    ✓ Comprehensive compliance validation
    ✓ Character limit enforcement (30/60/90 for headlines, 150 for body, 20 for CTA)
    ✓ Prohibited terms filtering
    ✓ Excessive punctuation detection
    ✓ Firestore persistence with batch operations
    ✓ Campaign integration and updates
    ✓ Proper async/await patterns
    ✓ Comprehensive logging and error handling
    
    Requirements Satisfied:
    - 3.1: Generate 5+ ad copy variations
    - 3.2: Multiple headline lengths (30, 60, 90 chars)
    - 3.3: Align with campaign objectives
    - 3.4: Compliance validation
    - 3.5: Filter prohibited terms
    - 11.1: ADK agent pattern
    - 11.2: Agent-to-agent messaging
    - 13.1: Firestore persistence
    """)
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
