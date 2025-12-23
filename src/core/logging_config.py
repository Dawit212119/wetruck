import logging

# Create a logger
logger = logging.getLogger("platform_backend")
logger.setLevel(logging.INFO)

# Create console handler if it doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)






