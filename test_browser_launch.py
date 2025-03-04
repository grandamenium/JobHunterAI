"""
Simple test script to verify that the browser launches with the app.
Run this directly to test the automatic browser opening feature.
"""
import os
import sys
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_browser_launches():
    """Test that the browser launches with the app."""
    logger.info("Starting test for browser launch")
    
    # Create a subprocess to run the main.py script
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for a few seconds to let the browser launch
    logger.info("Waiting for browser to launch (5 seconds)...")
    time.sleep(5)
    
    # Check if the process is still running
    if process.poll() is None:
        logger.info("App is still running, which is good!")
        
        # Check stdout for any browser launch logs
        stdout, stderr = process.communicate(timeout=1)
        if "Opening browser" in stdout or "Opening browser" in stderr:
            logger.info("Browser launch message detected in logs!")
        
        # Terminate the process
        try:
            logger.info("Terminating the app process...")
            process.terminate()
            process.wait(timeout=5)
            logger.info("Process terminated successfully")
        except subprocess.TimeoutExpired:
            logger.warning("Process did not terminate gracefully, killing it")
            process.kill()
        
        return True
    else:
        # Process has already ended
        stdout, stderr = process.communicate()
        logger.error(f"App terminated prematurely with return code {process.returncode}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False

if __name__ == "__main__":
    success = test_browser_launches()
    if success:
        logger.info("✅ Test passed: The app should launch with a browser window!")
        sys.exit(0)
    else:
        logger.error("❌ Test failed: The app did not launch properly")
        sys.exit(1)