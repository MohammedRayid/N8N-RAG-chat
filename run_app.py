import subprocess
import os
import sys
import time

def main():
    print("Starting N8N RAG Chat App...")
    print("=" * 50)

    # Path to frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')

    # Start backend server
    print("Starting backend server on http://localhost:5000...")
    backend_process = subprocess.Popen([sys.executable, 'server.py'], cwd=os.path.dirname(__file__), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Give time for backend to start and load models

    # Start frontend HTTP server
    print("Starting frontend server on http://localhost:3000...")
    frontend_process = subprocess.Popen([sys.executable, '-m', 'http.server', '3000'], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("\n" + "=" * 50)
    print("Both servers are running!")
    print("Open http://localhost:3000 in your browser to use the app.")
    print("Press Ctrl+C to stop both servers.")
    print("=" * 50 + "\n")

    try:
        # Keep running until interrupted
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        # Clean shutdown
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("All servers stopped.")

if __name__ == "__main__":
    main()
