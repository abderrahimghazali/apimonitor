"""
Optional web dashboard for ApiMonitor
"""

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
    
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False


if DASHBOARD_AVAILABLE:
    
    def create_dashboard_app(monitor):
        """Create FastAPI dashboard application"""
        
        app = FastAPI(
            title="ApiMonitor Dashboard",
            description="API Health Monitoring Dashboard",
            version="1.0.0"
        )
        
        # Templates (you would need to create these HTML templates)
        templates = Jinja2Templates(directory="templates")
        
        @app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            summary = monitor.get_health_summary()
            return templates.TemplateResponse(
                "dashboard.html", 
                {"request": request, "summary": summary}
            )
        
        @app.get("/api/health")
        async def api_health():
            """API health summary"""
            return monitor.get_health_summary()
        
        @app.get("/api/stats")
        async def api_stats():
            """Get all endpoint statistics"""
            return {k: v.dict() for k, v in monitor.get_all_stats().items()}
        
        @app.get("/api/stats/{endpoint_id}")
        async def api_endpoint_stats(endpoint_id: str):
            """Get stats for specific endpoint"""
            stats = monitor.get_endpoint_stats(endpoint_id)
            if stats:
                return stats.dict()
            return {"error": "Endpoint not found"}
        
        @app.get("/api/results/{endpoint_id}")
        async def api_endpoint_results(endpoint_id: str, hours: int = 24):
            """Get recent results for endpoint"""
            results = monitor.get_recent_results(endpoint_id, hours)
            return [r.dict() for r in results]
        
        return app
    
    async def start_dashboard_server(monitor, host: str = "127.0.0.1", port: int = 8080):
        """Start the dashboard server"""
        app = create_dashboard_app(monitor)
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

else:
    def create_dashboard_app(monitor):
        raise ImportError("Dashboard dependencies not installed")
    
    async def start_dashboard_server(monitor, host: str = "127.0.0.1", port: int = 8080):
        raise ImportError("Dashboard dependencies not installed")