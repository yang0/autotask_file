from typing import Dict, Any
import os
import shutil
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node


@register_node
class CopyFileNode(Node):
    NAME = "Copy File"
    DESCRIPTION = "Copy a file or directory to target directory with optional cut operation"
    
    INPUTS = {
        "source_path": {
            "label": "Source Path",
            "description": "Path to the source file or directory",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "target_dir": {
            "label": "Target Directory",
            "description": "Directory where the file/directory will be copied to",
            "type": "STRING", 
            "required": True,
            "widget": "DIR"
        },
        "is_cut": {
            "label": "Cut Operation",
            "description": "If True, source will be removed after copying (cut/move operation)",
            "type": "BOOLEAN",
            "default": False,
            "required": False
        }
    }
    
    OUTPUTS = {
        "target_path": {
            "label": "Target Path",
            "description": "Path where the file/directory was copied to",
            "type": "STRING"
        }
    }
    
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            source_path = os.path.abspath(node_inputs["source_path"])
            target_dir = os.path.abspath(node_inputs["target_dir"])
            is_cut = node_inputs.get("is_cut", False)
            
            workflow_logger.info(f"{'Moving' if is_cut else 'Copying'} from {source_path} to {target_dir}")

            # Check if source exists
            if not os.path.exists(source_path):
                error_msg = f"Source path does not exist: {source_path}"
                workflow_logger.error(error_msg)
                return {"success": False, "error_message": error_msg}

            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)

            # Get the source file/directory name
            source_name = os.path.basename(source_path)
            target_path = os.path.join(target_dir, source_name)

            # Copy operation
            try:
                if os.path.isdir(source_path):
                    if is_cut:
                        shutil.move(source_path, target_path)
                    else:
                        shutil.copytree(source_path, target_path)
                else:
                    if is_cut:
                        shutil.move(source_path, target_path)
                    else:
                        shutil.copy2(source_path, target_path)
                
                workflow_logger.info(f"Successfully {'moved' if is_cut else 'copied'} to {target_path}")
                return {
                    "success": True,
                    "target_path": target_path
                }

            except Exception as e:
                error_msg = f"Failed to {'move' if is_cut else 'copy'}: {str(e)}"
                workflow_logger.error(error_msg)
                return {"success": False, "error_message": error_msg}

        except Exception as e:
            error_msg = f"Operation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {"success": False, "error_message": error_msg}
