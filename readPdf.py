from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
from pathlib import Path
import pypdf

@register_node
class ReadPdfFileNode(Node):
    NAME = "Read PDF File"
    DESCRIPTION = "Read content and metadata from a PDF file, with optional page range."

    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the PDF file to read",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "start_page": {
            "label": "Start Page",
            "description": "Page number to start reading from (1-based, optional)",
            "type": "INT",
            "default": 1,
            "required": False
        },
        "end_page": {
            "label": "End Page",
            "description": "Page number to end reading at (1-based, 0 means last page, optional)",
            "type": "INT",
            "default": 0,
            "required": False
        },
        "extract_metadata": {
            "label": "Extract Metadata",
            "description": "Whether to extract PDF metadata",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        }
    }

    OUTPUTS = {
        "content": {
            "label": "PDF Content",
            "description": "Extracted text content from the PDF file (by page range)",
            "type": "STRING"
        },
        "meta_data": {
            "label": "Metadata",
            "description": "PDF file metadata",
            "type": "DICT"
        }
    }

    CATEGORY = "File Processing"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        def log_info(msg):
            if workflow_logger:
                workflow_logger.info(msg)
        def log_debug(msg):
            if workflow_logger:
                workflow_logger.debug(msg)
        def log_error(msg):
            if workflow_logger:
                workflow_logger.error(msg)
        try:
            file_path = os.path.abspath(node_inputs["file_path"])
            start_page = node_inputs.get("start_page", 1)
            end_page = node_inputs.get("end_page", 0)
            extract_metadata = node_inputs.get("extract_metadata", True)

            log_info(f"Reading PDF file: {file_path}")
            log_debug(f"Start page: {start_page}, End page: {end_page}, Extract metadata: {extract_metadata}")

            if not os.path.exists(file_path):
                error_msg = f"File does not exist: {file_path}"
                log_error(error_msg)
                return {"success": False, "error_message": error_msg}

            if not os.path.isfile(file_path):
                error_msg = f"Path is not a file: {file_path}"
                log_error(error_msg)
                return {"success": False, "error_message": error_msg}

            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                num_pages = len(pdf.pages)
                start_idx = max(0, (start_page - 1)) if start_page else 0
                # If end_page is 0 or not set, read to the last page
                end_idx = num_pages if not end_page or end_page == 0 else min(end_page, num_pages)
                if start_idx >= num_pages or start_idx < 0:
                    error_msg = f"Start page {start_page} is out of range. PDF has {num_pages} pages."
                    log_error(error_msg)
                    return {"success": False, "error_message": error_msg}
                if end_idx > num_pages or end_idx < start_idx:
                    error_msg = f"End page {end_page} is out of range. PDF has {num_pages} pages."
                    log_error(error_msg)
                    return {"success": False, "error_message": error_msg}
                content = ""
                for i in range(start_idx, end_idx):
                    page = pdf.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n\n"

                metadata = {
                    "source": str(file_path),
                    "filename": os.path.basename(file_path),
                    "extension": Path(file_path).suffix,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path),
                    "page_count": num_pages
                }
                if extract_metadata and pdf.metadata:
                    metadata.update({
                        "title": pdf.metadata.get("/Title", ""),
                        "author": pdf.metadata.get("/Author", ""),
                        "subject": pdf.metadata.get("/Subject", ""),
                        "creator": pdf.metadata.get("/Creator", ""),
                        "producer": pdf.metadata.get("/Producer", ""),
                        "creation_date": pdf.metadata.get("/CreationDate", ""),
                        "modification_date": pdf.metadata.get("/ModDate", "")
                    })

            log_info(f"Successfully read PDF content, length: {len(content)} characters.")
            return {
                "success": True,
                "content": content,
                "meta_data": metadata
            }

        except Exception as e:
            error_msg = f"Failed to read PDF file: {str(e)}"
            log_error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }
