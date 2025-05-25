document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard
    const advancedAnalytics = new AdvancedAnalyticsDashboard();
    advancedAnalytics.init();
});

class AdvancedAnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.riskMap = null;
        this.currentSection = 'overview';
    }

    init() {
        this.setupEventListeners();
        this.loadOverviewData();
    }

    setupEventListeners() {
        // Tab switching
        document.getElementById('overview-btn').addEventListener('click', () => this.switchSection('overview'));
        document.getElementById('predictive-btn').addEventListener('click', () => this.switchSection('predictive'));
        document.getElementById('risk-map-btn').addEventListener('click', () => this.switchSection('risk-map'));
        document.getElementById('compliance-btn').addEventListener('click', () => this.switchSection('compliance'));
    }

    switchSection(section) {
        // Hide all sections
        document.querySelectorAll('.dashboard-section').forEach(el => {
            el.classList.add('hidden');
        });
        
        // Show selected section
        document.getElementById(`${section}-section`).classList.remove('hidden');
        
        // Update active tab
        document.querySelectorAll('#overview-btn, #predictive-btn, #risk-map-btn, #compliance-btn').forEach(btn => {
            btn.classList.remove('bg-red-600', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-800');
        });
        
        document.getElementById(`${section}-btn`).classList.remove('bg-gray-200', 'text-gray-800');
        document.getElementById(`${section}-btn`).classList.add('bg-red-600', 'text-white');
        
        // Load data for the selected section if not already loaded
        this.currentSection = section;
        
        switch(section) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'predictive':
                this.loadPredictiveData();
                break;
            case 'risk-map':
                this.loadRiskMapData();
                break;
            case 'compliance':
                this.loadComplianceData();
                break;
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch('/api/analytics/overview');
            const data = await response.json();
            
            if (data.success) {
                // Update KPI cards
                document.getElementById('total-applications').textContent = data.stats.total;
                document.getElementById('approval-rate').textContent = data.stats.approval_rate + '%';
                document.getElementById('avg-processing-time').textContent = data.stats.avg_processing_time + ' days';
                document.getElementById('compliance-rate').textContent = data.stats.compliance_rate + '%';
                
                // Update trends
                this.updateTrendIndicator('total-trend', data.trends.total);
                this.updateTrendIndicator('approval-trend', data.trends.approval_rate);
                this.updateTrendIndicator('processing-trend', data.trends.processing_time, true);
                this.updateTrendIndicator('compliance-trend', data.trends.compliance);
                
                // Create charts
                this.createApplicationTrendsChart(data.charts.application_trends);
                this.createStatusDistributionChart(data.charts.status_distribution);
                this.createBusinessTypeChart(data.charts.business_types);
                this.createInspectorPerformanceChart(data.charts.inspector_performance);
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showNotification('Error loading analytics data', 'error');
        }
    }

    async loadPredictiveData() {
        try {
            const response = await fetch('/api/analytics/predictive');
            const data = await response.json();
            
            if (data.success) {
                // Update prediction cards
                document.getElementById('predicted-applications').textContent = data.predictions.applications;
                document.getElementById('upcoming-renewals').textContent = data.predictions.renewals;
                document.getElementById('predicted-inspections').textContent = data.predictions.inspections;
                
                // Create forecast charts
                this.createApplicationForecastChart(data.forecasts.applications);
                this.createRenewalForecastChart(data.forecasts.renewals);
            }
        } catch (error) {
            console.error('Error loading predictive data:', error);
            this.showNotification('Error loading predictive analytics', 'error');
        }
    }

    async loadRiskMapData() {
        try {
            const response = await fetch('/api/analytics/risk-map');
            const data = await response.json();
            
            if (data.success) {
                // Initialize map if not already done
                if (!this.riskMap) {
                    this.initializeRiskMap();
                }
                
                // Update risk map with data
                this.updateRiskMap(data.risk_map);
                
                // Update high risk areas table
                this.updateHighRiskAreas(data.high_risk_areas);
                
                // Update resource recommendations
                this.updateResourceRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('Error loading risk map data:', error);
            this.showNotification('Error loading risk assessment data', 'error');
        }
    }

    async loadComplianceData() {
        try {
            const response = await fetch('/api/analytics/compliance');
            const data = await response.json();
            
            if (data.success) {
                // Update compliance cards
                document.getElementById('overall-compliance').textContent = data.compliance.overall + '%';
                document.getElementById('expiring-certificates').textContent = data.compliance.expiring;
                document.getElementById('inspection-compliance').textContent = data.compliance.inspection + '%';
                
                // Update trend indicators
                this.updateTrendIndicator('compliance-overall-trend', data.trends.overall);
                this.updateTrendIndicator('inspection-compliance-trend', data.trends.inspection);
                
                // Create compliance charts
                this.createComplianceByTypeChart(data.charts.by_type);
                this.createComplianceTrendChart(data.charts.trend);
            }
        } catch (error) {
            console.error('Error loading compliance data:', error);
            this.showNotification('Error loading compliance data', 'error');
        }
    }

    // Helper methods for charts and visualizations
    createApplicationTrendsChart(data) {
        const ctx = document.getElementById('application-trends-chart').getContext('2d');
        
        if (this.charts.applicationTrends) {
            this.charts.applicationTrends.destroy();
        }
        
        this.charts.applicationTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'New Applications',
                        data: data.new,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Approved',
                        data: data.approved,
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Rejected',
                        data: data.rejected,
                        borderColor: 'rgba(239, 68, 68, 1)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Other chart creation methods would be similar

    initializeRiskMap() {
        this.riskMap = L.map('risk-map').setView([20.5937, 78.9629], 5); // Center on India
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.riskMap);
    }

    updateRiskMap(riskData) {
        // Clear existing markers
        if (this.riskMapLayer) {
            this.riskMap.removeLayer(this.riskMapLayer);
        }
        
        // Add heat map layer
        this.riskMapLayer = L.heatLayer(
            riskData.map(point => [point.lat, point.lng, point.risk_score / 100]),
            {radius: 25, blur: 15, maxZoom: 10}
        ).addTo(this.riskMap);
    }

    updateTrendIndicator(elementId, trendValue, inverse = false) {
        const element = document.getElementById(elementId);
        
        if (trendValue === 0) {
            element.textContent = 'No change';
            element.classList.remove('text-green-600', 'text-red-600');
            element.classList.add('text-gray-600');
            return;
        }
        
        const isPositive = trendValue > 0;
        const displayValue = Math.abs(trendValue) + '%';
        
        // For metrics where lower is better (like processing time)
        const isGood = inverse ? !isPositive : isPositive;
        
        element.textContent = (isPositive ? '+' : '-') + displayValue;
        
        if (isGood) {
            element.classList.remove('text-red-600', 'text-gray-600');
            element.classList.add('text-green-600');
        } else {
            element.classList.remove('text-green-600', 'text-gray-600');
            element.classList.add('text-red-600');
        }
    }

    showNotification(message, type = 'info') {
        // Implementation depends on your notification system
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}
