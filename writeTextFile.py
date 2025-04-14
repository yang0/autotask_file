from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
from pathlib import Path


@register_node
class WriteTextFileNode(Node):
    NAME = "Write Text File"
    DESCRIPTION = "Write content to a file"
    INPUTS = {
        "contents": {
            "label": "File Contents",
            "description": "Content to write to the file",
            "type": "STRING",
            "required": True
        },
        "file_name": {
            "label": "File Name",
            "description": "Name/path of the file to write",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "overwrite": {
            "label": "Overwrite",
            "description": "Whether to overwrite existing file",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "Base directory path (optional)",
            "type": "STRING",
            "required": False,
            "widget": "DIR"
        }
    }
    OUTPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path of the saved file",
            "type": "STRING"
        }
    }
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        try:
            contents = node_inputs.get("contents", "")
            file_name = node_inputs.get("file_name", "")
            overwrite = node_inputs.get("overwrite", True)
            base_dir = node_inputs.get("base_dir", "")

            if not file_name:
                workflow_logger.error("No file name provided")
                return {
                    "success": "false",
                    "error_message": "No file name provided",
                    "file_path": ""
                }

            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)
                if not base_path.exists():
                    workflow_logger.info(f"Creating base directory: {base_path}")
                    base_path.mkdir(parents=True, exist_ok=True)

            file_path = base_path.joinpath(file_name)

            if not file_path.parent.exists():
                workflow_logger.info(f"Creating parent directories: {file_path.parent}")
                file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_path.exists() and not overwrite:
                workflow_logger.warning(f"File exists and overwrite is disabled: {file_path}")
                return {
                    "success": "false",
                    "error_message": f"File already exists: {file_path}",
                    "file_path": str(file_path)
                }

            workflow_logger.info(f"Writing content to file: {file_path}")
            file_path.write_text(contents)

            return {
                "success": "true",
                "file_path": str(file_path),
                "error_message": ""
            }

        except Exception as e:
            error_msg = f"Error writing to file: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "file_path": ""
            }
