import os
import PyInstaller.__main__
import sys

def build():
    print("Building PyInstaller Executable...")
    
    # Determine critical paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    entry_point = os.path.join(project_root, "run_desktop.py")
    frontend_dir = os.path.join(project_root, "frontend")
    backend_dir = os.path.join(project_root, "backend")
    
    # Windows uses ; for separating source and destination in --add-data
    # macOS/Linux use :
    sep = os.pathsep
    
    # Hidden imports required by Uvicorn and FastAPI under Pyinstaller
    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off"
    ]
    
    # Base PyInstaller Command
    # --onedir creates a directory with the `exe` and supporting files. 
    # This is typically much faster to launch than --onefile.
    cmd = [
        entry_point,
        "--name=EmailExtractionSystem",
        "--noconfirm",         # Overwrite output directory without asking
        "--clean",             # Clean PyInstaller cache
        "--onedir",            # Directory structure (recommended for webapps)
        
        # Bundle the frontend directory into the _MEIPASS root
        f"--add-data={frontend_dir}{sep}frontend",
        
        # Add the backend directory to python module search paths
        # so `app.*` imports are correctly discovered by PyInstaller.
        f"--paths={backend_dir}"
    ]
    
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")
        
    print(f"Running PyInstaller with arguments:\n{' '.join(cmd)}")
    PyInstaller.__main__.run(cmd)
    
    print("\n-------------------------")
    print("Build successful!")
    print(f"You can find the executable at: {os.path.join(project_root, 'dist', 'EmailExtractionSystem')}")
    print("Run `dist\\EmailExtractionSystem\\EmailExtractionSystem.exe` to test.")
    print("-------------------------")

if __name__ == "__main__":
    build()
