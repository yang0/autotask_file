from typing import Dict, Any, List, Generator, AsyncGenerator
try:
    from autotask.nodes import Node, register_node, GeneratorNode
except ImportError:
    from ..stub import Node, register_node, GeneratorNode
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
            
            

@register_node
class ListDirectoryNode(Node):
    NAME = "List Directory"
    DESCRIPTION = """Get all files and directories in a specified path.

Return format:
{
    "success": true,
    "contents": [
        {
            "path": "file/dir path",
            "type": "file|dir"
        }
    ]
}"""

    INPUTS = {
        "directory_path": {
            "label": "Directory Path",
            "description": "Path of the directory to scan",
            "type": "STRING",
            "required": True
        },
        "include_dirs": {
            "label": "Include Directories",
            "description": "Whether to include directories in the results",
            "type": "BOOLEAN",
            "default": True,
            "required": True
        },
        "include_files": {
            "label": "Include Files",
            "description": "Whether to include files in the results",
            "type": "BOOLEAN",
            "default": True,
            "required": True
        },
        "recursive": {
            "label": "Include Subdirectories",
            "description": "Whether to scan subdirectories recursively",
            "type": "BOOLEAN",
            "default": False,
            "required": True
        }
    }
    OUTPUTS = {
        "contents": {
            "label": "Directory Contents",
            "description": "List of dictionaries containing path and type information",
            "type": "LIST"
        }
    }
    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        log = workflow_logger
        try:
            directory = os.path.abspath(node_inputs["directory_path"])
            include_dirs = node_inputs.get("include_dirs", True)
            include_files = node_inputs.get("include_files", True)
            recursive = node_inputs.get("recursive", False)

            if not os.path.exists(directory):
                error_msg = f"Directory does not exist: {directory}"
                log.error(error_msg)
                return {"success": False, "error_message": error_msg}

            if not os.path.isdir(directory):
                error_msg = f"Path is not a directory: {directory}"
                log.error(error_msg)
                return {"success": False, "error_message": error_msg}

            log.info(f"Scanning directory: {directory}")
            log.debug(f"Include directories: {include_dirs}")
            log.debug(f"Include files: {include_files}")
            log.debug(f"Recursive scan: {recursive}")

            contents = []
            
            def scan_directory(path: str):
                with os.scandir(path) as entries:
                    for entry in entries:
                        is_dir = entry.is_dir()
                        if is_dir and include_dirs:
                            contents.append({
                                "path": entry.path,
                                "type": "dir"
                            })
                        elif not is_dir and include_files:
                            contents.append({
                                "path": entry.path,
                                "type": "file"
                            })
                        
                        if recursive and is_dir:
                            scan_directory(entry.path)

            scan_directory(directory)
            
            return {
                "success": True,
                "contents": contents
            }

        except Exception as e:
            error_msg = f"Directory scanning failed: {str(e)}"
            log.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }
            
            

@register_node
class DirectoryListGeneratorNode(GeneratorNode):
    """Generator node to list directory contents one by one"""
    NAME = "Directory List Generator"
    DESCRIPTION = """List all contents in a directory one by one.
    
Return format for each yield:
{
        "path": "absolute path of the item",
        "is_file": true/false
}"""

    INPUTS = {
        "directory_path": {
            "label": "Directory Path",
            "description": "Path of the directory to scan",
            "type": "STRING",
            "required": True
        },
        "include_dirs": {
            "label": "Include Directories",
            "description": "Whether to include directories in the results",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        },
        "include_files": {
            "label": "Include Files",
            "description": "Whether to include files in the results",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        },
        "recursive": {
            "label": "Include Subdirectories",
            "description": "Whether to scan subdirectories recursively",
            "type": "BOOLEAN",
            "default": False,
            "required": False
        }
    }

    OUTPUTS = {
        "path": {
            "label": "Item Path",
            "description": "Absolute path of the current item",
            "type": "STRING"
        },
        "is_file": {
            "label": "Is File",
            "description": "Whether the current item is a file (true) or directory (false)",
            "type": "BOOLEAN"
        }
    }

    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> AsyncGenerator[Any, None]:
        log = workflow_logger
        try:
            directory = os.path.abspath(node_inputs["directory_path"])
            include_dirs = node_inputs.get("include_dirs", True)
            include_files = node_inputs.get("include_files", True)
            recursive = node_inputs.get("recursive", False)

            if not os.path.exists(directory):
                log.error(f"Directory does not exist: {directory}")
                return

            if not os.path.isdir(directory):
                log.error(f"Path is not a directory: {directory}")
                return

            log.info(f"Start scanning directory: {directory}")
            log.debug(f"Include directories: {include_dirs}")
            log.debug(f"Include files: {include_files}")
            log.debug(f"Recursive scan: {recursive}")

            async def scan_directory(path: str):
                with os.scandir(path) as entries:
                    for entry in entries:
                        is_file = entry.is_file()
                        is_dir = entry.is_dir()

                        if is_file and include_files:
                            log.debug(f"Found file: {entry.path}")
                            yield {
                                "path": entry.path,
                                "is_file": True
                            }
                        elif is_dir:
                            if include_dirs:
                                log.debug(f"Found directory: {entry.path}")
                                yield {
                                    "path": entry.path,
                                    "is_file": False
                                }
                            if recursive:
                                async for item in scan_directory(entry.path):
                                    yield item

            async for item in scan_directory(directory):
                yield item

            log.info("Directory scanning completed successfully")

        except Exception as e:
            error_msg = f"Directory scanning failed: {str(e)}"
            log.error(error_msg)
            return
            
            
