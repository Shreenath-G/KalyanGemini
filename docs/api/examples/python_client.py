"""
Python Client Example for Adaptive Ad Intelligence Platform API

This example demonstrates how to:
1. Create a new campaign
2. Monitor campaign performance
3. Trigger manual optimization
4. Export campaign data

Requirements:
    pip install requests

Usage:
    python python_client.py
"""

import requests
import time
import json
from typing import Dict, Any, Optional


class AdIntelligenceClient:
    """Client for Adaptive Ad Intelligence Platform API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        """
        Initialize the API client
        
        Args:
            api_key: Your API key
            base_url: API base URL (default: production)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_campaign(
        self,
        business_goal: str,
        monthly_budget: float,
        target_audience: str,
        products: list,
        optimization_mode: str = "standard"
    ) -> Dict[str, Any]:
        """
        Create a new advertising campaign
        
        Args:
            business_goal: Campaign objective (e.g., "increase_sales", "brand_awareness")
            monthly_budget: Budget in USD ($100 - $100,000)
            target_audience: Description of target audience
            products: List of products/services to advertise
            optimization_mode: "standard" or "aggressive"
            
        Returns:
            Campaign creation response with campaign_id
            
        Example:
            >>> client = AdIntelligenceClient("your_api_key")
            >>> response = client.create_campaign(
            ...     business_goal="increase_sales",
            ...     monthly_budget=5000.0,
            ...     target_audience="small business owners aged 30-50",
            ...     products=["CRM Software"]
            ... )
            >>> print(f"Campaign ID: {response['campaign_id']}")
        """
        url = f"{self.base_url}/api/v1/campaigns"
        
        payload = {
            "business_goal": business_goal,
            "monthly_budget": monthly_budget,
            "target_audience": target_audience,
            "products": products,
            "optimization_mode": optimization_mode
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign details
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Complete campaign information
        """
        url = f"{self.base_url}/api/v1/campaigns/{campaign_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def update_campaign(
        self,
        campaign_id: str,
        budget: Optional[float] = None,
        status: Optional[str] = None,
        optimization_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update campaign settings
        
        Args:
            campaign_id: Campaign identifier
            budget: New monthly budget (optional)
            status: New status - "active", "paused", "completed" (optional)
            optimization_mode: "standard" or "aggressive" (optional)
            
        Returns:
            Updated campaign information
        """
        url = f"{self.base_url}/api/v1/campaigns/{campaign_id}"
        
        params = {}
        if budget is not None:
            params['budget'] = budget
        if status is not None:
            params['status'] = status
        if optimization_mode is not None:
            params['optimization_mode'] = optimization_mode
        
        response = self.session.patch(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign performance metrics
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Performance metrics including ROAS, CPA, CTR, and breakdowns
        """
        url = f"{self.base_url}/api/v1/campaigns/{campaign_id}/performance"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def optimize_campaign(
        self,
        campaign_id: str,
        optimization_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Trigger manual campaign optimization
        
        Args:
            campaign_id: Campaign identifier
            optimization_type: "auto" (apply) or "suggest" (recommendations only)
            
        Returns:
            Optimization actions and results
        """
        url = f"{self.base_url}/api/v1/campaigns/{campaign_id}/optimize"
        
        params = {'optimization_type': optimization_type}
        
        response = self.session.post(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def list_campaigns(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List campaigns for the authenticated account
        
        Args:
            status: Filter by status (optional)
            limit: Number of campaigns per page (default: 50)
            offset: Number of campaigns to skip (default: 0)
            
        Returns:
            List of campaigns with pagination metadata
        """
        url = f"{self.base_url}/api/v1/campaigns"
        
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def export_account_data(
        self,
        format: str = "json",
        include_metrics: bool = True
    ) -> bytes:
        """
        Export all account data
        
        Args:
            format: "json" or "csv"
            include_metrics: Include performance metrics in export
            
        Returns:
            Exported data as bytes
        """
        url = f"{self.base_url}/api/v1/data/export"
        
        params = {
            'format': format,
            'include_metrics': include_metrics
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.content
    
    def wait_for_campaign_ready(
        self,
        campaign_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for campaign to be ready (status != draft)
        
        Args:
            campaign_id: Campaign identifier
            timeout: Maximum wait time in seconds (default: 300)
            poll_interval: Seconds between status checks (default: 5)
            
        Returns:
            Campaign information when ready
            
        Raises:
            TimeoutError: If campaign is not ready within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            campaign = self.get_campaign(campaign_id)
            
            if campaign['status'] != 'draft':
                return campaign
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Campaign {campaign_id} not ready after {timeout} seconds")


def example_campaign_workflow():
    """
    Example: Complete campaign workflow
    
    This example demonstrates:
    1. Creating a campaign
    2. Waiting for it to be ready
    3. Monitoring performance
    4. Triggering optimization
    """
    # Initialize client
    client = AdIntelligenceClient(api_key="your_api_key_here")
    
    print("=== Creating Campaign ===")
    
    # Create campaign
    campaign_response = client.create_campaign(
        business_goal="increase_sales",
        monthly_budget=5000.0,
        target_audience="small business owners aged 30-50 interested in productivity tools",
        products=["CRM Software", "Project Management Tool"],
        optimization_mode="standard"
    )
    
    campaign_id = campaign_response['campaign_id']
    print(f"Campaign created: {campaign_id}")
    print(f"Estimated launch: {campaign_response['estimated_launch']}")
    print(f"Message: {campaign_response['message']}")
    
    print("\n=== Waiting for Campaign Ready ===")
    
    # Wait for campaign to be ready
    try:
        campaign = client.wait_for_campaign_ready(campaign_id, timeout=60)
        print(f"Campaign status: {campaign['status']}")
        print(f"Creative variants: {len(campaign.get('creative_variants', []))}")
        print(f"Audience segments: {len(campaign.get('audience_segments', []))}")
    except TimeoutError as e:
        print(f"Warning: {e}")
        print("Campaign is still processing. You can check status later.")
    
    print("\n=== Monitoring Performance ===")
    
    # Get performance metrics
    performance = client.get_performance(campaign_id)
    print(f"Total spend: ${performance['total_spend']:.2f}")
    print(f"Total conversions: {performance['total_conversions']}")
    print(f"ROAS: {performance['roas']:.2f}")
    print(f"CPA: ${performance['cpa']:.2f}")
    print(f"CTR: {performance['ctr']:.2f}%")
    
    # Show top performing variant
    if performance.get('by_variant'):
        top_variant = max(performance['by_variant'], key=lambda v: v.get('roas', 0))
        print(f"\nTop variant: {top_variant['variant_id']}")
        print(f"  ROAS: {top_variant.get('roas', 0):.2f}")
        print(f"  Conversions: {top_variant.get('conversions', 0)}")
    
    print("\n=== Triggering Optimization ===")
    
    # Get optimization suggestions
    suggestions = client.optimize_campaign(campaign_id, optimization_type="suggest")
    print(f"Optimization suggestions: {suggestions['total_actions']}")
    
    for action in suggestions['actions']:
        print(f"  - {action['type']}: {action.get('reason', 'N/A')}")
    
    # Apply optimizations
    if suggestions['total_actions'] > 0:
        result = client.optimize_campaign(campaign_id, optimization_type="auto")
        print(f"\nApplied {len(result['actions'])} optimizations")
    
    print("\n=== Campaign Summary ===")
    
    # Get updated campaign details
    campaign = client.get_campaign(campaign_id)
    print(f"Campaign ID: {campaign['campaign_id']}")
    print(f"Status: {campaign['status']}")
    print(f"Budget: ${campaign['monthly_budget']:.2f}")
    print(f"Total spend: ${campaign['total_spend']:.2f}")
    print(f"ROAS: {campaign['current_roas']:.2f}")


def example_list_and_export():
    """
    Example: List campaigns and export data
    """
    client = AdIntelligenceClient(api_key="your_api_key_here")
    
    print("=== Listing Active Campaigns ===")
    
    # List active campaigns
    campaigns = client.list_campaigns(status="active", limit=10)
    print(f"Total active campaigns: {campaigns['total']}")
    
    for campaign in campaigns['campaigns']:
        print(f"\n{campaign['campaign_id']}:")
        print(f"  Goal: {campaign['business_goal']}")
        print(f"  Budget: ${campaign['monthly_budget']:.2f}")
        print(f"  ROAS: {campaign.get('current_roas', 0):.2f}")
    
    print("\n=== Exporting Account Data ===")
    
    # Export data as JSON
    data = client.export_account_data(format="json", include_metrics=True)
    
    # Save to file
    with open("account_export.json", "wb") as f:
        f.write(data)
    
    print("Account data exported to account_export.json")


def example_error_handling():
    """
    Example: Proper error handling
    """
    client = AdIntelligenceClient(api_key="your_api_key_here")
    
    try:
        # Attempt to create campaign with invalid budget
        client.create_campaign(
            business_goal="increase_sales",
            monthly_budget=150000.0,  # Exceeds max of $100,000
            target_audience="everyone",
            products=["Product"]
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()['error']
            print(f"Validation Error: {error['message']}")
            print(f"Details: {error['details']}")
        elif e.response.status_code == 429:
            error = e.response.json()['error']
            print(f"Rate limit exceeded. Retry after {error['retry_after']} seconds")
            time.sleep(error['retry_after'])
        else:
            print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Run examples
    print("Adaptive Ad Intelligence Platform - Python Client Examples\n")
    
    # Uncomment the example you want to run:
    
    # example_campaign_workflow()
    # example_list_and_export()
    # example_error_handling()
    
    print("\nNote: Replace 'your_api_key_here' with your actual API key")
    print("Update base_url if using a different environment")
