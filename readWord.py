from typing import Dict, Any
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node
import os
from pathlib import Path
from docx import Document as DocxDocument

@register_node
class ReadWordFileNode(Node):
    NAME = "Read Word File"
    DESCRIPTION = "Read content and metadata from a Word (.docx or .doc) file."

    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the Word (.docx or .doc) file to read",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "extract_metadata": {
            "label": "Extract Metadata",
            "description": "Whether to extract Word document metadata",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        },
        "include_headers": {
            "label": "Include Headers",
            "description": "Whether to include headers in extracted text",
            "type": "BOOLEAN",
            "default": True,
            "required": False
        }
    }

    OUTPUTS = {
        "content": {
            "label": "Word Content",
            "description": "Extracted text content from the Word file",
            "type": "STRING"
        },
        "meta_data": {
            "label": "Metadata",
            "description": "Word file metadata",
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
            extract_metadata = node_inputs.get("extract_metadata", True)
            include_headers = node_inputs.get("include_headers", True)
            ext = Path(file_path).suffix.lower()

            log_info(f"Reading Word file: {file_path}")
            log_debug(f"Extract metadata: {extract_metadata}, Include headers: {include_headers}")

            if not os.path.exists(file_path):
                error_msg = f"File does not exist: {file_path}"
                log_error(error_msg)
                return {"success": False, "error_message": error_msg}

            if not os.path.isfile(file_path):
                error_msg = f"Path is not a file: {file_path}"
                log_error(error_msg)
                return {"success": False, "error_message": error_msg}

            if ext == ".docx":
                try:
                    doc = DocxDocument(file_path)
                except Exception as e:
                    error_msg = f"Failed to open document {file_path}: {str(e)}"
                    log_error(error_msg)
                    return {"success": False, "error_message": error_msg}

                content = ""
                for para in doc.paragraphs:
                    if para.text.strip():
                        content += para.text + "\n\n"

                if include_headers:
                    for section in doc.sections:
                        header = section.header
                        if header.text.strip():
                            content = header.text + "\n\n" + content

                metadata = {
                    "source": str(file_path),
                    "filename": os.path.basename(file_path),
                    "extension": ext,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                }

                if extract_metadata:
                    core_props = doc.core_properties
                    if core_props:
                        metadata.update({
                            "title": core_props.title or "",
                            "author": core_props.author or "",
                            "subject": core_props.subject or "",
                            "created": str(core_props.created) if core_props.created else "",
                            "modified": str(core_props.modified) if core_props.modified else "",
                            "last_modified_by": core_props.last_modified_by or "",
                            "revision": core_props.revision or 0
                        })

            elif ext == ".doc":
                try:
                    import win32com.client
                    import pythoncom
                except ImportError:
                    error_msg = "win32com and pythoncom are required to read .doc files. Please install pywin32."
                    log_error(error_msg)
                    return {"success": False, "error_message": error_msg}
                try:
                    pythoncom.CoInitialize()
                    word = win32com.client.Dispatch("Word.Application")
                    word.Visible = False
                    doc = word.Documents.Open(str(Path(file_path).absolute()))
                    try:
                        content = ""
                        for para in doc.Paragraphs:
                            if para.Range.Text.strip():
                                content += para.Range.Text.strip() + "\n\n"
                        if include_headers:
                            for section in range(1, doc.Sections.Count + 1):
                                header_text = doc.Sections(section).Headers(1).Range.Text
                                if header_text.strip():
                                    content = header_text.strip() + "\n\n" + content
                        metadata = {
                            "source": str(file_path),
                            "filename": os.path.basename(file_path),
                            "extension": ext,
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        }
                        if extract_metadata:
                            try:
                                metadata.update({
                                    "title": doc.BuiltInDocumentProperties("Title").Value if doc.BuiltInDocumentProperties("Title") else "",
                                    "author": doc.BuiltInDocumentProperties("Author").Value if doc.BuiltInDocumentProperties("Author") else "",
                                    "subject": doc.BuiltInDocumentProperties("Subject").Value if doc.BuiltInDocumentProperties("Subject") else "",
                                    "created": str(doc.BuiltInDocumentProperties("Creation Date").Value) if doc.BuiltInDocumentProperties("Creation Date") else "",
                                    "modified": str(doc.BuiltInDocumentProperties("Last Save Time").Value) if doc.BuiltInDocumentProperties("Last Save Time") else "",
                                    "last_modified_by": doc.BuiltInDocumentProperties("Last Author").Value if doc.BuiltInDocumentProperties("Last Author") else "",
                                    "revision": doc.BuiltInDocumentProperties("Revision Number").Value if doc.BuiltInDocumentProperties("Revision Number") else 0
                                })
                            except Exception:
                                pass
                    finally:
                        if doc:
                            try:
                                doc.Close()
                            except Exception:
                                pass
                        if word:
                            try:
                                word.Quit()
                            except Exception:
                                pass
                        try:
                            pythoncom.CoUninitialize()
                        except Exception:
                            pass
                except Exception as e:
                    error_msg = f"Failed to read .doc file: {str(e)}"
                    log_error(error_msg)
                    return {"success": False, "error_message": error_msg}
            else:
                error_msg = f"Unsupported file extension: {ext}. Only .docx and .doc are supported."
                log_error(error_msg)
                return {"success": False, "error_message": error_msg}

            log_info(f"Successfully read Word content, length: {len(content)} characters.")
            return {
                "success": True,
                "content": content,
                "meta_data": metadata
            }

        except Exception as e:
            error_msg = f"Failed to read Word file: {str(e)}"
            log_error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }
