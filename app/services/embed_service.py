from PIL import Image
import os
import tempfile
import logging
import time
import sys
import base64
import magic
from stegano import lsb
from stegano.lsb import generators
import hashlib

# Configure more detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_file_extension(file_path: str) -> str:
    """Get file extension using python-magic"""
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        logger.info(f"Detected MIME type: {mime_type}")
        
        # Map common MIME types to extensions
        mime_to_ext = {
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-7z-compressed': '.7z',
            'text/plain': '.txt',
            'text/html': '.html',
            'application/json': '.json',
            'application/xml': '.xml',
            'application/x-msdownload': '.exe',  # Added for Windows executables
            'application/x-dosexec': '.exe',     # Alternative MIME type for executables
            'application/octet-stream': '.bin'  # Default for unknown binary
        }
        
        extension = mime_to_ext.get(mime_type, '.bin')
        logger.info(f"Using extension: {extension}")
        return extension
    except Exception as e:
        logger.error(f"Error detecting file type: {str(e)}")
        return '.bin'  # Default extension if detection fails

def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary by looking for non-text characters"""
    try:
        with open(file_path, 'rb') as f:
            # Read first 1024 bytes
            data = f.read(1024)
            # Check for non-text characters
            return any(byte > 127 for byte in data)
    except Exception as e:
        logger.error(f"Error checking file type: {str(e)}")
        return False

def embed_file_in_image(image_path: str, file_path: str) -> str:
    """Embeds a file into an image using LSB steganography with Stegano"""
    start_time = time.time()
    logger.info(f"Starting Stegano embedding process")
    logger.info(f"Carrier image: {os.path.basename(image_path)}")
    logger.info(f"File to embed: {os.path.basename(file_path)}")
    
    try:
        # Log file details
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")
        
        # Check if file is binary
        is_binary = is_binary_file(file_path)
        logger.info(f"File type: {'Binary' if is_binary else 'Text'}")
        
        # Use Stegano with Eratosthenes generator for better pixel selection
        try:
            embed_start = time.time()
            output_path = tempfile.mktemp(suffix='.png')
            logger.info(f"Using Eratosthenes generator for pixel selection")
            
            # Convert image to RGB if needed
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    logger.info(f"Converting image from {img.mode} to RGB mode")
                    img = img.convert('RGB')
                    # Save the converted image to a temporary file
                    temp_img_path = tempfile.mktemp(suffix='.png')
                    img.save(temp_img_path)
                    image_path = temp_img_path
            
            # Use Stegano's direct file embedding
            logger.info("Starting Stegano hide operation")
            if is_binary:
                # For binary files, read and encode as base64
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                encoded_data = base64.b64encode(file_data).decode('utf-8')
                secret = lsb.hide(image_path, encoded_data, generators.eratosthenes())
            else:
                # For text files, use direct file path
                secret = lsb.hide(image_path, file_path, generators.eratosthenes())
            
            secret.save(output_path)
            
            # Clean up temporary converted image if it was created
            if 'temp_img_path' in locals():
                os.remove(temp_img_path)
            
            embed_time = time.time() - embed_start
            logger.info(f"Stegano hide operation completed in {embed_time:.2f}s")
            
            # Check output file details
            output_size = os.path.getsize(output_path)
            logger.info(f"Output image size: {output_size} bytes")
            logger.info(f"Output saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Stegano hide operation failed: {str(e)}")
            raise ValueError(f"Failed to embed data into image: {str(e)}")
        
        total_time = time.time() - start_time
        logger.info(f"Embedding process completed successfully in {total_time:.2f}s")
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error during embedding (after {total_time:.2f}s): {str(e)}")
        raise ValueError(f"Failed to embed file: {str(e)}")

def extract_file_from_image(image_path: str) -> str:
    """Extracts an embedded file from an image using Stegano"""
    start_time = time.time()
    logger.info(f"Starting Stegano extraction process")
    logger.info(f"Source image: {os.path.basename(image_path)}")
    
    try:
        # Use Stegano with Eratosthenes generator to extract the hidden data
        try:
            extract_start = time.time()
            logger.info(f"Using Eratosthenes generator for extraction")
            
            # Use Stegano's direct file extraction
            logger.info("Starting Stegano reveal operation")
            extracted_data = lsb.reveal(image_path, generators.eratosthenes())
            
            # Try to decode as base64 first (binary file)
            try:
                logger.info("Attempting to decode as base64 (binary file)")
                decoded_data = base64.b64decode(extracted_data)
                
                # Create a temporary file to detect its type
                temp_input = tempfile.mktemp(suffix='_temp')
                with open(temp_input, 'wb') as f:
                    f.write(decoded_data)
                
                # Get the correct extension
                extension = get_file_extension(temp_input)
                output_path = tempfile.mktemp(suffix=extension)
                
                # Save the decoded data with correct extension
                with open(output_path, 'wb') as f:
                    f.write(decoded_data)
                
                # Clean up temporary file
                os.remove(temp_input)
                
                logger.info("Successfully decoded as binary file")
            except:
                # If base64 decode fails, treat as text
                logger.info("Treating as text file")
                output_path = tempfile.mktemp(suffix='.txt')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_data)
            
            extract_time = time.time() - extract_start
            logger.info(f"Stegano reveal operation completed in {extract_time:.2f}s")
            
            # Log extraction details
            if os.path.exists(output_path):
                extracted_size = os.path.getsize(output_path)
                logger.info(f"Extracted file size: {extracted_size} bytes")
                logger.info(f"Extracted file saved to: {output_path}")
            else:
                logger.error("Extracted file was not created")
                raise ValueError("Failed to create extracted file")
            
        except Exception as e:
            logger.error(f"Stegano reveal operation failed: {str(e)}")
            raise ValueError(f"Failed to extract data from image: {str(e)}")
        
        total_time = time.time() - start_time
        logger.info(f"Extraction process completed successfully in {total_time:.2f}s")
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error during extraction (after {total_time:.2f}s): {str(e)}")
        raise ValueError(f"Failed to extract file: {str(e)}") 