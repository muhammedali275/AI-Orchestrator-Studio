"""
Files API - File system operations for the orchestrator.

Provides endpoints for browsing, reading, and editing files.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

# Base directory for file operations (orchestrator directory)
BASE_DIR = Path(__file__).parent.parent.parent


class FileItem(BaseModel):
    """Model for file/directory item."""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    modified: Optional[str] = None


class FileContent(BaseModel):
    """Model for file content."""
    path: str
    content: str
    encoding: str = "utf-8"


class FileUpdateRequest(BaseModel):
    """Model for file update request."""
    content: str = Field(..., description="New file content")


@router.get("/list")
async def list_files(
    path: str = Query("", description="Directory path relative to orchestrator root")
) -> Dict[str, Any]:
    """
    List files and directories in the specified path.
    
    Args:
        path: Directory path relative to orchestrator root
        
    Returns:
        List of files and directories
    """
    try:
        # Construct full path
        if path:
            full_path = BASE_DIR / path
        else:
            full_path = BASE_DIR
        
        # Security check - ensure path is within BASE_DIR
        try:
            full_path = full_path.resolve()
            BASE_DIR.resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid path")
        
        # Check if path exists
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if not full_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        # List items
        items: List[FileItem] = []
        
        try:
            for item in sorted(full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    # Get relative path
                    rel_path = item.relative_to(BASE_DIR)
                    
                    # Get item info
                    item_type = "directory" if item.is_dir() else "file"
                    size = item.stat().st_size if item.is_file() else None
                    modified = item.stat().st_mtime
                    
                    items.append(FileItem(
                        name=item.name,
                        path=str(rel_path).replace("\\", "/"),
                        type=item_type,
                        size=size,
                        modified=str(modified)
                    ))
                except Exception as e:
                    logger.warning(f"Error processing item {item}: {str(e)}")
                    continue
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return {
            "path": path,
            "items": [item.dict() for item in items],
            "total": len(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content")
async def get_file_content(
    path: str = Query(..., description="File path relative to orchestrator root")
) -> FileContent:
    """
    Get the content of a file.
    
    Args:
        path: File path relative to orchestrator root
        
    Returns:
        File content
    """
    try:
        # Construct full path
        full_path = BASE_DIR / path
        
        # Security check
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid path")
        
        # Check if file exists
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return FileContent(
                path=path,
                content=content,
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            # Try binary mode for non-text files
            raise HTTPException(status_code=400, detail="File is not a text file")
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/content")
async def update_file_content(
    path: str = Query(..., description="File path relative to orchestrator root"),
    request: FileUpdateRequest = None
) -> Dict[str, Any]:
    """
    Update the content of a file.
    
    Args:
        path: File path relative to orchestrator root
        request: File update request with new content
        
    Returns:
        Success message
    """
    try:
        # Construct full path
        full_path = BASE_DIR / path
        
        # Security check
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid path")
        
        # Check if file exists
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Write file content
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
            
            return {
                "success": True,
                "message": f"File {path} updated successfully",
                "path": path
            }
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree")
async def get_directory_tree(
    path: str = Query("", description="Directory path relative to orchestrator root"),
    max_depth: int = Query(3, description="Maximum depth to traverse")
) -> Dict[str, Any]:
    """
    Get directory tree structure.
    
    Args:
        path: Directory path relative to orchestrator root
        max_depth: Maximum depth to traverse
        
    Returns:
        Directory tree structure
    """
    try:
        # Construct full path
        if path:
            full_path = BASE_DIR / path
        else:
            full_path = BASE_DIR
        
        # Security check
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid path")
        
        # Check if path exists
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if not full_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        def build_tree(dir_path: Path, current_depth: int = 0) -> Dict[str, Any]:
            """Recursively build directory tree."""
            if current_depth >= max_depth:
                return None
            
            tree = {
                "name": dir_path.name or "root",
                "path": str(dir_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "type": "directory",
                "children": []
            }
            
            try:
                for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    try:
                        if item.is_dir():
                            subtree = build_tree(item, current_depth + 1)
                            if subtree:
                                tree["children"].append(subtree)
                        else:
                            tree["children"].append({
                                "name": item.name,
                                "path": str(item.relative_to(BASE_DIR)).replace("\\", "/"),
                                "type": "file",
                                "size": item.stat().st_size
                            })
                    except Exception:
                        continue
            except PermissionError:
                pass
            
            return tree
        
        tree = build_tree(full_path)
        
        return {
            "tree": tree,
            "base_path": path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building directory tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
