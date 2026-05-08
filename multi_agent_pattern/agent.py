# from google.adk.agents import LlmAgent, BaseAgent
# from google.adk.agents.invocation_context import InvocationContext
# from google.adk.events import Event
# from typing import AsyncGenerator


# # Correctly implement a custom agent by extending BaseAgent
# class TaskExecutor(BaseAgent):
#     """A specialized agent with custom, non-LLM behavior."""
#     name: str = "TaskExecutor"
#     description: str = "Executes a predefined task."
#     async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
#         """Custom implementation logic for the task."""
#         # This is where your custom logic would go.
#         # For this example, we'll just yield a simple event.
#         yield Event(author=self.name, content="Task finished successfully.")
        
# # Define individual agents with proper initialization
# # LlmAgent requires a model to be specified.
# greeter = LlmAgent(
#     name="Greeter",
#     model="gemini-2.5-flash",
#     instruction="You are a friendly greeter."
# )

# task_doer = TaskExecutor() # Instantiate our concrete custom agent

# # Create a parent agent and assign its sub-agents
# # The parent agent's description and instructions should guide its delegation logic.
# coordinator = LlmAgent(
#     name="Coordinator",
#     model="gemini-2.5-flash",
#     description="A coordinator that can greet users and execute tasks.",
#     instruction="When asked to greet, delegate to the Greeter. When asked to perform a task, delegate to the TaskExecutor.",
#     sub_agents=[ greeter, task_doer ]
# )

# # The ADK framework automatically establishes the parent-child relationships.
# # These assertions will pass if checked after initialization.
# assert greeter.parent_agent == coordinator
# assert task_doer.parent_agent == coordinator
# print("Agent hierarchy created successfully.")



# Second Agent #

# import asyncio
# from typing import AsyncGenerator
# from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
# from google.adk.events import Event, EventActions
# from google.adk.agents.invocation_context import InvocationContext

# # Best Practice: Define custom agents as complete, self-describing classes.
# class ConditionChecker(BaseAgent):
#     """A custom agent that checks for a 'completed' status in the session state."""
#     name: str = "ConditionChecker"
#     description: str = "Checks if a process is complete and signals the loop to stop."
#     async def _run_async_impl(
#         self, 
#         context: InvocationContext
#         ) -> AsyncGenerator[Event, None]:
#         """Checks state and yields an event to either continue or stop the loop."""
#         status = context.session.state.get("status", "pending")
#         is_done = (status == "completed")
#         if is_done:
#             # Escalate to terminate the loop when the condition is met.
#             yield Event(author=self.name,    
#             actions=EventActions(escalate=True))
#         else:
#             # Yield a simple event to continue the loop.
#             yield Event(author=self.name, content="Condition not met, continuing loop.")


# # Correction: The LlmAgent must have a model and clear instructions.
# process_step = LlmAgent(
#     name="ProcessingStep",
#     model="gemini-2.5-flash",
#     instruction="You are a step in a longer process. Perform your task. If you are the final step, update session state by setting 'status' to 'completed'."
# )


# # The LoopAgent orchestrates the workflow.
# poller = LoopAgent(
#     name="StatusPoller",
#     max_iterations=10,
#     sub_agents=[ process_step, ConditionChecker() ] # Instantiating the well-defined custom agent.
# )
# # This poller will now execute 'process_step'
# # and then 'ConditionChecker'
# # repeatedly until the status is 'completed' or 10 iterations
# # have passed.


# Third Agent # -> Sequential Agent 
# from google.adk.agents import SequentialAgent, Agent

# # This agent's output will be saved to session.state["data"]
# step1 = Agent(name="Step1_Fetch", output_key="data")

# # This agent will use the data from the previous step.
# # We instruct it on how to find and use this data.
# step2 = Agent(
#     name="Step2_Process",
#     instruction="Analyze the information found in state['data'] and provide a summary."
# )   

# pipeline = SequentialAgent(
#     name="MyPipeline",
#     sub_agents=[step1, step2]
# )
# # When the pipeline is run with an initial input, Step1 will execute,
# # its response will be stored in session.state["data"], and then
# # Step2 will execute, using the information from the state as instructed.


# Fourth Agent # -> Parallel Agent

# from google.adk.agents import Agent, ParallelAgent

# # It's better to define the fetching logic as tools for the agents
# # For simplicity in this example, we'll embed the logic in the agent's instruction.
# # In a real-world scenario, you would use tools.
# # Define the individual agents that will run in parallel

# weather_fetcher = Agent(
#     name="weather_fetcher",
#     model="gemini-2.5-flash",
#     instruction="Fetch the weather for the given location and return only the weather report.",
#     output_key="weather_data" # The result will be stored in session.state["weather_data"]
# )

# news_fetcher = Agent(
#     name="news_fetcher",
#     model="gemini-2.5-flash",
#     instruction="Fetch the top news story for the given topic and return only that story.",
#     output_key="news_data" # The result will be stored in session.state["news_data"]
# )

# # Create the ParallelAgent to orchestrate the sub-agents
# data_gatherer = ParallelAgent(
#     name="data_gatherer",
#     sub_agents=[
#         weather_fetcher,
#         news_fetcher
#     ]
# )

# # This agent will receive the results from both sub-agents in session.state


# Fifth Agent # -> Team of Agents

from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.genai import types

# 1. A simple function tool for the core capability.
# This follows the best practice of separating actions from reasoning.
def generate_image(prompt: str) -> dict:
    """
    Generates an image based on a textual prompt.
    Args:
    prompt: A detailed description of the image to generate.
    Returns:
    A dictionary with the status and the generated image bytes.
    """
    print(f"TOOL: Generating image for prompt: '{prompt}'")
    # In a real implementation, this would call an image generation API.
    # For this example, we return mock image data.
    mock_image_bytes = b"mock_image_data_for_a_cat_wearing_a_hat"
    return {
    "status": "success",
    # The tool returns the raw bytes, the agent will handle the Part creation.
    "image_bytes": mock_image_bytes,
    "mime_type": "image/png"
    }

# 2. Refactor the ImageGeneratorAgent into an LlmAgent.
# It now correctly uses the input passed to it.
image_generator_agent = LlmAgent(
    name="ImageGen",
    model="gemini-2.5-flash",
    description="Generates an image based on a detailed text prompt.",
    instruction=(
    "You are an image generation specialist. Your task is to take the user's request "
    "and use the `generate_image` tool to create the image. "
    "The user's entire request should be used as the 'prompt' argument for the tool. "
    "After the tool returns the image bytes, you MUST output the image."
    ),
    tools=[generate_image]
    )

# 3. Wrap the corrected agent in an AgentTool.
# The description here is what the parent agent sees.
image_tool = agent_tool.AgentTool(
    agent=image_generator_agent
)

# 4. The parent agent remains unchanged. Its logic was correct.
artist_agent = LlmAgent(
    name="Artist",
    model="gemini-2.5-flash",
    instruction=(
    "You are a creative artist. First, invent a creative and descriptive prompt for an image. "
    "Then, use the `ImageGen` tool to generate the image using   your prompt."
    ),
    tools=[image_tool]
)

root_agent = artist_agent