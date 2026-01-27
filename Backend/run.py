import uvicorn
import sys
import os

if __name__ == "__main__":
    print("🚀 Starting SurfaceLabs Backend with Programmatic Reload Exclusions...")
    
    # Use strict reload_dirs to ONLY watch code folders.
    # This prevents uvicorn from even looking at app/storage or app/logs,
    # which avoids the infinite reload loop and the "extra arguments" error.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[
            "app/api",
            "app/core",
            "app/schemas",
            "app/services",
            "app/utils",
        ],
        reload_excludes=["**/.venv/*", "**/__pycache__/*"]
    )
