from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
from pathlib import Path
import shutil


@register_node
class FileDeleteNode(Node):
    NAME = "File Delete"
    DESCRIPTION = "Delete a file or directory"
    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the file or directory to delete",
            "type": "STRING",
            "required": True
        },
        "recursive": {
            "label": "Recursive Delete",
            "description": "Whether to recursively delete directories",
            "type": "BOOLEAN",
            "default": False,
            "required": False
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "Base directory path (optional)",
            "type": "STRING",
            "required": False
        }
    }
    OUTPUTS = {
        "deleted_path": {
            "label": "Deleted Path",
            "description": "Path that was deleted",
            "type": "STRING"
        }
    }
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        try:
            file_path_input = node_inputs.get("file_path", "")
            recursive = node_inputs.get("recursive", False)
            base_dir = node_inputs.get("base_dir", "")

            if not file_path_input:
                workflow_logger.error("No file path provided")
                return {
                    "success": "false",
                    "error_message": "No file path provided",
                    "deleted_path": ""
                }

            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)

            file_path = base_path.joinpath(file_path_input)

            if not file_path.exists():
                workflow_logger.warning(f"File/directory does not exist: {file_path}")
                return {
                    "success": "false",
                    "error_message": f"File/directory does not exist: {file_path}",
                    "deleted_path": str(file_path)
                }

            workflow_logger.info(f"Deleting: {file_path}")

            if file_path.is_dir():
                if recursive:
                    workflow_logger.info("Performing recursive directory deletion")
                    shutil.rmtree(file_path)
                else:
                    try:
                        file_path.rmdir()
                    except OSError:
                        error_msg = "Directory not empty. Use recursive=true to delete non-empty directories"
                        workflow_logger.error(error_msg)
                        return {
                            "success": "false",
                            "error_message": error_msg,
                            "deleted_path": str(file_path)
                        }
            else:
                file_path.unlink()

            workflow_logger.info("Deletion successful")
            return {
                "success": "true",
                "deleted_path": str(file_path),
                "error_message": ""
            }

        except Exception as e:
            error_msg = f"Error deleting file/directory: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "deleted_path": ""
            }
