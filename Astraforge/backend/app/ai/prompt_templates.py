"""
Prompt templates for mission generation and AI interactions.

This module contains structured prompts for generating space mission
specifications and other AI-powered features.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class MissionPromptTemplate(BaseModel):
    """Template for mission generation prompts."""
    
    system_prompt: str
    user_prompt_template: str
    response_schema: Dict[str, Any]


# Mission generation system prompt
MISSION_GENERATION_SYSTEM_PROMPT = """
You are an expert space mission planner with deep knowledge of orbital mechanics, spacecraft design, and mission operations. Your role is to generate realistic and feasible space mission specifications based on user descriptions.

Key principles:
1. All missions must be physically feasible with current or near-future technology
2. Consider realistic constraints: fuel requirements, launch windows, communication delays
3. Provide specific, quantifiable parameters where possible
4. Include risk assessment and alternative approaches when appropriate
5. Base recommendations on actual spacecraft capabilities and historical missions

When generating missions, consider:
- Orbital mechanics and delta-v requirements
- Spacecraft mass, fuel capacity, and propulsion systems
- Mission timeline and critical phases
- Communication and navigation requirements
- Scientific objectives and instrumentation needs
- Risk factors and contingency planning
"""

# Mission specification response schema
MISSION_SPECIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "mission": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Mission name"},
                "description": {"type": "string", "description": "Detailed mission description"},
                "objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of mission objectives"
                },
                "mission_type": {
                    "type": "string",
                    "enum": ["exploration", "communication", "scientific", "commercial", "military"],
                    "description": "Primary mission category"
                },
                "difficulty_level": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced", "expert"],
                    "description": "Mission complexity level"
                }
            },
            "required": ["name", "description", "objectives", "mission_type", "difficulty_level"]
        },
        "spacecraft": {
            "type": "object",
            "properties": {
                "vehicle_type": {
                    "type": "string",
                    "description": "Type of spacecraft (e.g., 'Small Satellite', 'Deep Space Probe')"
                },
                "mass_kg": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 500000,
                    "description": "Total spacecraft mass in kilograms"
                },
                "fuel_capacity_kg": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Fuel capacity in kilograms"
                },
                "thrust_n": {
                    "type": "number",
                    "minimum": 0.001,
                    "description": "Maximum thrust in Newtons"
                },
                "specific_impulse_s": {
                    "type": "number",
                    "minimum": 200,
                    "maximum": 500,
                    "description": "Specific impulse in seconds"
                },
                "payload_mass_kg": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Payload mass in kilograms"
                }
            },
            "required": ["vehicle_type", "mass_kg", "fuel_capacity_kg", "thrust_n", "specific_impulse_s", "payload_mass_kg"]
        },
        "trajectory": {
            "type": "object",
            "properties": {
                "departure_body": {
                    "type": "string",
                    "enum": ["Earth", "Moon", "Mars", "Venus", "Jupiter", "Saturn"],
                    "description": "Departure celestial body"
                },
                "target_body": {
                    "type": "string",
                    "enum": ["Earth", "Moon", "Mars", "Venus", "Jupiter", "Saturn", "Asteroid Belt", "Deep Space"],
                    "description": "Target destination"
                },
                "transfer_type": {
                    "type": "string",
                    "enum": ["hohmann", "bi-elliptic", "direct", "gravity_assist"],
                    "description": "Type of trajectory transfer"
                },
                "launch_window_start": {
                    "type": "string",
                    "format": "date",
                    "description": "Launch window start date (YYYY-MM-DD)"
                },
                "launch_window_end": {
                    "type": "string",
                    "format": "date",
                    "description": "Launch window end date (YYYY-MM-DD)"
                },
                "estimated_duration_days": {
                    "type": "number",
                    "minimum": 1,
                    "description": "Estimated mission duration in days"
                },
                "total_delta_v_ms": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Total delta-v requirement in m/s"
                }
            },
            "required": ["departure_body", "target_body", "transfer_type", "launch_window_start", "launch_window_end", "estimated_duration_days", "total_delta_v_ms"]
        },
        "mission_phases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Phase name"},
                    "description": {"type": "string", "description": "Phase description"},
                    "duration_days": {"type": "number", "minimum": 0, "description": "Phase duration in days"},
                    "delta_v_ms": {"type": "number", "minimum": 0, "description": "Delta-v required for this phase in m/s"}
                },
                "required": ["name", "description", "duration_days", "delta_v_ms"]
            },
            "description": "List of mission phases"
        },
        "constraints": {
            "type": "object",
            "properties": {
                "max_mission_duration_days": {
                    "type": "number",
                    "minimum": 1,
                    "description": "Maximum acceptable mission duration"
                },
                "budget_constraint_usd": {
                    "type": "number",
                    "minimum": 1000000,
                    "description": "Budget constraint in USD"
                },
                "risk_tolerance": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Acceptable risk level"
                }
            },
            "required": ["max_mission_duration_days", "budget_constraint_usd", "risk_tolerance"]
        },
        "success_metrics": {
            "type": "object",
            "properties": {
                "primary_success_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Primary mission success criteria"
                },
                "secondary_success_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Secondary mission success criteria"
                },
                "estimated_success_probability": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Estimated probability of mission success (0-1)"
                }
            },
            "required": ["primary_success_criteria", "secondary_success_criteria", "estimated_success_probability"]
        }
    },
    "required": ["mission", "spacecraft", "trajectory", "mission_phases", "constraints", "success_metrics"]
}

# User prompt template for mission generation
MISSION_GENERATION_USER_PROMPT = """
Generate a detailed space mission specification based on the following user request:

"{user_prompt}"

Please provide a comprehensive mission plan that includes:

1. Mission Overview: Name, description, objectives, and classification
2. Spacecraft Configuration: Vehicle type, mass, propulsion, and payload specifications
3. Trajectory Planning: Departure/target bodies, transfer type, launch windows, and delta-v requirements
4. Mission Phases: Detailed breakdown of mission timeline with specific phases
5. Constraints: Duration limits, budget considerations, and risk tolerance
6. Success Metrics: Primary and secondary success criteria with probability estimates

Ensure all parameters are realistic and based on current aerospace capabilities. Consider:
- Physical constraints and orbital mechanics
- Realistic spacecraft performance characteristics
- Appropriate mission timeline and phases
- Feasible budget and risk assessments
- Clear success criteria and probability estimates

The response must be valid JSON matching the specified schema exactly.
"""


class MissionPromptBuilder:
    """Builder class for creating mission generation prompts."""
    
    @staticmethod
    def build_mission_generation_prompt(user_prompt: str) -> MissionPromptTemplate:
        """
        Build a complete mission generation prompt.
        
        Args:
            user_prompt: The user's mission description
            
        Returns:
            MissionPromptTemplate with system prompt, user prompt, and schema
        """
        formatted_user_prompt = MISSION_GENERATION_USER_PROMPT.format(
            user_prompt=user_prompt
        )
        
        return MissionPromptTemplate(
            system_prompt=MISSION_GENERATION_SYSTEM_PROMPT,
            user_prompt_template=formatted_user_prompt,
            response_schema=MISSION_SPECIFICATION_SCHEMA
        )
    
    @staticmethod
    def build_mission_refinement_prompt(
        current_mission: Dict[str, Any],
        refinement_request: str
    ) -> MissionPromptTemplate:
        """
        Build a prompt for refining an existing mission.
        
        Args:
            current_mission: Current mission specification
            refinement_request: User's refinement request
            
        Returns:
            MissionPromptTemplate for mission refinement
        """
        refinement_system_prompt = f"""
{MISSION_GENERATION_SYSTEM_PROMPT}

You are refining an existing mission specification. The current mission is:
{current_mission}

Focus on making targeted improvements while maintaining mission feasibility and coherence.
"""
        
        refinement_user_prompt = f"""
Please refine the existing mission specification based on this request:

"{refinement_request}"

Maintain the overall mission structure while incorporating the requested changes.
Ensure all modifications are technically feasible and maintain mission coherence.
Update related parameters as needed (e.g., if changing spacecraft mass, update fuel requirements).

The response must be valid JSON matching the specified schema exactly.
"""
        
        return MissionPromptTemplate(
            system_prompt=refinement_system_prompt,
            user_prompt_template=refinement_user_prompt,
            response_schema=MISSION_SPECIFICATION_SCHEMA
        )


# Alternative mission suggestion prompt
ALTERNATIVE_MISSION_SYSTEM_PROMPT = """
You are a space mission consultant providing alternative mission approaches when the original request is not feasible.

Your role is to:
1. Identify why the original mission may not be feasible
2. Suggest 2-3 alternative approaches that address the user's core objectives
3. Explain the trade-offs and benefits of each alternative
4. Provide realistic specifications for each alternative

Focus on creative solutions that maintain the spirit of the original request while being technically achievable.
"""

ALTERNATIVE_MISSION_SCHEMA = {
    "type": "object",
    "properties": {
        "feasibility_analysis": {
            "type": "object",
            "properties": {
                "is_feasible": {"type": "boolean"},
                "issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of feasibility issues"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recommendations for improvement"
                }
            },
            "required": ["is_feasible", "issues", "recommendations"]
        },
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "advantages": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "trade_offs": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "estimated_cost_usd": {"type": "number"},
                    "estimated_duration_days": {"type": "number"},
                    "success_probability": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["name", "description", "advantages", "trade_offs", "estimated_cost_usd", "estimated_duration_days", "success_probability"]
            },
            "description": "Alternative mission approaches"
        }
    },
    "required": ["feasibility_analysis", "alternatives"]
}


def build_alternative_mission_prompt(original_request: str, issues: Optional[str] = None) -> MissionPromptTemplate:
    """
    Build a prompt for generating alternative mission approaches.
    
    Args:
        original_request: The original mission request
        issues: Optional description of identified issues
        
    Returns:
        MissionPromptTemplate for alternative mission generation
    """
    user_prompt = f"""
Analyze the following mission request and provide alternative approaches:

Original Request: "{original_request}"
"""
    
    if issues:
        user_prompt += f"""
Identified Issues: {issues}
"""
    
    user_prompt += """
Please provide:
1. A feasibility analysis of the original request
2. 2-3 alternative mission approaches that address the core objectives
3. Clear explanation of advantages and trade-offs for each alternative

Focus on practical solutions that maintain the user's primary goals while being technically achievable.
"""
    
    return MissionPromptTemplate(
        system_prompt=ALTERNATIVE_MISSION_SYSTEM_PROMPT,
        user_prompt_template=user_prompt,
        response_schema=ALTERNATIVE_MISSION_SCHEMA
    )