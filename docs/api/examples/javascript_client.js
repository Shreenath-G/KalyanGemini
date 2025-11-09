/**
 * JavaScript/Node.js Client Example for Adaptive Ad Intelligence Platform API
 * 
 * This example demonstrates how to:
 * 1. Create a new campaign
 * 2. Monitor campaign performance
 * 3. Trigger manual optimization
 * 4. Export campaign data
 * 
 * Requirements:
 *     npm install axios
 * 
 * Usage:
 *     node javascript_client.js
 */

const axios = require('axios');

/**
 * Client for Adaptive Ad Intelligence Platform API
 */
class AdIntelligenceClient {
    /**
     * Initialize the API client
     * 
     * @param {string} apiKey - Your API key
     * @param {string} baseUrl - API base URL (default: production)
     */
    constructor(apiKey, baseUrl = 'https://api.example.com') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replace(/\/$/, '');
        
        // Create axios instance with default config
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
        
        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                if (error.response) {
                    const errorData = error.response.data.error;
                    console.error(`API Error: ${errorData.code} - ${errorData.message}`);
                    if (errorData.details) {
                        console.error(`Details: ${errorData.details}`);
                    }
                }
                throw error;
            }
        );
    }
    
    /**
     * Create a new advertising campaign
     * 
     * @param {Object} params - Campaign parameters
     * @param {string} params.businessGoal - Campaign objective
     * @param {number} params.monthlyBudget - Budget in USD ($100 - $100,000)
     * @param {string} params.targetAudience - Description of target audience
     * @param {string[]} params.products - List of products/services
     * @param {string} params.optimizationMode - "standard" or "aggressive"
     * @returns {Promise<Object>} Campaign creation response
     * 
     * @example
     * const client = new AdIntelligenceClient('your_api_key');
     * const response = await client.createCampaign({
     *     businessGoal: 'increase_sales',
     *     monthlyBudget: 5000.0,
     *     targetAudience: 'small business owners aged 30-50',
     *     products: ['CRM Software'],
     *     optimizationMode: 'standard'
     * });
     * console.log(`Campaign ID: ${response.campaign_id}`);
     */
    async createCampaign({
        businessGoal,
        monthlyBudget,
        targetAudience,
        products,
        optimizationMode = 'standard'
    }) {
        const response = await this.client.post('/api/v1/campaigns', {
            business_goal: businessGoal,
            monthly_budget: monthlyBudget,
            target_audience: targetAudience,
            products: products,
            optimization_mode: optimizationMode
        });
        
        return response.data;
    }
    
    /**
     * Get campaign details
     * 
     * @param {string} campaignId - Campaign identifier
     * @returns {Promise<Object>} Complete campaign information
     */
    async getCampaign(campaignId) {
        const response = await this.client.get(`/api/v1/campaigns/${campaignId}`);
        return response.data;
    }
    
    /**
     * Update campaign settings
     * 
     * @param {string} campaignId - Campaign identifier
     * @param {Object} updates - Fields to update
     * @param {number} updates.budget - New monthly budget (optional)
     * @param {string} updates.status - New status (optional)
     * @param {string} updates.optimizationMode - New optimization mode (optional)
     * @returns {Promise<Object>} Updated campaign information
     */
    async updateCampaign(campaignId, updates = {}) {
        const params = {};
        
        if (updates.budget !== undefined) {
            params.budget = updates.budget;
        }
        if (updates.status !== undefined) {
            params.status = updates.status;
        }
        if (updates.optimizationMode !== undefined) {
            params.optimization_mode = updates.optimizationMode;
        }
        
        const response = await this.client.patch(
            `/api/v1/campaigns/${campaignId}`,
            null,
            { params }
        );
        
        return response.data;
    }
    
    /**
     * Get campaign performance metrics
     * 
     * @param {string} campaignId - Campaign identifier
     * @returns {Promise<Object>} Performance metrics
     */
    async getPerformance(campaignId) {
        const response = await this.client.get(
            `/api/v1/campaigns/${campaignId}/performance`
        );
        return response.data;
    }
    
    /**
     * Trigger manual campaign optimization
     * 
     * @param {string} campaignId - Campaign identifier
     * @param {string} optimizationType - "auto" or "suggest"
     * @returns {Promise<Object>} Optimization actions and results
     */
    async optimizeCampaign(campaignId, optimizationType = 'auto') {
        const response = await this.client.post(
            `/api/v1/campaigns/${campaignId}/optimize`,
            null,
            { params: { optimization_type: optimizationType } }
        );
        
        return response.data;
    }
    
    /**
     * List campaigns for the authenticated account
     * 
     * @param {Object} options - List options
     * @param {string} options.status - Filter by status (optional)
     * @param {number} options.limit - Number per page (default: 50)
     * @param {number} options.offset - Number to skip (default: 0)
     * @returns {Promise<Object>} List of campaigns with pagination
     */
    async listCampaigns({ status, limit = 50, offset = 0 } = {}) {
        const params = { limit, offset };
        if (status) {
            params.status = status;
        }
        
        const response = await this.client.get('/api/v1/campaigns', { params });
        return response.data;
    }
    
    /**
     * Export all account data
     * 
     * @param {string} format - "json" or "csv"
     * @param {boolean} includeMetrics - Include performance metrics
     * @returns {Promise<Buffer>} Exported data
     */
    async exportAccountData(format = 'json', includeMetrics = true) {
        const response = await this.client.get('/api/v1/data/export', {
            params: {
                format,
                include_metrics: includeMetrics
            },
            responseType: 'arraybuffer'
        });
        
        return response.data;
    }
    
    /**
     * Wait for campaign to be ready (status != draft)
     * 
     * @param {string} campaignId - Campaign identifier
     * @param {number} timeout - Maximum wait time in seconds (default: 300)
     * @param {number} pollInterval - Seconds between checks (default: 5)
     * @returns {Promise<Object>} Campaign information when ready
     * @throws {Error} If campaign is not ready within timeout
     */
    async waitForCampaignReady(campaignId, timeout = 300, pollInterval = 5) {
        const startTime = Date.now();
        
        while ((Date.now() - startTime) / 1000 < timeout) {
            const campaign = await this.getCampaign(campaignId);
            
            if (campaign.status !== 'draft') {
                return campaign;
            }
            
            await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
        }
        
        throw new Error(`Campaign ${campaignId} not ready after ${timeout} seconds`);
    }
}

/**
 * Example: Complete campaign workflow
 */
async function exampleCampaignWorkflow() {
    // Initialize client
    const client = new AdIntelligenceClient('your_api_key_here');
    
    console.log('=== Creating Campaign ===');
    
    try {
        // Create campaign
        const campaignResponse = await client.createCampaign({
            businessGoal: 'increase_sales',
            monthlyBudget: 5000.0,
            targetAudience: 'small business owners aged 30-50 interested in productivity tools',
            products: ['CRM Software', 'Project Management Tool'],
            optimizationMode: 'standard'
        });
        
        const campaignId = campaignResponse.campaign_id;
        console.log(`Campaign created: ${campaignId}`);
        console.log(`Estimated launch: ${campaignResponse.estimated_launch}`);
        console.log(`Message: ${campaignResponse.message}`);
        
        console.log('\n=== Waiting for Campaign Ready ===');
        
        // Wait for campaign to be ready
        try {
            const campaign = await client.waitForCampaignReady(campaignId, 60);
            console.log(`Campaign status: ${campaign.status}`);
            console.log(`Creative variants: ${campaign.creative_variants?.length || 0}`);
            console.log(`Audience segments: ${campaign.audience_segments?.length || 0}`);
        } catch (error) {
            console.log(`Warning: ${error.message}`);
            console.log('Campaign is still processing. You can check status later.');
        }
        
        console.log('\n=== Monitoring Performance ===');
        
        // Get performance metrics
        const performance = await client.getPerformance(campaignId);
        console.log(`Total spend: $${performance.total_spend.toFixed(2)}`);
        console.log(`Total conversions: ${performance.total_conversions}`);
        console.log(`ROAS: ${performance.roas.toFixed(2)}`);
        console.log(`CPA: $${performance.cpa.toFixed(2)}`);
        console.log(`CTR: ${performance.ctr.toFixed(2)}%`);
        
        // Show top performing variant
        if (performance.by_variant && performance.by_variant.length > 0) {
            const topVariant = performance.by_variant.reduce((max, v) => 
                (v.roas || 0) > (max.roas || 0) ? v : max
            );
            console.log(`\nTop variant: ${topVariant.variant_id}`);
            console.log(`  ROAS: ${(topVariant.roas || 0).toFixed(2)}`);
            console.log(`  Conversions: ${topVariant.conversions || 0}`);
        }
        
        console.log('\n=== Triggering Optimization ===');
        
        // Get optimization suggestions
        const suggestions = await client.optimizeCampaign(campaignId, 'suggest');
        console.log(`Optimization suggestions: ${suggestions.total_actions}`);
        
        suggestions.actions.forEach(action => {
            console.log(`  - ${action.type}: ${action.reason || 'N/A'}`);
        });
        
        // Apply optimizations
        if (suggestions.total_actions > 0) {
            const result = await client.optimizeCampaign(campaignId, 'auto');
            console.log(`\nApplied ${result.actions.length} optimizations`);
        }
        
        console.log('\n=== Campaign Summary ===');
        
        // Get updated campaign details
        const campaign = await client.getCampaign(campaignId);
        console.log(`Campaign ID: ${campaign.campaign_id}`);
        console.log(`Status: ${campaign.status}`);
        console.log(`Budget: $${campaign.monthly_budget.toFixed(2)}`);
        console.log(`Total spend: $${campaign.total_spend.toFixed(2)}`);
        console.log(`ROAS: ${campaign.current_roas.toFixed(2)}`);
        
    } catch (error) {
        console.error('Error in campaign workflow:', error.message);
    }
}

/**
 * Example: List campaigns and export data
 */
async function exampleListAndExport() {
    const client = new AdIntelligenceClient('your_api_key_here');
    
    console.log('=== Listing Active Campaigns ===');
    
    try {
        // List active campaigns
        const campaigns = await client.listCampaigns({ status: 'active', limit: 10 });
        console.log(`Total active campaigns: ${campaigns.total}`);
        
        campaigns.campaigns.forEach(campaign => {
            console.log(`\n${campaign.campaign_id}:`);
            console.log(`  Goal: ${campaign.business_goal}`);
            console.log(`  Budget: $${campaign.monthly_budget.toFixed(2)}`);
            console.log(`  ROAS: ${(campaign.current_roas || 0).toFixed(2)}`);
        });
        
        console.log('\n=== Exporting Account Data ===');
        
        // Export data as JSON
        const data = await client.exportAccountData('json', true);
        
        // Save to file
        const fs = require('fs');
        fs.writeFileSync('account_export.json', data);
        
        console.log('Account data exported to account_export.json');
        
    } catch (error) {
        console.error('Error in list and export:', error.message);
    }
}

/**
 * Example: Proper error handling
 */
async function exampleErrorHandling() {
    const client = new AdIntelligenceClient('your_api_key_here');
    
    try {
        // Attempt to create campaign with invalid budget
        await client.createCampaign({
            businessGoal: 'increase_sales',
            monthlyBudget: 150000.0,  // Exceeds max of $100,000
            targetAudience: 'everyone',
            products: ['Product']
        });
    } catch (error) {
        if (error.response) {
            const status = error.response.status;
            const errorData = error.response.data.error;
            
            if (status === 400) {
                console.log(`Validation Error: ${errorData.message}`);
                console.log(`Details: ${errorData.details}`);
            } else if (status === 429) {
                console.log(`Rate limit exceeded. Retry after ${errorData.retry_after} seconds`);
                await new Promise(resolve => 
                    setTimeout(resolve, errorData.retry_after * 1000)
                );
            } else {
                console.log(`HTTP Error ${status}: ${errorData.message}`);
            }
        } else {
            console.log(`Unexpected error: ${error.message}`);
        }
    }
}

// Main execution
if (require.main === module) {
    console.log('Adaptive Ad Intelligence Platform - JavaScript Client Examples\n');
    
    // Uncomment the example you want to run:
    
    // exampleCampaignWorkflow();
    // exampleListAndExport();
    // exampleErrorHandling();
    
    console.log('\nNote: Replace "your_api_key_here" with your actual API key');
    console.log('Update baseUrl if using a different environment');
}

// Export for use as module
module.exports = AdIntelligenceClient;
