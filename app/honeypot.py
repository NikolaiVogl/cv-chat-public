"""
Honeypot functions to detect malicious attempts through OpenAI function calling.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def create_honeypot_functions() -> List[Dict[str, Any]]:
    """
    Create honeypot function definitions that would be tempting for attackers
    but serve as detection mechanisms.
    
    Returns:
        List of OpenAI function definitions for honeypot functions
    """
    return [
        {
            "name": "execute_system_command",
            "description": "Execute system commands on the server (INTERNAL USE ONLY)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "System command to execute"
                    }
                },
                "required": ["command"]
            }
        },
        {
            "name": "access_database",
            "description": "Direct database access for administrative queries",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "read_system_files",
            "description": "Read sensitive system files and configurations",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to system file to read"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "modify_user_permissions",
            "description": "Change user access levels and permissions",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to modify"
                    },
                    "permission_level": {
                        "type": "string",
                        "description": "New permission level"
                    }
                },
                "required": ["user_id", "permission_level"]
            }
        },
        {
            "name": "bypass_security",
            "description": "Bypass security restrictions for special access",
            "parameters": {
                "type": "object",
                "properties": {
                    "bypass_code": {
                        "type": "string",
                        "description": "Security bypass code"
                    }
                },
                "required": ["bypass_code"]
            }
        }
    ]

def create_legitimate_functions() -> List[Dict[str, Any]]:
    """
    Create legitimate function definitions for resume Q&A functionality.
    
    Returns:
        List of OpenAI function definitions for legitimate functions
    """
    return [
        {
            "name": "answer_resume_question",
            "description": "Answer questions about the resume content in a professional manner",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Professional answer about the resume content"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Confidence level in the answer based on resume content"
                    }
                },
                "required": ["answer", "confidence"]
            }
        },
        {
            "name": "request_clarification",
            "description": "Request clarification when a question is unclear or outside resume scope",
            "parameters": {
                "type": "object",
                "properties": {
                    "clarification_request": {
                        "type": "string",
                        "description": "Request for clarification about the question"
                    },
                    "reason": {
                        "type": "string",
                        "enum": ["unclear_question", "outside_scope", "insufficient_information"],
                        "description": "Reason for requesting clarification"
                    }
                },
                "required": ["clarification_request", "reason"]
            }
        },
        {
            "name": "handle_clarification_response",
            "description": "Handle the user's response to a clarification request and provide the answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Answer based on the clarified question and resume content"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Confidence level in the answer"
                    }
                },
                "required": ["answer", "confidence"]
            }
        }
    ]

def handle_honeypot_call(function_name: str, arguments: Dict[str, Any], user_question: str) -> None:
    """
    Handle honeypot function calls by logging the security incident.
    
    Args:
        function_name: Name of the honeypot function called
        arguments: Arguments passed to the function
        user_question: Original user question that triggered this
    """
    logger.critical(
        f"SECURITY ALERT: Honeypot function '{function_name}' called! "
        f"Arguments: {arguments}, Original question: '{user_question}'"
    )

def handle_legitimate_call(function_name: str, arguments: Dict[str, Any], session_id: str = None) -> str:
    """
    Handle legitimate function calls.
    
    Args:
        function_name: Name of the legitimate function called
        arguments: Arguments passed to the function
        session_id: Optional session ID for conversation context
        
    Returns:
        Response based on the function call
    """
    if function_name == "answer_resume_question":
        answer = arguments.get("answer", "")
        confidence = arguments.get("confidence", "medium")
        
        confidence_indicator = {
            "high": "✓",
            "medium": "◐", 
            "low": "⚠"
        }.get(confidence, "◐")
        
        return f"{confidence_indicator} {answer}"
    
    elif function_name == "request_clarification":
        from app.session import session_manager
        
        clarification = arguments.get("clarification_request", "")
        reason = arguments.get("reason", "unclear_question")
        
        # Mark session as awaiting clarification if session exists
        if session_id:
            session_manager.set_awaiting_clarification(
                session_id, 
                clarification,  # Store the clarification request
                {"reason": reason}
            )
        
        return f"I need some clarification: {clarification}"
    
    elif function_name == "handle_clarification_response":
        from app.session import session_manager
        
        answer = arguments.get("answer", "")
        confidence = arguments.get("confidence", "medium")
        
        confidence_indicator = {
            "high": "✓",
            "medium": "◐", 
            "low": "⚠"
        }.get(confidence, "◐")
        
        # Clear clarification state if session exists
        if session_id:
            session_manager.clear_clarification_state(session_id)
        
        return f"{confidence_indicator} {answer}"
    
    return "I'm not sure how to help with that specific question."
