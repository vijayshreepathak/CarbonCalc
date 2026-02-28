"""
Modern Carbon Intelligence Platform - FastAPI Backend
Serves real-time carbon emissions data from CSV files
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Dict, List, Optional
import uvicorn

app = FastAPI(title="Carbon Intelligence Platform API", version="2.0.0")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Serve static files (CSS, JS, etc.) - must come before root handler
app.mount("/static", StaticFiles(directory="."), name="static")

# Route specific static files for direct access
@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css", media_type="text/css")

@app.get("/app.js") 
async def serve_js():
    return FileResponse("app.js", media_type="application/javascript")

# Configuration
DATA_DIR = Path("../data/streams")
EMISSION_FACTORS = {
    'road': 0.12,  # kg CO2e per ton-km
    'rail': 0.04,
    'air': 0.8,
    'sea': 0.02,
    'electricity': 0.5  # kg CO2e per kWh
}

class CarbonDataProcessor:
    def __init__(self):
        self.data_cache = {}
        self.cache_timestamp = {}
        self.cache_ttl = 2  # seconds
    
    def load_csv_with_cache(self, csv_path: str) -> pd.DataFrame:
        """Load CSV with caching to improve performance"""
        cache_key = str(csv_path)
        current_time = datetime.now()
        
        # Check if file exists
        if not os.path.exists(csv_path):
            return pd.DataFrame()
        
        # Check file modification time
        file_mtime = datetime.fromtimestamp(os.path.getmtime(csv_path))
        
        # Check cache validity
        if (cache_key in self.data_cache and 
            cache_key in self.cache_timestamp and
            (current_time - self.cache_timestamp[cache_key]).seconds < self.cache_ttl and
            file_mtime <= self.cache_timestamp[cache_key]):
            return self.data_cache[cache_key]
        
        try:
            # Load CSV with error handling
            df = pd.read_csv(csv_path, skip_blank_lines=True)
            
            # Cache the data
            self.data_cache[cache_key] = df
            self.cache_timestamp[cache_key] = current_time
            
            return df
        except Exception as e:
            print(f"Error loading {csv_path}: {e}")
            return pd.DataFrame()
    
    def calculate_transport_emissions(self, shipments_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate transport emissions from shipments data"""
        if shipments_df.empty:
            return pd.DataFrame()
        
        # Clean column names if they have extra fields
        if len(shipments_df.columns) > 15:
            expected_cols = ['shipment_id', 'event_time', 'period_date', 'origin_city', 'origin_state', 
                           'destination_city', 'destination_state', 'mode', 'distance_km', 'weight_tons',
                           'sku', 'quantity', 'supplier_id', 'facility_id', 'urgent_flag']
            shipments_df = shipments_df.iloc[:, :15]
            shipments_df.columns = expected_cols
        
        # Convert event_time to datetime
        try:
            shipments_df['event_time'] = pd.to_datetime(shipments_df['event_time'], utc=True, errors='coerce')
        except:
            shipments_df['event_time'] = pd.to_datetime(shipments_df['event_time'], errors='coerce')
        
        # Remove rows with invalid datetime
        shipments_df = shipments_df.dropna(subset=['event_time'])
        
        if shipments_df.empty:
            return pd.DataFrame()
        
        shipments_df['date'] = shipments_df['event_time'].dt.date
        
        # Calculate emissions
        shipments_df['emission_factor'] = shipments_df['mode'].map(EMISSION_FACTORS).fillna(0.12)
        shipments_df['distance_km'] = pd.to_numeric(shipments_df['distance_km'], errors='coerce').fillna(0)
        shipments_df['weight_tons'] = pd.to_numeric(shipments_df['weight_tons'], errors='coerce').fillna(0)
        
        shipments_df['kg_co2e'] = (
            shipments_df['distance_km'] * 
            shipments_df['weight_tons'] * 
            shipments_df['emission_factor']
        )
        
        return shipments_df
    
    def calculate_electricity_emissions(self, bills_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate electricity emissions from bills data"""
        if bills_df.empty:
            return pd.DataFrame()
        
        # Convert event_time to datetime
        try:
            bills_df['event_time'] = pd.to_datetime(bills_df['event_time'], utc=True, errors='coerce')
        except:
            bills_df['event_time'] = pd.to_datetime(bills_df['event_time'], errors='coerce')
        
        # Remove rows with invalid datetime
        bills_df = bills_df.dropna(subset=['event_time'])
        
        if bills_df.empty:
            return pd.DataFrame()
        
        bills_df['date'] = bills_df['event_time'].dt.date
        
        # Calculate emissions
        bills_df['kwh'] = pd.to_numeric(bills_df['kwh'], errors='coerce').fillna(0)
        bills_df['kg_co2e'] = bills_df['kwh'] * EMISSION_FACTORS['electricity']
        
        return bills_df
    
    def get_summary_data(self) -> Dict:
        """Get comprehensive summary data"""
        # Load data
        shipments_df = self.load_csv_with_cache(DATA_DIR / "shipments_stream.csv")
        electricity_df = self.load_csv_with_cache(DATA_DIR / "electricity_bills_stream.csv")
        suppliers_df = self.load_csv_with_cache(DATA_DIR / "suppliers_stream.csv")
        
        # Calculate emissions
        transport_emissions = self.calculate_transport_emissions(shipments_df)
        electricity_emissions = self.calculate_electricity_emissions(electricity_df)
        
        # Calculate totals
        total_transport = transport_emissions['kg_co2e'].sum() if not transport_emissions.empty else 0
        total_electricity = electricity_emissions['kg_co2e'].sum() if not electricity_emissions.empty else 0
        total_emissions = total_transport + total_electricity
        
        # Calculate purchased goods (simplified)
        total_purchased = 0
        if not shipments_df.empty and not suppliers_df.empty:
            try:
                merged = shipments_df.merge(
                    suppliers_df[['supplier_id', 'emissions_intensity_kgco2e_per_unit']], 
                    on='supplier_id', 
                    how='left'
                )
                merged['quantity'] = pd.to_numeric(merged['quantity'], errors='coerce').fillna(0)
                merged['intensity'] = pd.to_numeric(merged['emissions_intensity_kgco2e_per_unit'], errors='coerce').fillna(0.5)
                total_purchased = (merged['quantity'] * merged['intensity']).sum()
                total_emissions += total_purchased
            except:
                total_purchased = 0
        
        # Get daily trend (last 30 days)
        trend_data = self.get_daily_trend(transport_emissions, electricity_emissions)
        
        # Get transport mode breakdown
        transport_modes = {}
        if not transport_emissions.empty:
            transport_modes = transport_emissions.groupby('mode')['kg_co2e'].sum().to_dict()
        
        # Get recent activity
        recent_activity = self.get_recent_activity(transport_emissions, electricity_emissions)
        
        # Get hotspots
        hotspots = self.get_hotspots(transport_emissions, electricity_emissions, shipments_df)
        
        return {
            'summary': {
                'totalEmissions': float(total_emissions),
                'totalActivities': len(transport_emissions) + len(electricity_emissions),
                'transportEmissions': float(total_transport),
                'electricityEmissions': float(total_electricity),
                'purchasedGoodsEmissions': float(total_purchased),
                'lastUpdate': datetime.now().isoformat()
            },
            'trendData': trend_data,
            'categories': {
                'Transport': float(total_transport),
                'Electricity': float(total_electricity),
                'Purchased Goods': float(total_purchased)
            },
            'transportModes': {k: float(v) for k, v in transport_modes.items()},
            'recentActivity': recent_activity,
            'hotspots': hotspots
        }
    
    def get_daily_trend(self, transport_df: pd.DataFrame, electricity_df: pd.DataFrame) -> List[Dict]:
        """Get daily emissions trend for the last 30 days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        trend_data = []
        
        for date in date_range:
            date_obj = date.date()
            
            # Transport emissions for this date
            transport_day = 0
            if not transport_df.empty:
                day_transport = transport_df[transport_df['date'] == date_obj]
                transport_day = day_transport['kg_co2e'].sum()
            
            # Electricity emissions for this date
            electricity_day = 0
            if not electricity_df.empty:
                day_electricity = electricity_df[electricity_df['date'] == date_obj]
                electricity_day = day_electricity['kg_co2e'].sum()
            
            trend_data.append({
                'date': date_obj.isoformat(),
                'transport': float(transport_day),
                'electricity': float(electricity_day),
                'total': float(transport_day + electricity_day)
            })
        
        return trend_data
    
    def get_recent_activity(self, transport_df: pd.DataFrame, electricity_df: pd.DataFrame) -> List[Dict]:
        """Get recent activity feed"""
        activities = []
        
        # Get recent transport activities
        if not transport_df.empty:
            recent_transport = transport_df.nlargest(5, 'event_time')
            for _, row in recent_transport.iterrows():
                activities.append({
                    'type': 'transport',
                    'title': f"{row['mode'].title()} Transport",
                    'details': f"{row['distance_km']:.0f}km, {row['weight_tons']:.1f} tons",
                    'value': f"{row['kg_co2e']:.2f} kg CO2e",
                    'timestamp': row['event_time'].strftime('%H:%M:%S') if pd.notna(row['event_time']) else '00:00:00',
                    'icon': self.get_transport_icon(row['mode'])
                })
        
        # Get recent electricity activities
        if not electricity_df.empty:
            recent_electricity = electricity_df.nlargest(5, 'event_time')
            for _, row in recent_electricity.iterrows():
                activities.append({
                    'type': 'electricity',
                    'title': 'Electricity Usage',
                    'details': f"{row['kwh']:.0f} kWh",
                    'value': f"{row['kg_co2e']:.2f} kg CO2e",
                    'timestamp': row['event_time'].strftime('%H:%M:%S') if pd.notna(row['event_time']) else '00:00:00',
                    'icon': 'fas fa-bolt'
                })
        
        # Sort by timestamp and return top 10
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]
    
    def get_transport_icon(self, mode: str) -> str:
        """Get icon for transport mode"""
        icons = {
            'road': 'fas fa-truck',
            'rail': 'fas fa-train',
            'air': 'fas fa-plane',
            'sea': 'fas fa-ship'
        }
        return icons.get(mode, 'fas fa-truck')
    
    def get_hotspots(self, transport_df: pd.DataFrame, electricity_df: pd.DataFrame, shipments_df: pd.DataFrame) -> Dict:
        """Get hotspot analysis"""
        hotspots = {
            'suppliers': [],
            'routes': [],
            'skus': [],
            'facilities': []
        }
        
        try:
            # Supplier hotspots
            if not transport_df.empty and 'supplier_id' in transport_df.columns:
                supplier_emissions = transport_df.groupby('supplier_id')['kg_co2e'].sum().nlargest(5)
                hotspots['suppliers'] = [
                    {'name': supplier, 'value': f"{emissions:.1f}"}
                    for supplier, emissions in supplier_emissions.items()
                ]
            
            # Route hotspots (origin-destination pairs)
            if not transport_df.empty:
                transport_df['route'] = transport_df['origin_city'] + '-' + transport_df['destination_city']
                route_emissions = transport_df.groupby('route')['kg_co2e'].sum().nlargest(5)
                hotspots['routes'] = [
                    {'name': route, 'value': f"{emissions:.1f}"}
                    for route, emissions in route_emissions.items()
                ]
            
            # SKU hotspots
            if not transport_df.empty and 'sku' in transport_df.columns:
                sku_emissions = transport_df.groupby('sku')['kg_co2e'].sum().nlargest(5)
                hotspots['skus'] = [
                    {'name': sku, 'value': f"{emissions:.1f}"}
                    for sku, emissions in sku_emissions.items()
                ]
            
            # Facility hotspots (combine transport and electricity)
            facility_emissions = {}
            
            if not transport_df.empty and 'facility_id' in transport_df.columns:
                transport_facilities = transport_df.groupby('facility_id')['kg_co2e'].sum()
                facility_emissions.update(transport_facilities.to_dict())
            
            if not electricity_df.empty and 'facility_id' in electricity_df.columns:
                electricity_facilities = electricity_df.groupby('facility_id')['kg_co2e'].sum()
                for facility, emissions in electricity_facilities.items():
                    facility_emissions[facility] = facility_emissions.get(facility, 0) + emissions
            
            if facility_emissions:
                top_facilities = sorted(facility_emissions.items(), key=lambda x: x[1], reverse=True)[:5]
                hotspots['facilities'] = [
                    {'name': facility, 'value': f"{emissions:.1f}"}
                    for facility, emissions in top_facilities
                ]
        
        except Exception as e:
            print(f"Error calculating hotspots: {e}")
        
        return hotspots

# Initialize data processor
data_processor = CarbonDataProcessor()

@app.get("/")
async def serve_index():
    """Serve the main dashboard page"""
    return FileResponse("index.html")

@app.get("/standalone")
async def serve_standalone():
    """Serve the standalone dashboard with embedded CSS/JS"""
    return FileResponse("standalone.html")

@app.get("/api/summary")
async def get_summary():
    """Get comprehensive dashboard summary data"""
    try:
        data = data_processor.get_summary_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "carbon-intelligence-api",
        "version": "2.0.0"
    }

@app.get("/api/data-status")
async def get_data_status():
    """Get data file status"""
    status = {}
    
    for filename in ["shipments_stream.csv", "suppliers_stream.csv", "electricity_bills_stream.csv"]:
        filepath = DATA_DIR / filename
        if filepath.exists():
            stat = filepath.stat()
            status[filename] = {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "rows": len(pd.read_csv(filepath)) if filepath.suffix == '.csv' else 0
            }
        else:
            status[filename] = {"exists": False}
    
    return status

if __name__ == "__main__":
    print("Starting Modern Carbon Intelligence Platform")
    print("Dashboard: http://localhost:8001")
    print("API: http://localhost:8001/api/summary")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        reload=False,
        log_level="info"
    )