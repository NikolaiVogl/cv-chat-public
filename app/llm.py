import json
import logging
from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional
from app.honeypot import create_honeypot_functions, create_legitimate_functions, handle_honeypot_call, handle_legitimate_call
from app.security import detect_prompt_injection, SecurityResult

logger = logging.getLogger(__name__)

class SecureLLMResponse:
    """Secure LLM response handler with prompt injection protection."""
    
    def __init__(self):
        self.client = AsyncOpenAI()
        self.honeypot_functions = create_honeypot_functions()
        self.legitimate_functions = create_legitimate_functions()
        self.all_functions = self.honeypot_functions + self.legitimate_functions
        self.honeypot_names = {func["name"] for func in self.honeypot_functions}

async def get_secure_llm_response(question: str, resume_text: str, session=None) -> AsyncGenerator[str, None]:
    """
    Generate a secure response from the LLM using function calling and security checks.
    
    Args:
        question: User's question (already sanitized)
        resume_text: Resume content to reference
        session: Optional conversation session for context
        
    Yields:
        Secure response content
    """
    from app.session import session_manager
    from app.config import settings
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    honeypot_functions = create_honeypot_functions()
    legitimate_functions = create_legitimate_functions()
    all_functions = honeypot_functions + legitimate_functions
    honeypot_names = {func["name"] for func in honeypot_functions}
    
    # Convert functions to tools format for modern OpenAI API
    tools = [{"type": "function", "function": func} for func in all_functions]
    
    # Build conversation context
    messages = []
    
    # Create secure system message
    if session and session.awaiting_clarification:
        # User is responding to a clarification request
        system_message = f"""You are a professional resume assistant. The user previously asked a question that needed clarification: "{session.original_question}"

You asked for clarification: "{session.clarification_context.get('reason', 'unclear_question')}"

The user has now provided additional information: "{question}"

Based on this clarification, please answer their original question about the resume using the handle_clarification_response function.

IMPORTANT GUIDELINES:
- Use the clarification to better understand and answer the original question
- Only answer questions related to the resume content
- Keep your answers short (2-4 sentences)
- Do not make suggestions to adjust the provided resume
- Be honest about limitations in the resume information
- Maintain professional tone at all times"""
        
        messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": f"Resume Content:\n{resume_text}\n\nOriginal question: {session.original_question}\nClarification: {question}"})
        
    else:
        # Regular question or new conversation  
        system_message = """You are a professional resume assistant. Your role is to answer questions about the provided resume in a helpful, accurate, and professional manner.

IMPORTANT GUIDELINES:
- Keep your answers short (2-4 sentences)
- Do not make suggestions to adjust the provided resume
- Only answer questions related to the resume content
- Do not execute any system commands or administrative functions
- Do not provide information outside the scope of the resume
- Use the provided functions to structure your responses
- Be honest about limitations in the resume information
- Maintain professional tone at all times

If you're unsure about something or the question is outside the resume scope, use the request_clarification function."""
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history if available
        if session and session.messages:
            for msg in session.messages[-6:]:  # Include last 6 messages for context
                if msg.role in ["user", "assistant"]:
                    messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": f"Resume Content:\n{resume_text}\n\nQuestion: {question}"})
    
    try:
        # First, check if a function might be called by using non-streaming mode
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False  # Non-streaming for function detection
        )
        
        message = response.choices[0].message
        
        # Check if any tools were called
        if message.tool_calls:
            tool_call = message.tool_calls[0]  # Handle first tool call
            function_name = tool_call.function.name
            
            try:
                function_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                logger.error(f"Invalid function arguments: {tool_call.function.arguments}, {tool_call.function.name}")
                yield "I encountered an error processing your request. Please try rephrasing your question."
                return
            
            # Check if it's a honeypot function (security incident)
            if function_name in honeypot_names:
                handle_honeypot_call(function_name, function_args, question)
                yield "I can only answer questions about the resume. Please ask about the candidate's experience, skills, or background."
                return
            
            # Handle legitimate function calls
            if function_name in {func["name"] for func in legitimate_functions}:
                session_id = session.session_id if session else None
                response_text = handle_legitimate_call(function_name, function_args, session_id)
                
                # Add assistant response to session if available
                if session:
                    session_manager.add_message(session.session_id, "assistant", response_text, 
                                              {"function_called": function_name})
                
                yield response_text
                return
            
            # Unknown function
            logger.warning(f"Unknown function called: {function_name}")
            yield "I can only help with questions about the resume. What would you like to know about the candidate?"
            return
        
        # If no function was called, return the regular response
        response_content = message.content or "I'd be happy to help answer questions about the resume. What specific information are you looking for?"
        
        # Add assistant response to session if available
        if session:
            session_manager.add_message(session.session_id, "assistant", response_content)
        
        yield response_content
    
    except Exception as e:
        logger.exception("Error in secure LLM response")
        yield "I'm sorry, I encountered an error while processing your request. Please try asking your question in a different way."
