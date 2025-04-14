from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
import json
from pathlib import Path


@register_node
class FileInfoNode(Node):
    NAME = "File Info"
    DESCRIPTION = "Get information about a file or directory"
    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the file or directory",
            "type": "STRING",
            "required": True
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "Base directory path (optional)",
            "type": "STRING",
            "required": False
        }
    }
    OUTPUTS = {
        "info": {
            "label": "File Information",
            "description": "JSON string containing file information",
            "type": "STRING"
        },
        "exists": {
            "label": "File Exists",
            "description": "Whether the file exists",
            "type": "STRING"
        }
    }
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        try:
            file_path_input = node_inputs.get("file_path", "")
            base_dir = node_inputs.get("base_dir", "")

            if not file_path_input:
                workflow_logger.error("No file path provided")
                return {
                    "success": "false",
                    "error_message": "No file path provided",
                    "info": "{}",
                    "exists": "false"
                }

            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)

            file_path = base_path.joinpath(file_path_input)

            if not file_path.exists():
                workflow_logger.info(f"File/directory does not exist: {file_path}")
                return {
                    "success": "true",
                    "info": json.dumps({"path": str(file_path), "exists": False}),
                    "exists": "false",
                    "error_message": ""
                }

            workflow_logger.info(f"Getting information for: {file_path}")
            is_dir = file_path.is_dir()

            info = {
                "path": str(file_path),
                "name": file_path.name,
                "exists": True,
                "is_directory": is_dir,
                "is_file": file_path.is_file(),
                "parent": str(file_path.parent),
                "extension": file_path.suffix if file_path.is_file() else "",
                "stem": file_path.stem
            }

            stats = file_path.stat()
            info.update({
                "size": stats.st_size,
                "created_time": stats.st_ctime,
                "modified_time": stats.st_mtime,
                "accessed_time": stats.st_atime
            })

            if is_dir:
                try:
                    contents = list(file_path.iterdir())
                    info.update({
                        "file_count": sum(1 for item in contents if item.is_file()),
                        "directory_count": sum(1 for item in contents if item.is_dir()),
                        "total_items": len(contents)
                    })
                except PermissionError:
                    info["permission_error"] = "Cannot list directory contents"

            return {
                "success": "true",
                "info": json.dumps(info, indent=2),
                "exists": "true",
                "error_message": ""
            }

        except Exception as e:
            error_msg = f"Error getting file information: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "info": "{}",
                "exists": "false"
            }
