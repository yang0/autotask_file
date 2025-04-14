try:
    from autotask.nodes import Node, register_node
except ImportError:
    from .stub import Node, register_node

from typing import Dict, Any
import os


@register_node
class FileConcatenationNode(Node):
    NAME = "File Concatenation Node"
    DESCRIPTION = "Concatenate multiple text files into a single output file"

    INPUTS = {
        "input_files": {
            "label": "Input Files",
            "description": "List of text file paths to concatenate",
            "type": "LIST",
            "required": True,
        },
        "output_file": {
            "label": "Output File",
            "description": "Path where the concatenated file will be saved",
            "type": "STRING",
            "required": True,
        }
    }

    OUTPUTS = {
        "output_file": {
            "label": "Output File",
            "description": "Path to the concatenated file",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            input_files = node_inputs["input_files"]
            output_file = node_inputs["output_file"]

            workflow_logger.info(f"Starting file concatenation process...input_files: {input_files}, output_file: {output_file}")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Perform file concatenation
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for file_path in input_files:
                    workflow_logger.debug(f"Processing file: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(content)
                            outfile.write('\n')  # Add newline between files
                    except Exception as e:
                        workflow_logger.error(f"Error reading file {file_path}: {str(e)}")
                        raise

            workflow_logger.info(f"File concatenation completed: {output_file}")
            return {
                "success": True,
                "output_file": output_file
            }

        except Exception as e:
            error_msg = f"File concatenation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }


if __name__ == "__main__":
    # Test code
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create test files
    test_files = ["test1.txt", "test2.txt"]
    for i, file in enumerate(test_files):
        with open(file, 'w', encoding='utf-8') as f:
            f.write(f"This is test file {i+1}")
    
    # Test the node
    node = FileConcatenationNode()
    result = node.execute({
        "input_files": test_files,
        "output_path": "concatenated.txt"
    }, logger)
    print(f"Test result: {result}")
    
    # Clean up test files
    for file in test_files + ["concatenated.txt"]:
        if os.path.exists(file):
            os.remove(file)
