from dotenv import load_dotenv
from livekit.agents import AgentTask, function_tool , RunContext
from utilis.sendMail.emailSend import emailSend

import os

from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero , groq , elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.beta.workflows import GetEmailTask



load_dotenv(".env.local")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY=os.getenv("ELEVENLAB_API_KEY")

class Assistant(Agent):
    def __init__(self) -> None:
        with open('instructions.txt','r') as file:
            content = file.read()
            file.close()
        super().__init__(         
              instructions=content,
        )

        self.user_problem = None
        self.solution = None
        
    @function_tool
    async def save_problem(self, problem: str):
        """Save user's problem for later email delivery"""
        self.user_problem = problem
        return {"ok": "problem_saved"}
    
    @function_tool
    async def save_solution(self, solution: str):
        """Save generated solution"""
        self.solution = solution
        return {"ok": "solution_saved"}
    
    @function_tool
    async def email_given(self, email: str):
        """Called when user confirms email"""

        if not self.solution:
            return {"error": "No solution available to send"}

        subject = "Solution to Your Problem"
        body = f"""
                    Hello,

                    Thank you for reaching out.

                    Here is the solution to your problem:

                    {self.solution}

                    If you need further help, feel free to reply.

                    Best regards,
                    AI Assistant
    """

        emailSend(email, body, subject)
        return {"ok": "email_sent"}
        
    # @function_tool()
    # async def get_alternate_contact_info(context: RunContext, contact_method: str, contact_value: str) -> None:
    #     """Collect alternative contact information when email isn't available"""
    #     # Store the alternative contact info
    #     context.session.userdata.alternate_contact_method = contact_method
    #     context.session.userdata.alternate_contact_value = contact_value
    #     await context.session.generate_reply(
    #     instructions=f"Acknowledge that you've recorded their {contact_method}: {contact_value}. Let them know this will be used for communication instead of email."
    # )

server = AgentServer() 

@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        stt=groq.STT(
      model="whisper-large-v3-turbo",
      language="en",
   ),
        llm=groq.LLM(
        model="llama-3.1-8b-instant"
    ),
      tts=elevenlabs.TTS(
      voice_id="ODq5zmih8GrVes37Dizd",
      model="eleven_multilingual_v2"
   ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    content =None
    with open('instructions.txt','r') as file:
            content = file.read()
            file.close()

    await session.generate_reply(
        instructions = content
    )
    
 


if __name__ == "__main__":
    agents.cli.run_app(server)