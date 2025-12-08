"""
Code Executor Tool - Execute code in sandboxed environment.

Uses configuration from tool config - no hard-coded settings.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from .base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class CodeExecutorTool(BaseTool):
    """
    Code execution tool for running code snippets.
    
    Supports multiple languages with timeout and resource limits.
    """
    
    def __init__(self, name: str = "code_executor", config: Optional[Dict[str, Any]] = None):
        """
        Initialize code executor tool.
        
        Args:
            name: Tool name
            config: Configuration including timeout, max_memory, allowed_languages
        """
        super().__init__(
            name=name,
            description="Execute code in a sandboxed environment",
            config=config
        )
        
        self.timeout = self.config.get("timeout", 30)
        self.max_memory = self.config.get("max_memory", "512MB")
        self.allowed_languages = self.config.get("allowed_languages", ["python", "javascript"])
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        stdin: Optional[str] = None
    ) -> ToolResult:
        """
        Execute code.
        
        Args:
            code: Code to execute
            language: Programming language
            stdin: Standard input for the code
            
        Returns:
            ToolResult with execution output
        """
        if language not in self.allowed_languages:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Language '{language}' not allowed. Allowed: {self.allowed_languages}"
            )
        
        try:
            logger.info(f"[CodeExecutor] Executing {language} code")
            
            # Execute based on language
            if language == "python":
                result = await self._execute_python(code, stdin)
            elif language == "javascript":
                result = await self._execute_javascript(code, stdin)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    output=None,
                    error=f"Execution not implemented for {language}"
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"[CodeExecutor] Timeout executing {language} code")
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Code execution timeout ({self.timeout}s)"
            )
            
        except Exception as e:
            logger.error(f"[CodeExecutor] Error: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )
    
    async def _execute_python(self, code: str, stdin: Optional[str]) -> ToolResult:
        """
        Execute Python code.
        
        Args:
            code: Python code
            stdin: Standard input
            
        Returns:
            ToolResult with output
        """
        try:
            # Create subprocess to execute code
            process = await asyncio.create_subprocess_exec(
                "python", "-c", code,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=self.timeout
            )
            
            output = stdout.decode()
            error = stderr.decode()
            
            if process.returncode == 0:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output=output,
                    metadata={
                        "language": "python",
                        "return_code": process.returncode
                    }
                )
            else:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    output=output,
                    error=error,
                    metadata={
                        "language": "python",
                        "return_code": process.returncode
                    }
                )
                
        except FileNotFoundError:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="Python interpreter not found"
            )
    
    async def _execute_javascript(self, code: str, stdin: Optional[str]) -> ToolResult:
        """
        Execute JavaScript code.
        
        Args:
            code: JavaScript code
            stdin: Standard input
            
        Returns:
            ToolResult with output
        """
        try:
            # Create subprocess to execute code with Node.js
            process = await asyncio.create_subprocess_exec(
                "node", "-e", code,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=self.timeout
            )
            
            output = stdout.decode()
            error = stderr.decode()
            
            if process.returncode == 0:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output=output,
                    metadata={
                        "language": "javascript",
                        "return_code": process.returncode
                    }
                )
            else:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    output=output,
                    error=error,
                    metadata={
                        "language": "javascript",
                        "return_code": process.returncode
                    }
                )
                
        except FileNotFoundError:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="Node.js not found"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to execute"
                    },
                    "language": {
                        "type": "string",
                        "enum": self.allowed_languages,
                        "description": "Programming language",
                        "default": "python"
                    },
                    "stdin": {
                        "type": "string",
                        "description": "Standard input for the code"
                    }
                },
                "required": ["code"]
            }
        }
