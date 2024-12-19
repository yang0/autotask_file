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
                # Windows下转换为小写进行匹配
                patterns = [p.lower() for p in patterns]
            
            if not os.path.exists(directory):
                log.error(f"目录不存在: {directory}")
                return
                
            if not os.path.isdir(directory):
                log.error(f"路径不是目录: {directory}")
                return

            log.info(f"开始遍历目录: {directory}")
            log.debug(f"通配符模式: {patterns}")
            log.debug(f"是否包含子目录: {recursive}")
            log.debug(f"是否区分大小写: {is_case_sensitive}")

            def match_file(filename: str, patterns: list) -> bool:
                """根据操作系统判断文件是否匹配模式"""
                if not is_case_sensitive:
                    fileNAME =filename.lower()
                return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)

            # 遍历目录
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 检查是否匹配任一模式
                        if match_file(file, patterns):
                            log.debug(f"找到匹配文件: {file_path}")
                            yield file_path  # 直接yield文件路径字符串
            else:
                # 不递归遍历，只查找当前目录
                for pattern in patterns:
                    pattern_path = os.path.join(directory, pattern)
                    total_files = len(glob.glob(pattern_path, recursive=False))
                    log.info(f"总共找到 {total_files} 个文件")
                    for file_path in glob.glob(pattern_path, recursive=False):
                        if os.path.isfile(file_path):
                            fileNAME =os.path.basename(file_path)
                            if match_file(filename, patterns):
                                log.debug(f"找到匹配文件: {file_path}")
                                yield file_path  # 直接yield文件路径字符串

        except Exception as e:
            log.error(f"文件遍历失败: {str(e)}")
            return