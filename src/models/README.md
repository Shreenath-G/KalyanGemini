# Data Models Documentation

This directory contains all Pydantic data models for the Adaptive Ad Intelligence Platform.

## Models Overview

### Campaign Models (`campaign.py`)
- **Campaign**: Complete campaign data with validation
  - Budget validation (100-100,000 USD)
  - Status tracking (draft, active, paused, completed)
  - Performance metrics tracking
- **CampaignRequest**: API request model for campaign creation
- **CampaignResponse**: API response model with campaign ID and status

### Creative Models (`creative.py`)
- **CreativeVariant**: Ad creative variations with performance tracking
  - Headlines for different character limits (30, 60, 90 chars)
  - Body copy (max 150 chars)
  - Call-to-action (max 20 chars)
  - Compliance scoring
  - Performance metrics (impressions, clicks, conversions, ROAS)
- **CreativeHeadlines**: Structured headlines for multiple platforms
- **CreativeStatus**: Enum for variant status (active, paused, testing)

### Audience Models (`audience.py`)
- **AudienceSegment**: Audience targeting segments with demographics
  - Demographics (age, gender, income)
  - Interests and behaviors
  - Size estimation (small, medium, large)
  - Conversion probability and priority scoring
  - Performance tracking
- **Demographics**: Demographic targeting criteria
- **SegmentSize**: Enum for audience size categories

### Budget Models (`budget.py`)
- **BudgetAllocation**: Complete budget allocation plan
  - Total and daily budget tracking
  - Test budget reservation (20%)
  - Spend tracking and validation
- **SegmentAllocation**: Per-segment budget allocation
  - Daily budget per segment
  - Platform split (Google Ads, Meta Ads, Programmatic)
  - Max CPC bidding
- **PlatformSplit**: Budget distribution across platforms

### Metrics Models (`metrics.py`)
- **PerformanceMetrics**: Comprehensive campaign performance data
  - Aggregate metrics (spend, impressions, clicks, conversions)
  - Calculated metrics (ROAS, CPA, CTR, conversion rate)
  - Breakdowns by variant, segment, and platform
- **VariantMetrics**: Performance metrics for creative variants
- **SegmentMetrics**: Performance metrics for audience segments
- **PlatformMetrics**: Performance metrics by advertising platform
- **MetricsSnapshot**: Point-in-time metrics for time-series analysis

## Validation Features

All models include:
- Field type validation
- Range validation (budgets, scores, percentages)
- Character limit enforcement
- Required field validation
- Custom validators for business logic
- Serialization/deserialization support

## Calculation Methods

Performance models include built-in calculation methods:
- `calculate_roas()`: Return on Ad Spend
- `calculate_cpa()`: Cost Per Acquisition
- `calculate_ctr()`: Click-Through Rate
- `calculate_conversion_rate()`: Conversion percentage

## Usage Example

```python
from src.models import Campaign, CampaignRequest, CreativeVariant

# Create a campaign request
request = CampaignRequest(
    business_goal="increase_signups",
    monthly_budget=5000.0,
    target_audience="small business owners aged 30-50",
    products=["CRM Software"]
)

# Create a creative variant
variant = CreativeVariant(
    variant_id="var_001",
    campaign_id="camp_001",
    headlines={
        "short": "Save 50% Today",
        "medium": "Limited Time: Save 50% on Premium Plans",
        "long": "Don't Miss Out: Save 50% on All Premium Plans"
    },
    body="Upgrade your business with premium features.",
    cta="Get Started Now"
)

# Calculate metrics
ctr = variant.calculate_ctr()
roas = variant.roas
```

## Requirements Mapping

- **Requirement 1.3**: Campaign budget validation (100-100,000 USD)
- **Requirement 1.5**: Product list validation
- **Requirement 5.5**: Budget allocation with 5% tolerance
- **Requirement 6.1**: Performance metrics collection
- **Requirement 6.2**: ROAS, CPA, CTR calculations
- **Requirement 8.2**: Metrics aggregation and breakdowns
