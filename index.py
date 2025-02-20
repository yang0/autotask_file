from typing import Dict, Any, Generator
from autotask.nodes import GeneratorNode, register_node
import os
import glob
import fnmatch
import platform

@register_node
class FileIteratorNode(GeneratorNode):
    NAME ="文件遍历器"
    DESCRIPTION = "遍历指定目录下的文件，支持通配符匹配"
    INPUTS = {
        "app_dir": {
            "label": "目录路径",
            "description": "要遍历的目录路径",
            "type": "STRING",
            "required": True
        },
        "recursive": {
            "label": "包含子目录",
            "description": "是否遍历子目录",
            "type": "BOOLEAN",
            "default": False,
            "required": True
        },
        "patterns": {
            "label": "文件通配符",
            "description": "文件匹配模式，多个用逗号或分号分隔(如: *.txt,*.jpg;*.png)",
            "type": "STRING",
            "required": True
        }
    }
    OUTPUTS = {
        "file_path": {
            "label": "文件路径",
            "description": "匹配到的文件的绝对路径",
            "type": "STRING"
        }
    }
    CATEGORY = "文件处理"

    def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Generator:
        log = workflow_logger
        try:
            directory = os.path.abspath(node_inputs["app_dir"])
            recursive = node_inputs.get("recursive", False)
            patterns = node_inputs["patterns"]

            # 分割通配符模式
            patterns = [p.strip() for p in patterns.replace(";", ",").split(",") if p.strip()]
            
            # 根据操作系统决定是否区分大小写
            is_case_sensitive = platform.system() != 'Windows'
            if not is_case_sensitive:
                patterns = [p.lower() for p in patterns]
            
            if not os.path.exists(directory):
                log.error(f"Directory does not exist: {directory}")
                return
                
            if not os.path.isdir(directory):
                log.error(f"Path is not a directory: {directory}")
                return

            log.info(f"Start scanning directory: {directory}")
            log.debug(f"Wildcard patterns: {patterns}")
            log.debug(f"Include subdirectories: {recursive}")
            log.debug(f"Case sensitive: {is_case_sensitive}")

            def match_file(filename: str, patterns: list) -> bool:
                """根据操作系统判断文件是否匹配模式"""
                if not is_case_sensitive:
                    filename = filename.lower()
                return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)

            # 遍历目录
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if match_file(file, patterns):
                            log.debug(f"Found matching file: {file_path}")
                            yield file_path
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
                                yield file_path

        except Exception as e:
            log.error(f"File scanning failed: {str(e)}")
            return