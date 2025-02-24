from typing import Dict, Any, List
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
import glob
import fnmatch
import platform


@register_node
class FileListNode(Node):
    NAME = "File List"
    DESCRIPTION = "Get a list of files in a directory, supports wildcard matching"
    INPUTS = {
        "app_dir": {
            "label": "Directory Path",
            "description": "Path of the directory to scan",
            "type": "STRING",
            "required": True
        },
        "recursive": {
            "label": "Include Subdirectories",
            "description": "Whether to scan subdirectories",
            "type": "BOOLEAN",
            "default": False,
            "required": True
        },
        "patterns": {
            "label": "File Patterns",
            "description": "File matching patterns, separated by comma or semicolon (e.g., *.txt,*.jpg;*.png)",
            "type": "STRING",
            "required": True
        }
    }
    OUTPUTS = {
        "file_list": {
            "label": "File List",
            "description": "List of matched file paths",
            "type": "LIST"
        }
    }
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        log = workflow_logger
        try:
            directory = os.path.abspath(node_inputs["app_dir"])
            recursive = node_inputs.get("recursive", False)
            patterns = node_inputs["patterns"]

            # Split patterns
            patterns = [p.strip() for p in patterns.replace(";", ",").split(",") if p.strip()]
            
            # Case sensitivity based on OS
            is_case_sensitive = platform.system() != 'Windows'
            if not is_case_sensitive:
                patterns = [p.lower() for p in patterns]
            
            if not os.path.exists(directory):
                log.error(f"Directory does not exist: {directory}")
                return {"success": False, "error_message": f"Directory does not exist: {directory}"}
                
            if not os.path.isdir(directory):
                log.error(f"Path is not a directory: {directory}")
                return {"success": False, "error_message": f"Path is not a directory: {directory}"}

            log.info(f"Start scanning directory: {directory}")
            log.debug(f"Wildcard patterns: {patterns}")
            log.debug(f"Include subdirectories: {recursive}")
            log.debug(f"Case sensitive: {is_case_sensitive}")

            def match_file(filename: str, patterns: list) -> bool:
                """Check if file matches any pattern"""
                if not is_case_sensitive:
                    filename = filename.lower()
                return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)

            # Collect matching files
            file_list = []
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if match_file(file, patterns):
                            log.debug(f"Found matching file: {file_path}")
                            file_list.append(file_path)
            else:
                for pattern in patterns:
                    pattern_path = os.path.join(directory, pattern)
                    total_files = len(glob.glob(pattern_path, recursive=False))
                    log.info(f"Found {total_files} files in total")
                    for file_path in glob.glob(pattern_path, recursive=False):
                        if os.path.isfile(file_path):
                            filename = os.path.basename(file_path)
                            if match_file(filename, patterns):
                                log.debug(f"Found matching file: {file_path}")
                                file_list.append(file_path)

            return {
                "success": True,
                "file_list": file_list
            }

        except Exception as e:
            error_msg = f"File scanning failed: {str(e)}"
            log.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }