from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os


@register_node
class ReadTextFileNode(Node):
    NAME = "Read Text File"
    DESCRIPTION = "Read content from a text file and return as string"
    
    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the text file to read",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "encoding": {
            "label": "File Encoding",
            "description": "Text file encoding (e.g., utf-8, ascii, etc)",
            "type": "STRING",
            "default": "utf-8",
            "required": False
        }
    }
    
    OUTPUTS = {
        "content": {
            "label": "File Content",
            "description": "Content read from the text file",
            "type": "STRING"
        }
    }
    
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            file_path = os.path.abspath(node_inputs["file_path"])
            encoding = node_inputs.get("encoding", "utf-8")
            
            workflow_logger.info(f"Reading file: {file_path}")
            workflow_logger.debug(f"Using encoding: {encoding}")

            if not os.path.exists(file_path):
                error_msg = f"File does not exist: {file_path}"
                workflow_logger.error(error_msg)
                return {"success": False, "error_message": error_msg}
            
            if not os.path.isfile(file_path):
                error_msg = f"Path is not a file: {file_path}"
                workflow_logger.error(error_msg)
                return {"success": False, "error_message": error_msg}

            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                workflow_logger.info(f"Successfully read {len(content)} characters")
                return {
                    "success": True,
                    "content": content
                }

        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }
