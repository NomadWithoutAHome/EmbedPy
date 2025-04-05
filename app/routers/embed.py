from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse, JSONResponse
from ..services.embed_service import embed_file_in_image, extract_file_from_image
from pathlib import Path
import tempfile
import shutil
import logging
import time
import os
import traceback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/embed", tags=["embed"])

def cleanup_temp_file(filepath: str):
    try:
        Path(filepath).unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Failed to cleanup temporary file {filepath}: {str(e)}")

@router.post("/embed")
async def embed_file(
    background_tasks: BackgroundTasks,
    carrier_image: UploadFile = File(...),
    file_to_embed: UploadFile = File(...)
):
    temp_image = None
    temp_file = None
    output_path = None
    process_start = time.time()
    
    try:
        # Gather debug info
        debug_info = {
            "carrier_image": {
                "filename": carrier_image.filename,
                "content_type": carrier_image.content_type,
                "size": 0
            },
            "file_to_embed": {
                "filename": file_to_embed.filename,
                "content_type": file_to_embed.content_type,
                "size": 0
            },
            "timestamps": {
                "start": process_start
            }
        }
        
        # Validate file types
        if not carrier_image.content_type.startswith('image/'):
            raise ValueError("Carrier file must be an image")
        
        logger.info(f"Processing embedding request: {carrier_image.filename} + {file_to_embed.filename}")
        
        # Create temporary files
        temp_image = tempfile.NamedTemporaryFile(delete=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        # Copy uploaded files to temporary files
        try:
            debug_info["timestamps"]["copy_start"] = time.time()
            
            # Copy carrier image
            carrier_content = await carrier_image.read()
            debug_info["carrier_image"]["size"] = len(carrier_content)
            temp_image.write(carrier_content)
            
            # Copy file to embed
            embed_content = await file_to_embed.read()
            debug_info["file_to_embed"]["size"] = len(embed_content)
            temp_file.write(embed_content)
            
            debug_info["timestamps"]["copy_end"] = time.time()
            logger.info(f"Files copied: Carrier ({debug_info['carrier_image']['size']} bytes), "
                       f"To embed ({debug_info['file_to_embed']['size']} bytes)")
            
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Failed to process uploaded files: {str(e)}\n{trace}")
            raise ValueError(f"Failed to process uploaded files: {str(e)}")
        
        # Close the files to ensure all data is written
        temp_image.close()
        temp_file.close()
        
        # Perform the embedding
        debug_info["timestamps"]["embed_start"] = time.time()
        output_path = embed_file_in_image(temp_image.name, temp_file.name)
        debug_info["timestamps"]["embed_end"] = time.time()
        
        # Get output file size
        output_size = os.path.getsize(output_path)
        debug_info["output_file"] = {
            "path": output_path,
            "size": output_size
        }
        
        total_time = time.time() - process_start
        debug_info["timestamps"]["end"] = time.time()
        debug_info["total_time"] = total_time
        
        logger.info(f"Embedding completed in {total_time:.2f}s. Output size: {output_size} bytes")
        
        # Schedule cleanup after response is sent
        background_tasks.add_task(cleanup_temp_file, temp_image.name)
        background_tasks.add_task(cleanup_temp_file, temp_file.name)
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        # Add debug headers
        response = FileResponse(
            output_path,
            media_type="image/png",
            filename=f"embedded_{carrier_image.filename}"
        )
        
        # Add custom headers with debug info
        response.headers["X-Processing-Time"] = f"{total_time:.2f}s"
        response.headers["X-Embedding-Info"] = f"Carrier: {debug_info['carrier_image']['size']} bytes, Embedded: {debug_info['file_to_embed']['size']} bytes"
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error during embedding: {str(e)}")
        # Clean up files immediately on error
        if temp_image:
            cleanup_temp_file(temp_image.name)
        if temp_file:
            cleanup_temp_file(temp_file.name)
        if output_path:
            cleanup_temp_file(output_path)
            
        # Return detailed error
        total_time = time.time() - process_start
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(e),
                "debug_info": {
                    "process_time": f"{total_time:.2f}s",
                    "carrier_image": carrier_image.filename,
                    "file_to_embed": file_to_embed.filename,
                    "error_type": "validation_error"
                }
            }
        )
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Unexpected error during embedding: {str(e)}\n{trace}")
        # Clean up files immediately on error
        if temp_image:
            cleanup_temp_file(temp_image.name)
        if temp_file:
            cleanup_temp_file(temp_file.name)
        if output_path:
            cleanup_temp_file(output_path)
            
        # Return error info
        total_time = time.time() - process_start
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error during embedding process",
                "debug_info": {
                    "process_time": f"{total_time:.2f}s",
                    "error": str(e),
                    "error_type": "server_error"
                }
            }
        )

@router.post("/extract")
async def extract_file(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...)
):
    temp_image = None
    extracted_path = None
    process_start = time.time()
    
    try:
        # Gather debug info
        debug_info = {
            "image": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size": 0
            },
            "timestamps": {
                "start": process_start
            }
        }
        
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise ValueError("Uploaded file must be an image")
        
        logger.info(f"Processing extraction request: {image.filename}")
        
        # Create temporary file
        temp_image = tempfile.NamedTemporaryFile(delete=False)
        
        # Copy uploaded file to temporary file
        try:
            debug_info["timestamps"]["copy_start"] = time.time()
            image_content = await image.read()
            debug_info["image"]["size"] = len(image_content)
            temp_image.write(image_content)
            debug_info["timestamps"]["copy_end"] = time.time()
            
            logger.info(f"Image copied: {debug_info['image']['filename']} ({debug_info['image']['size']} bytes)")
            
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Failed to process uploaded file: {str(e)}\n{trace}")
            raise ValueError(f"Failed to process uploaded file: {str(e)}")
        
        # Close the file to ensure all data is written
        temp_image.close()
        
        # Perform the extraction
        debug_info["timestamps"]["extract_start"] = time.time()
        extracted_path = extract_file_from_image(temp_image.name)
        debug_info["timestamps"]["extract_end"] = time.time()
        
        # Get the extracted filename
        extracted_filename = os.path.basename(extracted_path)
        base_filename = extracted_filename.split('_', 1)[1] if '_' in extracted_filename else extracted_filename
        
        # Get extracted file size
        extracted_size = os.path.getsize(extracted_path)
        debug_info["extracted_file"] = {
            "path": extracted_path,
            "size": extracted_size,
            "filename": base_filename
        }
        
        total_time = time.time() - process_start
        debug_info["timestamps"]["end"] = time.time()
        debug_info["total_time"] = total_time
        
        logger.info(f"Extraction completed in {total_time:.2f}s. Extracted file: {base_filename} ({extracted_size} bytes)")
        
        # Schedule cleanup after response is sent
        background_tasks.add_task(cleanup_temp_file, temp_image.name)
        background_tasks.add_task(cleanup_temp_file, extracted_path)
        
        # Add debugging headers
        response = FileResponse(
            extracted_path,
            filename=base_filename
        )
        
        # Add custom headers with debug info
        response.headers["X-Processing-Time"] = f"{total_time:.2f}s"
        response.headers["X-Extraction-Info"] = f"Source: {debug_info['image']['size']} bytes, Extracted: {extracted_size} bytes"
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error during extraction: {str(e)}")
        # Clean up files immediately on error
        if temp_image:
            cleanup_temp_file(temp_image.name)
        if extracted_path:
            cleanup_temp_file(extracted_path)
            
        # Return detailed error
        total_time = time.time() - process_start
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(e),
                "debug_info": {
                    "process_time": f"{total_time:.2f}s",
                    "image": image.filename,
                    "error_type": "validation_error"
                }
            }
        )
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Unexpected error during extraction: {str(e)}\n{trace}")
        # Clean up files immediately on error
        if temp_image:
            cleanup_temp_file(temp_image.name)
        if extracted_path:
            cleanup_temp_file(extracted_path)
            
        # Return error info
        total_time = time.time() - process_start
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error during extraction process",
                "debug_info": {
                    "process_time": f"{total_time:.2f}s",
                    "error": str(e),
                    "error_type": "server_error"
                }
            }
        ) 