"""
FastAPI backend for Failure Viewer App.
"""

from config import create_app
import routes

# Create FastAPI app
app = create_app()

# Register routes
app.get("/")(routes.root)
app.get("/api/health")(routes.health_check)
app.get("/api/projects")(routes.list_projects)
app.get("/api/projects/{project_name}")(routes.load_project)
app.post("/api/projects/{project_name}/filter")(routes.filter_tasks)
app.get("/api/projects/{project_name}/samples/{sample_id}")(routes.get_sample)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

