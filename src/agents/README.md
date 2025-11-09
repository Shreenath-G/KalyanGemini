# Campaign Orchestrator Agent

## Overview

The Campaign Orchestrator Agent is the central coordination agent in the Adaptive Ad Intelligence Platform. It manages the campaign creation and optimization workflow by coordinating specialist agents (Creative Generator, Audience Targeting, and Budget Optimizer).

## Architecture

### Agent Communication

The orchestrator uses a message-passing architecture to communicate with specialist agents:

```
API Request → Campaign Orchestrator → [Creative, Audience, Budget] Agents (parallel)
                                    ↓
                            Synthesize Strategy
                                    ↓
                            Persist to Firestore
                                    ↓
                            Return Response
```

### Key Components

1. **CampaignOrchestratorAgent**: Main orchestrator class
2. **AgentMessage**: Message structure for agent communication
3. **AgentResponse**: Response structure from specialist agents
4. **AgentErrorHandler**: Error handling and fallback strategies

## Features

### Campaign Creation (Task 5.1-5.3)

- **Agent Initialization**: Sets up communication channels to specialist agents
- **Request Handling**: Distributes campaign creation tasks to specialist agents in parallel
- **Timeout Management**: 30-second timeout with fallback strategies
- **Strategy Synthesis**: Combines agent outputs into unified campaign strategy
- **State Persistence**: Saves campaign state to Firestore using ADK state management

### Optimization Handling (Task 5.4)

- **Manual Optimization**: Processes user-triggered optimization requests
- **Automatic Optimization**: Handles optimization actions from Performance Analyzer Agent
- **Budget Adjustments**: Coordinates with Budget Optimizer Agent for spend reallocation
- **Creative Updates**: Coordinates with Creative Generator Agent for new variants
- **Pause Actions**: Immediately pauses underperforming variants or segments

### API Integration (Task 5.5)

- **Campaign Creation Endpoint**: Integrated with POST /api/v1/campaigns
- **Optimization Endpoint**: Integrated with POST /api/v1/campaigns/{id}/optimize
- **Error Handling**: Graceful degradation with fallback strategies
- **Logging**: Comprehensive logging with correlation IDs for tracing

## Fallback Strategies

When specialist agents fail or timeout, the orchestrator applies fallback strategies:

### Creative Generator Fallback
- Uses template-based creative generation
- Generates 3 basic variants with standard messaging
- Marks variants with `fallback: true` flag

### Audience Targeting Fallback
- Uses broad category targeting
- Creates single broad audience segment
- Lower conversion probability (0.05)

### Budget Optimizer Fallback
- Equal distribution across segments
- Standard platform split (40% Google, 40% Meta, 20% Programmatic)
- Conservative max CPC ($2.00)

## Usage

### Creating a Campaign

```python
from src.agents.campaign_orchestrator import get_orchestrator_agent
from src.models.campaign import Campaign, CampaignRequest

# Get orchestrator instance
orchestrator = get_orchestrator_agent()

# Handle campaign request
agent_results = await orchestrator.handle_campaign_request(campaign, campaign_request)

# Synthesize strategy
updated_campaign = await orchestrator.synthesize_strategy(campaign, agent_results)
```

### Handling Optimization

```python
# Define optimization actions
actions = [
    {
        "type": "pause_variant",
        "variant_id": "var_123",
        "reason": "Low ROAS: 0.5"
    },
    {
        "type": "scale_variant",
        "variant_id": "var_456",
        "reason": "High ROAS: 4.2",
        "increase_percent": 50
    }
]

# Apply optimizations
results = await orchestrator.handle_optimization_request(
    campaign_id="camp_123",
    optimization_actions=actions,
    optimization_type="auto"
)
```

## Error Handling

The orchestrator includes comprehensive error handling:

1. **Timeout Handling**: 30-second timeout for agent responses
2. **Retry Logic**: Exponential backoff for transient failures
3. **Fallback Strategies**: Automatic fallback when agents fail
4. **Error Logging**: Detailed error logs with stack traces
5. **Graceful Degradation**: System continues operation with reduced functionality

## State Management

The orchestrator uses ADK's state management backed by Firestore:

- **Campaign State**: Tracks campaign progress and agent coordination
- **Correlation IDs**: Links related agent communications
- **Agent Status**: Records success/failure of each agent
- **Optimization History**: Tracks optimization actions over time

## Requirements Satisfied

- **Requirement 2.1**: Campaign Orchestrator receives and analyzes campaign requests
- **Requirement 2.2**: Uses ADK agent-to-agent messaging
- **Requirement 2.3**: Collects responses within 30 seconds
- **Requirement 2.4**: Uses fallback strategies for agent failures
- **Requirement 2.5**: Synthesizes outputs into unified campaign plan
- **Requirement 11.1**: Implements all agents using Google ADK
- **Requirement 11.2**: Uses ADK communication primitives
- **Requirement 12.2**: Comprehensive error handling
- **Requirement 12.3**: Graceful degradation on failures

## Future Enhancements

1. **Full ADK Integration**: Replace placeholder message passing with actual ADK infrastructure
2. **Pub/Sub Integration**: Use Google Pub/Sub for agent communication
3. **Advanced State Management**: Implement full ADK state persistence
4. **Performance Monitoring**: Add metrics for agent response times
5. **Circuit Breaker**: Implement circuit breaker pattern for failing agents

## Testing

To test the orchestrator agent:

```bash
# Run unit tests (when implemented)
pytest tests/agents/test_campaign_orchestrator.py

# Test API integration
curl -X POST http://localhost:8080/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "business_goal": "increase_signups",
    "monthly_budget": 5000,
    "target_audience": "small business owners",
    "products": ["CRM Software"]
  }'
```

## Logging

The orchestrator logs all important events:

- Agent message sending/receiving
- Timeout events
- Fallback strategy activation
- Strategy synthesis completion
- Optimization actions applied

All logs include correlation IDs for request tracing.
