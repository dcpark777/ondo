"""
Schema generation service using avrotize for converting dataset schemas
to various formats (protobuf, Scala, Python).
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.api.schemas import ColumnResponse


def columns_to_avro_schema(
    dataset_name: str,
    namespace: str,
    columns: List[ColumnResponse],
    description: Optional[str] = None,
) -> Dict:
    """
    Convert dataset columns to Avro schema format.
    
    Args:
        dataset_name: Name of the dataset (used as record name)
        namespace: Namespace for the Avro schema
        columns: List of column information
        description: Optional dataset description
        
    Returns:
        Avro schema as a dictionary
    """
    # Map common SQL types to Avro types
    def map_type_to_avro(sql_type: Optional[str], nullable: Optional[bool]) -> Dict:
        """Map SQL type to Avro type, handling nullable fields."""
        if sql_type is None:
            avro_type = "string"  # Default to string if type is unknown
        else:
            sql_type_lower = sql_type.lower()
            # Map SQL types to Avro types
            if "int" in sql_type_lower or "integer" in sql_type_lower:
                avro_type = "long"
            elif "bigint" in sql_type_lower:
                avro_type = "long"
            elif "smallint" in sql_type_lower or "tinyint" in sql_type_lower:
                avro_type = "int"
            elif "float" in sql_type_lower:
                avro_type = "float"
            elif "double" in sql_type_lower or "decimal" in sql_type_lower or "numeric" in sql_type_lower:
                avro_type = "double"
            elif "boolean" in sql_type_lower or "bool" in sql_type_lower:
                avro_type = "boolean"
            elif "timestamp" in sql_type_lower or "datetime" in sql_type_lower:
                avro_type = {"type": "long", "logicalType": "timestamp-millis"}
            elif "date" in sql_type_lower:
                avro_type = {"type": "int", "logicalType": "date"}
            elif "bytes" in sql_type_lower or "binary" in sql_type_lower:
                avro_type = "bytes"
            else:
                avro_type = "string"  # Default to string
        
        # Handle nullable fields by wrapping in union with null
        if nullable is True:
            if isinstance(avro_type, dict):
                return ["null", avro_type]
            else:
                return ["null", avro_type]
        else:
            return avro_type
    
    # Build Avro schema fields
    fields = []
    for col in columns:
        field = {
            "name": col.name,
            "type": map_type_to_avro(col.type, col.nullable),
        }
        if col.description:
            field["doc"] = col.description
        fields.append(field)
    
    # Build complete Avro schema
    schema = {
        "type": "record",
        "name": _sanitize_name(dataset_name),
        "namespace": namespace,
        "fields": fields,
    }
    
    if description:
        schema["doc"] = description
    
    return schema


def _sanitize_name(name: str) -> str:
    """Sanitize name for use in schema (remove special characters, capitalize)."""
    # Remove special characters and replace spaces/underscores with nothing
    sanitized = "".join(c if c.isalnum() else "" for c in name)
    # Capitalize first letter
    if sanitized:
        return sanitized[0].upper() + sanitized[1:] if len(sanitized) > 1 else sanitized.upper()
    return "Record"


def generate_protobuf_schema(avro_schema: Dict) -> Tuple[str, str]:
    """
    Generate Protocol Buffers schema from Avro schema using avrotize.
    
    Args:
        avro_schema: Avro schema dictionary
        
    Returns:
        Tuple of (schema_code, test_code) - test_code will be empty for protobuf
    """
    schema = _convert_with_avrotize(avro_schema, "a2p")
    return schema, ""  # Protobuf doesn't generate test code


def generate_scala_schema(avro_schema: Dict) -> Tuple[str, str]:
    """
    Generate Java classes from Avro schema using avrotize.
    Note: Avrotize doesn't have direct Scala support, so we generate Java classes
    which Scala can interoperate with.
    
    Args:
        avro_schema: Avro schema dictionary
        
    Returns:
        Tuple of (schema_code, test_code) - separated by file patterns
    """
    return _convert_with_avrotize_separated(avro_schema, "a2java")


def generate_python_schema(avro_schema: Dict) -> Tuple[str, str]:
    """
    Generate Python classes from Avro schema using avrotize.
    
    Args:
        avro_schema: Avro schema dictionary
        
    Returns:
        Tuple of (schema_code, test_code) - separated by file patterns
    """
    return _convert_with_avrotize_separated(avro_schema, "a2py")


def _separate_schema_from_tests(files: List[Path], format_type: str) -> Tuple[str, str]:
    """
    Separate schema files from test files based on naming patterns.
    
    Args:
        files: List of generated file paths
        format_type: Format type ('java', 'python', 'protobuf')
        
    Returns:
        Tuple of (schema_code, test_code)
    """
    schema_files = []
    test_files = []
    
    for file in files:
        filename = file.name.lower()
        # Common test file patterns
        is_test = (
            'test' in filename or
            'spec' in filename or
            filename.endswith('_test.py') or
            filename.endswith('test.py') or
            filename.endswith('_test.java') or
            filename.endswith('test.java') or
            'Test' in file.name or
            filename.startswith('test_')
        )
        
        if is_test:
            test_files.append(file)
        else:
            schema_files.append(file)
    
    # Read and concatenate schema files
    schema_code = "\n\n".join([f.read_text() for f in schema_files]) if schema_files else ""
    
    # Read and concatenate test files
    test_code = "\n\n".join([f.read_text() for f in test_files]) if test_files else ""
    
    return schema_code, test_code


def _convert_with_avrotize(avro_schema: Dict, command: str) -> str:
    """
    Convert Avro schema using avrotize command-line tool.
    
    Args:
        avro_schema: Avro schema dictionary
        command: avrotize command (a2p, a2scala, a2python)
        
    Returns:
        Converted schema as string
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write Avro schema to temporary file
        avro_file = Path(tmpdir) / "schema.avsc"
        with open(avro_file, "w") as f:
            json.dump(avro_schema, f, indent=2)
        
        try:
            # Run avrotize command
            if command == "a2p":
                # Protocol Buffers - needs output directory
                output_dir = Path(tmpdir) / "proto"
                output_dir.mkdir()
                result = subprocess.run(
                    ["avrotize", "a2p", str(avro_file), "--out", str(output_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Find the generated .proto file
                proto_files = list(output_dir.glob("*.proto"))
                if proto_files:
                    return proto_files[0].read_text()
                return result.stdout
            elif command == "a2java":
                # Generate Java classes (Scala can use Java classes)
                output_dir = Path(tmpdir) / "java"
                output_dir.mkdir()
                result = subprocess.run(
                    ["avrotize", "a2java", str(avro_file), "--out", str(output_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Find generated Java files
                java_files = list(output_dir.rglob("*.java"))
                if java_files:
                    # Read and return all Java files concatenated
                    java_content = "\n\n".join([f.read_text() for f in java_files])
                    return java_content
                raise RuntimeError(f"No Java files generated. stderr: {result.stderr}")
            elif command == "a2py":
                # Generate Python classes using a2py
                output_dir = Path(tmpdir) / "python"
                output_dir.mkdir()
                result = subprocess.run(
                    ["avrotize", "a2py", str(avro_file), "--out", str(output_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Find generated Python files
                python_files = list(output_dir.rglob("*.py"))
                if python_files:
                    # Read and return all Python files concatenated
                    python_content = "\n\n".join([f.read_text() for f in python_files])
                    return python_content
                raise RuntimeError(f"No Python files generated. stderr: {result.stderr}")
            else:
                raise ValueError(f"Unknown avrotize command: {command}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Avrotize conversion failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "avrotize command not found. Please ensure avrotize is installed and in PATH."
            )


def _convert_with_avrotize_separated(avro_schema: Dict, command: str) -> Tuple[str, str]:
    """
    Convert Avro schema using avrotize and separate schema from test code.
    
    Args:
        avro_schema: Avro schema dictionary
        command: avrotize command (a2java, a2py)
        
    Returns:
        Tuple of (schema_code, test_code)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write Avro schema to temporary file
        avro_file = Path(tmpdir) / "schema.avsc"
        with open(avro_file, "w") as f:
            json.dump(avro_schema, f, indent=2)
        
        try:
            if command == "a2java":
                # Generate Java classes (Scala can use Java classes)
                output_dir = Path(tmpdir) / "java"
                output_dir.mkdir()
                result = subprocess.run(
                    ["avrotize", "a2java", str(avro_file), "--out", str(output_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Find generated Java files
                java_files = list(output_dir.rglob("*.java"))
                if java_files:
                    schema_code, test_code = _separate_schema_from_tests(java_files, "java")
                    return schema_code, test_code
                raise RuntimeError(f"No Java files generated. stderr: {result.stderr}")
            elif command == "a2py":
                # Generate Python classes using a2py
                output_dir = Path(tmpdir) / "python"
                output_dir.mkdir()
                result = subprocess.run(
                    ["avrotize", "a2py", str(avro_file), "--out", str(output_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Find generated Python files
                python_files = list(output_dir.rglob("*.py"))
                if python_files:
                    schema_code, test_code = _separate_schema_from_tests(python_files, "python")
                    return schema_code, test_code
                raise RuntimeError(f"No Python files generated. stderr: {result.stderr}")
            else:
                raise ValueError(f"Unknown avrotize command for separated output: {command}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Avrotize conversion failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "avrotize command not found. Please ensure avrotize is installed and in PATH."
            )

