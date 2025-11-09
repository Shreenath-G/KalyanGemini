"""Locust load testing configuration for Adaptive Ad Intelligence Platform

This file defines load testing scenarios using Locust for realistic HTTP load testing.

Run with:
    # Test campaign creation with 100 users ramping up over 10 seconds
    locust -f tests/locustfile.py --host=http://localhost:8080 --users 100 --spawn-rate 10 --run-time 5m

    # Test bid execution with 1000 users for high throughput
    locust -f tests/locustfile.py --host=http://localhost:8080 --users 1000 --spawn-rate 100 --run-time 2m CampaignUser

    # Run in headless mode with specific test
    locust -f tests/locustfile.py --host=http://localhost:8080 --users 1000 --spawn-rate 100 --run-time 5m --headless --only-summary

Requirements: 10.5
"""

from locust import HttpUser, task, between, events
import random
import uuid
import time
from datetime import datetime


class CampaignUser(HttpUser):
    """Simulates users creating and managing campaigns"""
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.account_id = f"acc_load_test_{uuid.uuid4().hex[:8]}"
        self.api_key = "test_api_key_12345"
        self.campaign_ids = []
    
    @task(10)
    def create_campaign(self):
        """Create a new campaign (most common operation)"""
        campaign_data = {
            "business_goal": random.choice([
                "increase_sales",
                "increase_traffic",
                "increase_awareness",
                "increase_signups"
            ]),
            "monthly_budget": random.uniform(1000, 10000),
            "target_audience": random.choice([
                "small business owners aged 30-50",
                "tech-savvy entrepreneurs",
                "marketing professionals",
                "e-commerce store owners"
            ]),
            "products": [random.choice([
                "CRM Software",
                "Project Management Tool",
                "Email Marketing Platform",
                "Analytics Dashboard"
            ])],
            "optimization_mode": random.choice(["standard", "aggressive"])
        }
        
        with self.client.post(
            "/api/v1/campaigns",
            json=campaign_data,
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200 or response.status_code == 201:
                try:
                    data = response.json()
                    campaign_id = data.get("campaign_id")
                    if campaign_id:
                        self.campaign_ids.append(campaign_id)
                        response.success()
                    else:
                        response.failure("No campaign_id in response")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def get_campaign(self):
        """Retrieve campaign details"""
        if not self.campaign_ids:
            return
        
        campaign_id = random.choice(self.campaign_ids)
        
        with self.client.get(
            f"/api/v1/campaigns/{campaign_id}",
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Campaign might not exist yet, that's ok
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(3)
    def get_campaign_performance(self):
        """Retrieve campaign performance metrics"""
        if not self.campaign_ids:
            return
        
        campaign_id = random.choice(self.campaign_ids)
        
        with self.client.get(
            f"/api/v1/campaigns/{campaign_id}/performance",
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def optimize_campaign(self):
        """Trigger campaign optimization"""
        if not self.campaign_ids:
            return
        
        campaign_id = random.choice(self.campaign_ids)
        
        with self.client.post(
            f"/api/v1/campaigns/{campaign_id}/optimize",
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check system health"""
        with self.client.get(
            "/api/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")


class BidExecutionUser(HttpUser):
    """Simulates ad exchanges sending bid requests"""
    
    # Very short wait time for high throughput
    wait_time = between(0.001, 0.01)
    
    def on_start(self):
        """Called when a user starts"""
        self.exchange_id = f"exchange_{uuid.uuid4().hex[:8]}"
    
    @task
    def submit_bid_request(self):
        """Submit a bid request (must respond in <100ms)"""
        bid_request = {
            "request_id": str(uuid.uuid4()),
            "inventory_type": random.choice(["display", "search", "social"]),
            "user_profile": {
                "age": random.randint(25, 65),
                "gender": random.choice(["male", "female", "other"]),
                "interests": random.sample(
                    ["business", "technology", "sports", "travel", "food", "fashion"],
                    k=random.randint(2, 4)
                ),
                "location": random.choice(["US", "UK", "CA", "AU"]),
                "device": random.choice(["desktop", "mobile", "tablet"])
            },
            "floor_price": random.uniform(0.10, 2.00),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/bids/request",
            json=bid_request,
            headers={"X-Exchange-ID": self.exchange_id},
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                if response_time > 100:
                    response.failure(f"Response time {response_time:.2f}ms exceeds 100ms requirement")
                else:
                    response.success()
            elif response.status_code == 204:
                # No bid (valid response)
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """Simulates mixed workload of campaigns and bids"""
    
    wait_time = between(0.1, 1.0)
    
    def on_start(self):
        """Called when a user starts"""
        self.account_id = f"acc_mixed_{uuid.uuid4().hex[:8]}"
        self.api_key = "test_api_key_12345"
        self.campaign_ids = []
    
    @task(5)
    def create_campaign(self):
        """Create campaign"""
        campaign_data = {
            "business_goal": "increase_sales",
            "monthly_budget": random.uniform(1000, 10000),
            "target_audience": "small business owners",
            "products": ["CRM Software"],
            "optimization_mode": "standard"
        }
        
        self.client.post(
            "/api/v1/campaigns",
            json=campaign_data,
            headers={"X-API-Key": self.api_key}
        )
    
    @task(20)
    def submit_bid(self):
        """Submit bid request"""
        bid_request = {
            "request_id": str(uuid.uuid4()),
            "inventory_type": "display",
            "user_profile": {
                "age": random.randint(25, 65),
                "interests": ["business", "technology"],
                "location": "US",
                "device": "desktop"
            },
            "floor_price": 0.50
        }
        
        self.client.post(
            "/api/v1/bids/request",
            json=bid_request
        )
    
    @task(2)
    def get_performance(self):
        """Get performance metrics"""
        if self.campaign_ids:
            campaign_id = random.choice(self.campaign_ids)
            self.client.get(
                f"/api/v1/campaigns/{campaign_id}/performance",
                headers={"X-API-Key": self.api_key}
            )


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("\n" + "="*60)
    print("LOAD TEST STARTED")
    print("="*60)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("\n" + "="*60)
    print("LOAD TEST COMPLETED")
    print("="*60)
    
    stats = environment.stats
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Success Rate: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.2f}%")
    print(f"RPS: {stats.total.total_rps:.2f}")
    
    print(f"\nResponse Times:")
    print(f"  Average: {stats.total.avg_response_time:.2f}ms")
    print(f"  Median: {stats.total.median_response_time:.2f}ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Min: {stats.total.min_response_time:.2f}ms")
    print(f"  Max: {stats.total.max_response_time:.2f}ms")
    
    print("\n" + "="*60)
    
    # Check requirements
    p99 = stats.total.get_response_time_percentile(0.99)
    success_rate = (stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100
    
    print("\nREQUIREMENT VALIDATION:")
    print("="*60)
    
    if success_rate >= 95.0:
        print(f"✓ Success Rate: {success_rate:.2f}% (>= 95%)")
    else:
        print(f"✗ Success Rate: {success_rate:.2f}% (< 95%)")
    
    # Check if this is a bid execution test (high RPS)
    if stats.total.total_rps > 1000:
        if p99 < 100:
            print(f"✓ P99 Latency: {p99:.2f}ms (< 100ms for bid execution)")
        else:
            print(f"✗ P99 Latency: {p99:.2f}ms (>= 100ms for bid execution)")
    else:
        if p99 < 5000:
            print(f"✓ P99 Latency: {p99:.2f}ms (< 5000ms for campaign operations)")
        else:
            print(f"✗ P99 Latency: {p99:.2f}ms (>= 5000ms for campaign operations)")
    
    print("="*60 + "\n")


# Custom shape for ramping load test
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    A step load shape that increases load in steps to test auto-scaling
    
    Stages:
    1. 10 users for 60s (warm-up)
    2. 50 users for 60s (low load)
    3. 100 users for 60s (medium load)
    4. 500 users for 60s (high load)
    5. 1000 users for 60s (peak load)
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 180, "users": 100, "spawn_rate": 10},
        {"duration": 240, "users": 500, "spawn_rate": 50},
        {"duration": 300, "users": 1000, "spawn_rate": 100},
    ]
    
    def tick(self):
        """Returns the current user count and spawn rate"""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None


class SpikeLoadShape(LoadTestShape):
    """
    A spike load shape to test system resilience
    
    Pattern: Low -> Spike -> Low -> Spike
    """
    
    def tick(self):
        """Returns the current user count and spawn rate"""
        run_time = self.get_run_time()
        
        if run_time < 60:
            return (50, 10)  # Baseline
        elif run_time < 90:
            return (1000, 100)  # Spike
        elif run_time < 150:
            return (50, 10)  # Back to baseline
        elif run_time < 180:
            return (1000, 100)  # Second spike
        elif run_time < 240:
            return (50, 10)  # Recovery
        else:
            return None
