# agent.py
from dotenv import load_dotenv
import os
import logging
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins.google.beta.realtime import RealtimeModel
from prompts import INSTRUCTIONS, WELCOME_MESSAGE

# import the tools you exposed from tools.py
from tools import (
    get_datetime,
    get_weather,
    create_ticket,
    get_ticket_by_serial_tool,
    list_tickets_tool,
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=INSTRUCTIONS,
            llm=RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Puck",
                api_key=os.getenv("GOOGLE_API_KEY"),
            ),
            tools=[
                # calling my tools function
                get_weather,
                get_datetime,
                create_ticket,
                get_ticket_by_serial_tool,
                list_tickets_tool,
            ],
        )


async def entrypoint(ctx: agents.JobContext):
    assistant = Assistant()
    session = AgentSession()

    # Connect to the room
    await ctx.connect()
    logging.info("Agent connected to the room.")

    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    logging.info("Agent session started.")

    # The agent will speak the welcome message unprompted at the start 1
    # The agent will now run and respond to the user until the job is terminated 2
    await session.generate_reply(instructions=WELCOME_MESSAGE)
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))