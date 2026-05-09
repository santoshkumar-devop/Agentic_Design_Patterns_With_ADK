# import asyncio
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Import necessary classes from the Google Agent Developer Kit (ADK)
# from google.adk.agents import LlmAgent
# from google.adk.sessions import InMemorySessionService
# from google.adk.runners import Runner
# from google.genai.types import Content, Part

# # Define an LlmAgent with an output_key.
# greeting_agent = LlmAgent(
#     name="Greeter",
#     model="gemini-2.5-flash",
#     instruction="Generate a short, friendly greeting.",
#     output_key="last_greeting"
# )

# # --- Setup Runner and Session ---
# app_name, user_id, session_id = "state_app", "user1", "session1"
# session_service = InMemorySessionService()

# runner = Runner(
#     agent=greeting_agent,
#     app_name=app_name,
#     session_service=session_service
# )

# async def main():
#     session = await session_service.create_session(
#         app_name=app_name,
#         user_id=user_id,
#         session_id=session_id
#     )

#     print(f"Initial state: {session.state}")

#     # --- Run the Agent ---
#     user_message = Content(parts=[Part(text="Hello")])
#     print("\n--- Running the agent ---")
#     for event in runner.run(
#         user_id=user_id,
#         session_id=session_id,
#         new_message=user_message
#     ):
#         if event.is_final_response():
#             print("Agent responded.")

#     print("\n--- Checking Updated State ---")
#     # Correctly check the state *after* the runner has finished processing all events.
#     updated_session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
#     print(f"\nState after agent run: {updated_session.state}")

# if __name__ == "__main__":
#     asyncio.run(main())

import time
from google.adk.tools.tool_context import ToolContext
from google.adk.sessions import InMemorySessionService

# --- Define the Recommended Tool-Based Approach ---
def log_user_login(tool_context: ToolContext) -> dict:
    """ Updates the session state upon a user login event.
    This tool encapsulates all state changes related to a user
    login.
    Args:
    tool_context: Automatically provided by ADK, gives access
    to session state.
    Returns:
    A dictionary confirming the action was successful.
    """
    # Access the state directly through the provided context.
    state = tool_context.state
    # Get current values or defaults, then update the state.
    # This is much cleaner and co-locates the logic.
    login_count = state.get("user:login_count", 0) + 1
    state["user:login_count"] = login_count
    state["task_status"] = "active"
    state["user:last_login_ts"] = time.time()
    state["temp:validation_needed"] = True
    print("State updated from within the `log_user_login` tool.")

    return {"status": "success","message": f"User login tracked. Total logins: {login_count}."}

# --- Demonstration of Usage ---
# In a real application, an LLM Agent would decide to call this tool.
# Here, we simulate a direct call for demonstration purposes.

async def main():
    session_service = InMemorySessionService()
    app_name, user_id, session_id = "state_app_tool", "user3", "session3"

    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state={"user:login_count": 0, "task_status": "idle"}
    )
    print(f"Initial state: {session.state}")

    # 2. Simulate a tool call (in a real app, the ADK Runner does this)
    # We create a ToolContext manually just for this standalone example.
    from unittest.mock import MagicMock
    mock_context = MagicMock(spec=ToolContext)
    mock_context.state = session.state

    # 3. Execute the tool
    log_user_login(mock_context)
    # 4. Check the updated state
    # Since we are bypassing the Runner, we check the session object directly.
    # In a real app, the Runner would persist these changes to the session service automatically.
    print(f"State after tool execution: {session.state}")

    # Expected output will show the same state change as the
    # "Before" case, but the code organization is significantly cleaner and more robust.

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())