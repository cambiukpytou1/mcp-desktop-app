"""
Dataset Integration System
=========================

System for integrating CSV and JSON datasets with prompt templates
for bulk testing and parameter sweeps.
"""

import csv
import json
from typing import Dict, List, Any, Optional, Iterator, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import io

from .templating_engine import TemplateVariable, AdvancedTemplatingEngine


@dataclass
class DatasetColumn:
    """Dataset column definition."""
    name: str
    type: str  # 'string', 'number', 'boolean', 'list', 'dict'
    description: str = ""
    nullable: bool = True
    unique: bool = False
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class DatasetInfo:
    """Dataset information and metadata."""
    name: str
    source_path: str
    format: str  # 'csv', 'json', 'jsonl'
    row_count: int
    column_count: int
    columns: List[DatasetColumn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: Optional[datetime] = None
    file_size: int = 0


@dataclass
class ParameterSweepConfig:
    """Configuration for parameter sweep testing."""
    template_id: str
    dataset_path: str
    variable_mappings: Dict[str, str]  # template_var -> dataset_column
    batch_size: int = 10
    max_rows: Optional[int] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    randomize: bool = False
    seed: Optional[int] = None


@dataclass
class BulkTestResult:
    """Result of bulk testing operation."""
    config: ParameterSweepConfig
    total_rows: int
    successful_renders: int
    failed_renders: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)


class DatasetIntegration:
    """
    Dataset integration system for prompt template testing.
    
    Provides CSV and JSON data binding capabilities with bulk testing
    and parameter sweep functionality.
    """
    
    def __init__(self):
        """Initialize the dataset integration system."""
        self.templating_engine = AdvancedTemplatingEngine()
        self.supported_formats = ['csv', 'json', 'jsonl']
    
    def analyze_dataset(self, file_path: str) -> DatasetInfo:
        """
        Analyze a dataset file and return metadata information.
        
        Args:
            file_path: Path to the dataset file
            
        Returns:
            DatasetInfo with dataset metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        file_format = self._detect_format(file_path)
        file_size = path.stat().st_size
        
        dataset_info = DatasetInfo(
            name=path.stem,
            source_path=file_path,
            format=file_format,
            row_count=0,
            column_count=0,
            file_size=file_size,
            last_modified=datetime.fromtimestamp(path.stat().st_mtime)
        )
        
        # Analyze content based on format
        if file_format == 'csv':
            self._analyze_csv(dataset_info)
        elif file_format in ['json', 'jsonl']:
            self._analyze_json(dataset_info)
        
        return dataset_info
    
    def _detect_format(self, file_path: str) -> str:
        """Detect file format based on extension and content."""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return 'csv'
        elif extension == '.json':
            return 'json'
        elif extension == '.jsonl':
            return 'jsonl'
        else:
            # Try to detect from content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('{'):
                        return 'json'
                    elif ',' in first_line:
                        return 'csv'
            except:
                pass
        
        return 'unknown'
    
    def _analyze_csv(self, dataset_info: DatasetInfo) -> None:
        """Analyze CSV file structure."""
        try:
            with open(dataset_info.source_path, 'r', encoding='utf-8') as f:
                # Use csv.Sniffer to detect dialect
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                
                reader = csv.reader(f, dialect)
                headers = next(reader, [])
                
                if headers:
                    dataset_info.column_count = len(headers)
                    
                    # Create column definitions
                    for header in headers:
                        dataset_info.columns.append(DatasetColumn(
                            name=header,
                            type='string',  # Default, could be improved with type detection
                            description=f"Column: {header}"
                        ))
                
                # Count rows
                row_count = 0
                sample_values = {col.name: [] for col in dataset_info.columns}
                
                for row in reader:
                    row_count += 1
                    for i, value in enumerate(row):
                        if i < len(dataset_info.columns):
                            col_name = dataset_info.columns[i].name
                            if len(sample_values[col_name]) < 5:  # Keep 5 sample values
                                sample_values[col_name].append(value)
                
                dataset_info.row_count = row_count
                
                # Add sample values to columns
                for col in dataset_info.columns:
                    col.sample_values = sample_values.get(col.name, [])
                    
        except Exception as e:
            raise ValueError(f"Error analyzing CSV file: {e}")
    
    def _analyze_json(self, dataset_info: DatasetInfo) -> None:
        """Analyze JSON file structure."""
        try:
            with open(dataset_info.source_path, 'r', encoding='utf-8') as f:
                if dataset_info.format == 'jsonl':
                    # JSON Lines format
                    lines = f.readlines()
                    dataset_info.row_count = len(lines)
                    
                    if lines:
                        # Analyze first line to get structure
                        first_obj = json.loads(lines[0])
                        self._extract_json_columns(first_obj, dataset_info)
                else:
                    # Regular JSON format
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        dataset_info.row_count = len(data)
                        if data:
                            self._extract_json_columns(data[0], dataset_info)
                    else:
                        dataset_info.row_count = 1
                        self._extract_json_columns(data, dataset_info)
                        
        except Exception as e:
            raise ValueError(f"Error analyzing JSON file: {e}")
    
    def _extract_json_columns(self, obj: Dict[str, Any], dataset_info: DatasetInfo, prefix: str = "") -> None:
        """Extract column information from JSON object."""
        for key, value in obj.items():
            col_name = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Nested object - recurse
                self._extract_json_columns(value, dataset_info, col_name)
            else:
                # Determine type
                col_type = 'string'
                if isinstance(value, bool):
                    col_type = 'boolean'
                elif isinstance(value, int):
                    col_type = 'number'
                elif isinstance(value, float):
                    col_type = 'number'
                elif isinstance(value, list):
                    col_type = 'list'
                
                dataset_info.columns.append(DatasetColumn(
                    name=col_name,
                    type=col_type,
                    description=f"JSON field: {col_name}",
                    sample_values=[str(value)]
                ))
        
        dataset_info.column_count = len(dataset_info.columns)
    
    def load_dataset(self, file_path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load dataset from file.
        
        Args:
            file_path: Path to dataset file
            max_rows: Maximum number of rows to load
            
        Returns:
            List of dictionaries representing dataset rows
        """
        file_format = self._detect_format(file_path)
        
        if file_format == 'csv':
            return self._load_csv(file_path, max_rows)
        elif file_format == 'json':
            return self._load_json(file_path, max_rows)
        elif file_format == 'jsonl':
            return self._load_jsonl(file_path, max_rows)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    def _load_csv(self, file_path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load CSV file."""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                data.append(dict(row))
        
        return data
    
    def _load_json(self, file_path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            if max_rows:
                return data[:max_rows]
            return data
        else:
            return [data]
    
    def _load_jsonl(self, file_path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load JSON Lines file."""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if max_rows and i >= max_rows:
                    break
                
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        
        return data
    
    def flatten_json_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flatten nested JSON data for template use.
        
        Args:
            data: List of nested dictionaries
            
        Returns:
            List of flattened dictionaries
        """
        flattened_data = []
        
        for item in data:
            flattened_item = self._flatten_dict(item)
            flattened_data.append(flattened_item)
        
        return flattened_data
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Recursively flatten a nested dictionary."""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def run_bulk_test(
        self, 
        template: str, 
        config: ParameterSweepConfig,
        templating_engine: Optional[AdvancedTemplatingEngine] = None
    ) -> BulkTestResult:
        """
        Run bulk testing with parameter sweep.
        
        Args:
            template: Template to test
            config: Parameter sweep configuration
            templating_engine: Optional templating engine instance
            
        Returns:
            BulkTestResult with test results
        """
        if templating_engine is None:
            templating_engine = self.templating_engine
        
        start_time = datetime.now()
        
        result = BulkTestResult(
            config=config,
            total_rows=0,
            successful_renders=0,
            failed_renders=0
        )
        
        try:
            # Load dataset
            data = self.load_dataset(config.dataset_path, config.max_rows)
            
            # Apply filters if specified
            if config.filter_conditions:
                data = self._apply_filters(data, config.filter_conditions)
            
            # Randomize if requested
            if config.randomize:
                import random
                if config.seed:
                    random.seed(config.seed)
                random.shuffle(data)
            
            result.total_rows = len(data)
            
            # Process in batches
            for i in range(0, len(data), config.batch_size):
                batch = data[i:i + config.batch_size]
                
                for row_data in batch:
                    # Map dataset columns to template variables
                    template_variables = {}
                    for template_var, dataset_col in config.variable_mappings.items():
                        if dataset_col in row_data:
                            template_variables[template_var] = row_data[dataset_col]
                    
                    # Render template
                    render_result = templating_engine.render_template(template, template_variables)
                    
                    test_result = {
                        'row_index': len(result.results),
                        'template_variables': template_variables,
                        'dataset_row': row_data,
                        'success': render_result.success,
                        'rendered_content': render_result.rendered_content if render_result.success else '',
                        'error': render_result.error if not render_result.success else None,
                        'render_time': render_result.render_time
                    }
                    
                    result.results.append(test_result)
                    
                    if render_result.success:
                        result.successful_renders += 1
                    else:
                        result.failed_renders += 1
                        result.errors.append(f"Row {len(result.results)}: {render_result.error}")
        
        except Exception as e:
            result.errors.append(f"Bulk test error: {e}")
        
        # Calculate execution time
        end_time = datetime.now()
        result.execution_time = (end_time - start_time).total_seconds()
        
        return result
    
    def _apply_filters(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filter conditions to dataset."""
        filtered_data = []
        
        for row in data:
            include_row = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in row:
                    if row[filter_key] != filter_value:
                        include_row = False
                        break
                else:
                    include_row = False
                    break
            
            if include_row:
                filtered_data.append(row)
        
        return filtered_data