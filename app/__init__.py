"""
EmPy - Image File Embedder
A modern tool for embedding files into images securely
"""

import logging
import sys

# Configure root logger for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('empy.log')
    ]
)

# Reduce noise from other libraries
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('fastapi').setLevel(logging.WARNING)

# Get application logger
logger = logging.getLogger(__name__)
logger.info("EmPy application initialized") 