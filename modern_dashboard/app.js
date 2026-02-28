// Modern Carbon Intelligence Platform JavaScript

class CarbonDashboard {
    constructor() {
        this.apiBase = 'http://localhost:8001';
        this.isAutoRefresh = true;
        this.refreshRate = 2000; // milliseconds
        this.refreshTimer = null;
        this.currentSection = 'overview';
        this.charts = {};
        
        console.log('Carbon Dashboard initializing...');
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupInfoModal();
        this.setupTooltips();
        this.initCharts();
        this.loadData();
        this.startAutoRefresh();
        
        // Hide loading overlay after init
        setTimeout(() => {
            document.getElementById('loadingOverlay').classList.add('hidden');
            // Trigger chart resize after layout is stable
            this.resizeAllCharts();
        }, 1000);
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });
        
        // Auto refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefresh');
        autoRefreshToggle.addEventListener('change', (e) => {
            this.isAutoRefresh = e.target.checked;
            if (this.isAutoRefresh) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
        
        // Refresh rate selector
        const refreshRateSelect = document.getElementById('refreshRate');
        refreshRateSelect.addEventListener('change', (e) => {
            this.refreshRate = parseInt(e.target.value) * 1000;
            if (this.isAutoRefresh) {
                this.startAutoRefresh();
            }
        });
        
        // Manual refresh button
        document.getElementById('manualRefresh').addEventListener('click', () => {
            this.loadData();
        });
        
        // Chart controls
        document.querySelectorAll('.chart-control').forEach(control => {
            control.addEventListener('click', (e) => {
                const period = e.target.dataset.period;
                this.updateChartPeriod(period);
                
                // Update active state
                e.target.parentElement.querySelectorAll('.chart-control').forEach(c => c.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        // Activity filters
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.dataset.type;
                this.filterActivity(type);
                
                // Update active state
                e.target.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }
    
    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');
        
        this.currentSection = sectionName;
        
        // Initialize charts for this section if not already done
        this.initializeSectionCharts(sectionName);
    }
    
    initializeSectionCharts(sectionName) {
        if (!this.chartsInitialized[sectionName]) {
            try {
                switch(sectionName) {
                    case 'emissions':
                        this.initEmissionsCharts();
                        break;
                    case 'transport':
                        this.initTransportCharts();
                        break;
                    case 'energy':
                        this.initEnergyCharts();
                        break;
                }
                this.chartsInitialized[sectionName] = true;
                console.log(`${sectionName} charts initialized`);
            } catch (error) {
                console.error(`Error initializing ${sectionName} charts:`, error);
            }
        }
    }
    
    async loadData() {
        try {
            // Show loading state
            this.showLoading();
            
            // Load CSV data directly (since we don't have the FastAPI backend yet)
            const data = await this.loadCSVData();
            this.updateDashboard(data);
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadCSVData() {
        // Load data from FastAPI backend
        try {
            console.log('Fetching data from API...');
            const response = await fetch(`${this.apiBase}/api/summary`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            console.log('API data loaded successfully:', data.summary);
            return data;
        } catch (error) {
            console.error('API Error:', error);
            console.log('Falling back to mock data');
            // Fallback to mock data if API fails
            return this.generateMockData();
        }
    }
    
    generateMockData() {
        const now = new Date();
        const days = [];
        
        // Generate 30 days of data
        for (let i = 29; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            days.push({
                date: date.toISOString().split('T')[0],
                transport: Math.random() * 500 + 100,
                electricity: Math.random() * 300 + 50,
                total: 0
            });
        }
        
        days.forEach(day => {
            day.total = day.transport + day.electricity;
        });
        
        const totalEmissions = days.reduce((sum, day) => sum + day.total, 0);
        const totalTransport = days.reduce((sum, day) => sum + day.transport, 0);
        const totalElectricity = days.reduce((sum, day) => sum + day.electricity, 0);
        
        return {
            summary: {
                totalEmissions: totalEmissions,
                totalActivities: Math.floor(Math.random() * 1000) + 500,
                transportEmissions: totalTransport,
                electricityEmissions: totalElectricity,
                lastUpdate: new Date().toLocaleTimeString()
            },
            trendData: days,
            categories: {
                'Transport': totalTransport,
                'Electricity': totalElectricity,
                'Purchased Goods': Math.random() * 200 + 50
            },
            transportModes: {
                'Road': Math.random() * 300 + 100,
                'Rail': Math.random() * 150 + 50,
                'Air': Math.random() * 200 + 75,
                'Sea': Math.random() * 100 + 25
            },
            recentActivity: this.generateRecentActivity(),
            hotspots: this.generateHotspots()
        };
    }
    
    generateRecentActivity() {
        const activities = [];
        const types = ['transport', 'electricity'];
        const transportModes = ['road', 'rail', 'air', 'sea'];
        
        for (let i = 0; i < 10; i++) {
            const type = types[Math.floor(Math.random() * types.length)];
            const timestamp = new Date(Date.now() - Math.random() * 3600000);
            
            if (type === 'transport') {
                const mode = transportModes[Math.floor(Math.random() * transportModes.length)];
                const distance = Math.floor(Math.random() * 2000) + 100;
                const weight = (Math.random() * 50 + 1).toFixed(1);
                const emissions = (distance * weight * 0.12).toFixed(2);
                
                activities.push({
                    type: 'transport',
                    title: `${mode.charAt(0).toUpperCase() + mode.slice(1)} Transport`,
                    details: `${distance}km, ${weight} tons`,
                    value: `${emissions} kg CO2e`,
                    timestamp: timestamp.toLocaleTimeString(),
                    icon: this.getTransportIcon(mode)
                });
            } else {
                const kwh = Math.floor(Math.random() * 5000) + 100;
                const emissions = (kwh * 0.5).toFixed(2);
                
                activities.push({
                    type: 'electricity',
                    title: 'Electricity Usage',
                    details: `${kwh} kWh`,
                    value: `${emissions} kg CO2e`,
                    timestamp: timestamp.toLocaleTimeString(),
                    icon: 'fas fa-bolt'
                });
            }
        }
        
        return activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    }
    
    getTransportIcon(mode) {
        const icons = {
            'road': 'fas fa-truck',
            'rail': 'fas fa-train',
            'air': 'fas fa-plane',
            'sea': 'fas fa-ship'
        };
        return icons[mode] || 'fas fa-truck';
    }
    
    generateHotspots() {
        return {
            suppliers: [
                { name: 'Supplier A', value: (Math.random() * 1000 + 100).toFixed(1) },
                { name: 'Supplier B', value: (Math.random() * 800 + 80).toFixed(1) },
                { name: 'Supplier C', value: (Math.random() * 600 + 60).toFixed(1) },
                { name: 'Supplier D', value: (Math.random() * 400 + 40).toFixed(1) },
                { name: 'Supplier E', value: (Math.random() * 200 + 20).toFixed(1) }
            ],
            routes: [
                { name: 'NYC-LA Route', value: (Math.random() * 1200 + 200).toFixed(1) },
                { name: 'CHI-MIA Route', value: (Math.random() * 1000 + 150).toFixed(1) },
                { name: 'HOU-SEA Route', value: (Math.random() * 800 + 120).toFixed(1) },
                { name: 'DEN-ATL Route', value: (Math.random() * 600 + 100).toFixed(1) },
                { name: 'BOS-SF Route', value: (Math.random() * 400 + 80).toFixed(1) }
            ],
            skus: [
                { name: 'SKU_STEEL_001', value: (Math.random() * 500 + 100).toFixed(1) },
                { name: 'SKU_PLASTIC_002', value: (Math.random() * 400 + 80).toFixed(1) },
                { name: 'SKU_MOTOR_003', value: (Math.random() * 300 + 60).toFixed(1) },
                { name: 'SKU_PARTS_004', value: (Math.random() * 200 + 40).toFixed(1) },
                { name: 'SKU_TOOLS_005', value: (Math.random() * 100 + 20).toFixed(1) }
            ],
            facilities: [
                { name: 'Facility NYC', value: (Math.random() * 800 + 150).toFixed(1) },
                { name: 'Facility LA', value: (Math.random() * 700 + 130).toFixed(1) },
                { name: 'Facility CHI', value: (Math.random() * 600 + 110).toFixed(1) },
                { name: 'Facility HOU', value: (Math.random() * 500 + 90).toFixed(1) },
                { name: 'Facility MIA', value: (Math.random() * 400 + 70).toFixed(1) }
            ]
        };
    }
    
    updateDashboard(data) {
        // Update KPIs
        this.updateKPIs(data.summary);
        
        // Update charts
        this.updateTrendChart(data.trendData);
        this.updateCategoryChart(data.categories);
        this.updateTransportModeChart(data.transportModes);
        
        // Update activity feed
        this.updateActivityFeed(data.recentActivity);
        
        // Update hotspots
        this.updateHotspots(data.hotspots);
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = data.summary.lastUpdate;
    }
    
    updateKPIs(summary) {
        const formatNumber = (num) => {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toFixed(1);
        };
        
        document.getElementById('totalEmissions').textContent = formatNumber(summary.totalEmissions);
        document.getElementById('totalActivities').textContent = summary.totalActivities.toLocaleString();
        document.getElementById('transportEmissions').textContent = formatNumber(summary.transportEmissions);
        document.getElementById('electricityEmissions').textContent = formatNumber(summary.electricityEmissions);
        
        // Update percentages
        const transportPercent = ((summary.transportEmissions / summary.totalEmissions) * 100).toFixed(0);
        const electricityPercent = ((summary.electricityEmissions / summary.totalEmissions) * 100).toFixed(0);
        
        document.getElementById('transportPercent').textContent = transportPercent + '%';
        document.getElementById('electricityPercent').textContent = electricityPercent + '%';
    }
    
    initCharts() {
        // Initialize empty charts
        try {
            console.log('Initializing charts...');
            if (typeof Plotly === 'undefined') {
                throw new Error('Plotly.js library not loaded');
            }
            
            // Initialize overview charts
            this.charts.trend = this.createTrendChart([]);
            this.charts.category = this.createCategoryChart({});
            this.charts.transportMode = this.createTransportModeChart({});
            
            // Initialize other section charts (will be loaded when sections are accessed)
            this.chartsInitialized = {
                overview: true,
                emissions: false,
                transport: false,
                energy: false
            };
            
            console.log('Charts initialized successfully');
        } catch (error) {
            console.error('Chart initialization failed:', error);
            this.showError('Failed to initialize charts: ' + error.message);
        }
    }
    
    createTrendChart(data) {
        const trace = {
            x: data.map(d => d.date),
            y: data.map(d => d.total),
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: '#00d4aa',
                width: 3,
                shape: 'spline'
            },
            marker: {
                color: '#00d4aa',
                size: 6
            },
            fill: 'tonexty',
            fillcolor: 'rgba(0, 212, 170, 0.1)',
            name: 'Daily Emissions'
        };
        
        const layout = {
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: {
                gridcolor: 'rgba(255,255,255,0.1)',
                showgrid: true,
                zeroline: false,
                color: '#b0b0b0'
            },
            yaxis: {
                gridcolor: 'rgba(255,255,255,0.1)',
                showgrid: true,
                zeroline: false,
                color: '#b0b0b0',
                title: 'kg CO2e'
            },
            margin: { t: 20, r: 20, b: 40, l: 60 },
            showlegend: false,
            hovermode: 'x unified'
        };
        
        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: false,
            showTips: false
        };
        
        Plotly.newPlot('trendChart', [trace], layout, config);
        
        // Ensure chart resizes properly
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('trendChart');
        });
        
        return trace;
    }
    
    createCategoryChart(data) {
        const trace = {
            labels: Object.keys(data),
            values: Object.values(data),
            type: 'pie',
            hole: 0.6,
            marker: {
                colors: ['#00d4aa', '#ffab00', '#667eea', '#f5576c']
            },
            textinfo: 'label+percent',
            textposition: 'outside',
            textfont: { color: '#ffffff' }
        };
        
        const layout = {
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ffffff', family: 'Inter' },
            margin: { t: 20, r: 20, b: 20, l: 20 },
            showlegend: false
        };
        
        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: false
        };
        
        Plotly.newPlot('categoryPieChart', [trace], layout, config);
        
        // Ensure chart resizes properly
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('categoryPieChart');
        });
        
        return trace;
    }
    
    createTransportModeChart(data) {
        const trace = {
            x: Object.keys(data),
            y: Object.values(data),
            type: 'bar',
            marker: {
                color: ['#00d4aa', '#667eea', '#ffab00', '#f5576c'],
                opacity: 0.8
            }
        };
        
        const layout = {
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: {
                gridcolor: 'rgba(255,255,255,0.1)',
                showgrid: false,
                zeroline: false,
                color: '#b0b0b0'
            },
            yaxis: {
                gridcolor: 'rgba(255,255,255,0.1)',
                showgrid: true,
                zeroline: false,
                color: '#b0b0b0',
                title: 'kg CO2e'
            },
            margin: { t: 20, r: 20, b: 40, l: 60 },
            showlegend: false
        };
        
        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: false
        };
        
        Plotly.newPlot('transportModeChart', [trace], layout, config);
        
        // Ensure chart resizes properly
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('transportModeChart');
        });
        
        return trace;
    }
    
    updateTrendChart(data) {
        const update = {
            x: [data.map(d => d.date)],
            y: [data.map(d => d.total)]
        };
        
        Plotly.restyle('trendChart', update, [0]);
    }
    
    updateCategoryChart(data) {
        const update = {
            labels: [Object.keys(data)],
            values: [Object.values(data)]
        };
        
        Plotly.restyle('categoryPieChart', update, [0]);
    }
    
    updateTransportModeChart(data) {
        const update = {
            x: [Object.keys(data)],
            y: [Object.values(data)]
        };
        
        Plotly.restyle('transportModeChart', update, [0]);
    }
    
    updateActivityFeed(activities) {
        const feed = document.getElementById('activityFeed');
        feed.innerHTML = '';
        
        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <div class="activity-icon ${activity.type}">
                    <i class="${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-details">${activity.details} • ${activity.timestamp}</div>
                </div>
                <div class="activity-value">${activity.value}</div>
            `;
            feed.appendChild(item);
        });
    }
    
    updateHotspots(hotspots) {
        // Update suppliers
        this.updateHotspotList('supplierHotspots', hotspots.suppliers);
        
        // Update routes
        this.updateHotspotList('routeHotspots', hotspots.routes);
        
        // Update SKUs
        this.updateHotspotList('skuHotspots', hotspots.skus);
        
        // Update facilities
        this.updateHotspotList('facilityHotspots', hotspots.facilities);
    }
    
    updateHotspotList(elementId, items) {
        const container = document.getElementById(elementId);
        container.innerHTML = '';
        
        items.forEach(item => {
            const element = document.createElement('div');
            element.className = 'hotspot-item';
            element.innerHTML = `
                <div class="hotspot-name">${item.name}</div>
                <div class="hotspot-value">${item.value} kg CO2e</div>
            `;
            container.appendChild(element);
        });
    }
    
    filterActivity(type) {
        const items = document.querySelectorAll('.activity-item');
        items.forEach(item => {
            if (type === 'all') {
                item.style.display = 'flex';
            } else {
                const icon = item.querySelector('.activity-icon');
                if (icon.classList.contains(type)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            }
        });
    }
    
    updateChartPeriod(period) {
        // This would update the chart based on the selected period
        console.log('Updating chart period to:', period);
        // For now, just reload the data
        this.loadData();
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        if (this.isAutoRefresh) {
            this.refreshTimer = setInterval(() => {
                this.loadData();
            }, this.refreshRate);
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
    
    showLoading() {
        // Add subtle loading indicator
        const refreshBtn = document.getElementById('manualRefresh');
        const icon = refreshBtn.querySelector('i');
        icon.style.animation = 'spin 1s linear infinite';
    }
    
    hideLoading() {
        const refreshBtn = document.getElementById('manualRefresh');
        const icon = refreshBtn.querySelector('i');
        icon.style.animation = '';
    }
    
    showError(message) {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-danger);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: var(--shadow-card);
            z-index: 1001;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 5000);
    }
    
    resizeAllCharts() {
        // Resize all charts to ensure proper fit
        const chartIds = ['trendChart', 'categoryPieChart', 'transportModeChart', 'emissionsScopeChart', 
                         'monthlyEmissionsChart', 'emissionSourcesChart', 'transportModeEmissionsChart',
                         'routeEfficiencyChart', 'fleetUtilizationChart', 'energyConsumptionChart',
                         'energySourcesChart', 'peakUsageChart'];
        chartIds.forEach(chartId => {
            const element = document.getElementById(chartId);
            if (element && typeof Plotly !== 'undefined') {
                try {
                    Plotly.Plots.resize(chartId);
                } catch (error) {
                    console.log(`Could not resize ${chartId}:`, error);
                }
            }
        });
    }
    
    setupInfoModal() {
        const infoBtn = document.getElementById('infoBtn');
        const modal = document.getElementById('infoModal');
        const closeBtn = document.getElementById('closeInfoModal');
        
        // Open modal
        infoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
            
            // Show modal with animation
            modal.style.display = 'flex';
            requestAnimationFrame(() => {
                modal.classList.add('show');
            });
        });
        
        // Close modal function
        const closeModal = () => {
            modal.classList.remove('show');
            
            setTimeout(() => {
                modal.style.display = 'none';
                // Restore body scroll
                document.body.style.overflow = '';
            }, 400);
        };
        
        // Close button event
        closeBtn.addEventListener('click', closeModal);
        
        // Click outside modal to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Prevent modal content clicks from closing modal
        const modalContent = modal.querySelector('.modal-content');
        modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeModal();
            }
        });
    }
    
    setupTooltips() {
        const sectionInfoBtns = document.querySelectorAll('.section-info-btn');
        
        sectionInfoBtns.forEach(btn => {
            const tooltip = btn.querySelector('.info-tooltip');
            
            if (tooltip) {
                btn.addEventListener('mouseenter', (e) => {
                    this.positionTooltip(btn, tooltip);
                });
                
                btn.addEventListener('mouseleave', () => {
                    this.hideTooltip(tooltip);
                });
            }
        });
    }
    
    positionTooltip(btn, tooltip) {
        // Get button position
        const btnRect = btn.getBoundingClientRect();
        const tooltipWidth = 300;
        const tooltipHeight = 200; // Approximate
        const margin = 12;
        
        // Calculate optimal position
        let left = btnRect.left - tooltipWidth + btnRect.width;
        let top = btnRect.bottom + margin;
        
        // Check if tooltip would go off-screen horizontally
        if (left < margin) {
            left = btnRect.right + margin;
        }
        if (left + tooltipWidth > window.innerWidth - margin) {
            left = btnRect.left - tooltipWidth - margin;
        }
        
        // Check if tooltip would go off-screen vertically
        if (top + tooltipHeight > window.innerHeight - margin) {
            top = btnRect.top - tooltipHeight - margin;
        }
        
        // Apply positioning
        tooltip.style.left = Math.max(margin, left) + 'px';
        tooltip.style.top = Math.max(margin, top) + 'px';
        tooltip.style.right = 'auto';
        
        // Show tooltip
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
        tooltip.style.transform = 'translateX(0) translateY(0)';
    }
    
    hideTooltip(tooltip) {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        tooltip.style.transform = 'translateX(10px) translateY(-10px)';
    }
    
    initEmissionsCharts() {
        // Emissions Scope Chart
        const scopeData = [
            { scope: 'Scope 1', value: 8.2, color: '#00d4aa' },
            { scope: 'Scope 2', value: 3.5, color: '#0084ff' },
            { scope: 'Scope 3', value: 20.4, color: '#ff6b6b' }
        ];
        
        const scopeTrace = {
            x: scopeData.map(d => d.scope),
            y: scopeData.map(d => d.value),
            type: 'bar',
            marker: { color: scopeData.map(d => d.color) },
            text: scopeData.map(d => `${d.value}M kg CO2e`),
            textposition: 'auto'
        };
        
        const scopeLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', showgrid: false },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Emissions (M kg CO2e)' },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('emissionsScopeChart', [scopeTrace], scopeLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Monthly Emissions Chart
        const monthlyData = this.generateMonthlyEmissionsData();
        const monthlyTrace = {
            x: monthlyData.months,
            y: monthlyData.values,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#00d4aa', width: 3 },
            marker: { color: '#00d4aa', size: 8 }
        };
        
        const monthlyLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Emissions (M kg CO2e)' },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('monthlyEmissionsChart', [monthlyTrace], monthlyLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Emission Sources Chart
        const sourcesData = [
            { source: 'Transport', value: 35 },
            { source: 'Energy', value: 25 },
            { source: 'Manufacturing', value: 20 },
            { source: 'Supply Chain', value: 15 },
            { source: 'Waste', value: 5 }
        ];
        
        const sourcesTrace = {
            labels: sourcesData.map(d => d.source),
            values: sourcesData.map(d => d.value),
            type: 'pie',
            hole: 0.6,
            marker: {
                colors: ['#00d4aa', '#0084ff', '#ff6b6b', '#ffa726', '#ab47bc']
            },
            textinfo: 'label+percent',
            textfont: { color: '#ffffff' }
        };
        
        const sourcesLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            margin: { t: 20, r: 20, b: 20, l: 20 },
            showlegend: false
        };
        
        Plotly.newPlot('emissionSourcesChart', [sourcesTrace], sourcesLayout, {
            responsive: true,
            displayModeBar: false
        });
    }
    
    initTransportCharts() {
        // Transport Mode Emissions Over Time
        const transportTimeData = this.generateTransportTimeData();
        const transportTraces = transportTimeData.modes.map((mode, index) => ({
            x: transportTimeData.dates,
            y: transportTimeData.data[mode],
            type: 'scatter',
            mode: 'lines',
            name: mode,
            line: { color: ['#00d4aa', '#0084ff', '#ff6b6b', '#ffa726'][index] }
        }));
        
        const transportTimeLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Emissions (kg CO2e)' },
            margin: { t: 20, r: 20, b: 40, l: 60 },
            legend: { orientation: 'h', y: -0.2 }
        };
        
        Plotly.newPlot('transportModeEmissionsChart', transportTraces, transportTimeLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Route Efficiency Chart
        const efficiencyData = this.generateRouteEfficiencyData();
        const efficiencyTrace = {
            x: efficiencyData.routes,
            y: efficiencyData.efficiency,
            type: 'bar',
            marker: { 
                color: efficiencyData.efficiency.map(e => e > 85 ? '#00d4aa' : e > 70 ? '#ffa726' : '#ff6b6b')
            }
        };
        
        const efficiencyLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Route' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Efficiency %', range: [0, 100] },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('routeEfficiencyChart', [efficiencyTrace], efficiencyLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Fleet Utilization Chart
        const fleetData = this.generateFleetUtilizationData();
        const fleetTrace = {
            x: fleetData.hours,
            y: fleetData.utilization,
            type: 'scatter',
            mode: 'lines+markers',
            fill: 'tonexty',
            line: { color: '#00d4aa', width: 2 },
            marker: { color: '#00d4aa', size: 6 }
        };
        
        const fleetLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Hour of Day' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Utilization %', range: [0, 100] },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('fleetUtilizationChart', [fleetTrace], fleetLayout, {
            responsive: true,
            displayModeBar: false
        });
    }
    
    initEnergyCharts() {
        // Energy Consumption Pattern
        const energyData = this.generateEnergyConsumptionData();
        const energyTrace = {
            x: energyData.hours,
            y: energyData.consumption,
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            line: { color: '#0084ff', width: 2 },
            fillcolor: 'rgba(0, 132, 255, 0.1)'
        };
        
        const energyLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Hour of Day' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Consumption (kWh)' },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('energyConsumptionChart', [energyTrace], energyLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Energy Sources Chart
        const sourcesData = [
            { source: 'Grid', value: 70, color: '#ff6b6b' },
            { source: 'Solar', value: 20, color: '#ffa726' },
            { source: 'Wind', value: 8, color: '#00d4aa' },
            { source: 'Others', value: 2, color: '#ab47bc' }
        ];
        
        const sourcesTrace = {
            labels: sourcesData.map(d => d.source),
            values: sourcesData.map(d => d.value),
            type: 'pie',
            hole: 0.5,
            marker: { colors: sourcesData.map(d => d.color) },
            textinfo: 'label+percent',
            textfont: { color: '#ffffff' }
        };
        
        const sourcesLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            margin: { t: 20, r: 20, b: 20, l: 20 },
            showlegend: false
        };
        
        Plotly.newPlot('energySourcesChart', [sourcesTrace], sourcesLayout, {
            responsive: true,
            displayModeBar: false
        });
        
        // Peak Usage Hours Chart
        const peakData = this.generatePeakUsageData();
        const peakTrace = {
            x: peakData.days,
            y: peakData.peaks,
            type: 'bar',
            marker: { 
                color: peakData.peaks.map((peak, index) => 
                    ['Saturday', 'Sunday'].includes(peakData.days[index]) ? '#ab47bc' : '#0084ff'
                )
            }
        };
        
        const peakLayout = {
            title: false,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#ffffff', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)' },
            yaxis: { gridcolor: 'rgba(255, 255, 255, 0.1)', title: 'Peak Usage (kWh)' },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };
        
        Plotly.newPlot('peakUsageChart', [peakTrace], peakLayout, {
            responsive: true,
            displayModeBar: false
        });
    }
    
    // Data generation methods for new charts
    generateMonthlyEmissionsData() {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const values = months.map(() => (Math.random() * 10 + 20).toFixed(1));
        return { months, values };
    }
    
    generateTransportTimeData() {
        const modes = ['Road', 'Rail', 'Air', 'Sea'];
        const dates = [];
        const data = {};
        
        // Generate last 30 days
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }
        
        modes.forEach(mode => {
            data[mode] = dates.map(() => Math.random() * 1000 + 500);
        });
        
        return { modes, dates, data };
    }
    
    generateRouteEfficiencyData() {
        const routes = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8'];
        const efficiency = routes.map(() => Math.random() * 40 + 60);
        return { routes, efficiency };
    }
    
    generateFleetUtilizationData() {
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const utilization = hours.map(hour => {
            if (hour >= 6 && hour <= 18) {
                return Math.random() * 30 + 60; // Higher during day
            } else {
                return Math.random() * 40 + 10; // Lower at night
            }
        });
        return { hours, utilization };
    }
    
    generateEnergyConsumptionData() {
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const consumption = hours.map(hour => {
            if (hour >= 8 && hour <= 17) {
                return Math.random() * 200 + 300; // Higher during business hours
            } else {
                return Math.random() * 100 + 50; // Lower at night
            }
        });
        return { hours, consumption };
    }
    
    generatePeakUsageData() {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const peaks = days.map(day => {
            if (['Saturday', 'Sunday'].includes(day)) {
                return Math.random() * 100 + 50; // Lower on weekends
            } else {
                return Math.random() * 150 + 200; // Higher on weekdays
            }
        });
        return { days, peaks };
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, checking dependencies...');
    
    // Check if Plotly is loaded
    if (typeof Plotly === 'undefined') {
        console.error('Plotly.js not loaded! Charts will not work.');
        document.body.innerHTML = `
            <div style="text-align: center; margin-top: 50px; color: #ff4444;">
                <h2>Error: Plotly.js not loaded</h2>
                <p>Please check your internet connection and refresh the page.</p>
            </div>
        `;
        return;
    }
    
    console.log('All dependencies loaded, starting dashboard...');
    window.carbonDashboard = new CarbonDashboard();
});

// Add some CSS animations that weren't in the CSS file
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .error-toast {
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
`;
document.head.appendChild(style);