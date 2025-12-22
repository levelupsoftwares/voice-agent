from dotenv import load_dotenv
from livekit.agents import function_tool
from services.sendMail.emailSend import emailSend
from services.meet import get_calendar_service, eventCreate
import asyncio

import os

from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero , groq , elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.beta.workflows import GetEmailTask



load_dotenv(".env.local")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ELEVEN_API_KEY=os.getenv("ELEVENLAB_API_KEY")

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
        self.user_email = None
        self.meeting_agreed = False
        self.schedule_date_time = None

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
    async def email_store(self, user_email: str):
        """Store the confirms email"""
        self.user_email=  user_email
        return{"ok":"user email stored"}

    @function_tool
    async def save_meeting_decision(self, agreed: bool):
        """save the user decision regarding scheduling meeting"""
        self.meeting_agreed = agreed
        return {"ok":"User decision saved"}


    
    @function_tool
    async def meeting_datetime(self,schedule_date_time:str,schedule_end_time:str):       
            """call when user agreed for meeting else ignore"""
            if not self.user_email:
                return{"error": "User email is missing...."}
            
            self.schedule_date_time = schedule_date_time
            # self.schedule_time = schedule_time
            self.schedule_end_time = schedule_end_time
            
            service = await asyncio.to_thread(get_calendar_service)
            await asyncio.to_thread(eventCreate,service,"Schedule Meeting","Lahore","Diagnose the problem from root cause",schedule_date_time,schedule_end_time,self.user_email)
            # eventCreate("Schedule Meeting","Lahore","Dignose the problem from root cause",schedule_date,schedule_end_time,self.user_email)

            return {"ok": "Date and time set for meeting + calneder event pushed"}
    
    @function_tool
    async def email_sending(self,confirm: bool):
        """Send final email with solution and optional meeting details"""
        if not confirm:
            return {"error": "Email sending not confirmed"}
    
        if not self.solution or not self.user_email:
            return {"error": "Missing solution or email"}

        subject = "Solution to Your Problem"

        body = f"""
    Hello,

    Thank you for reaching out.

    Here is the solution to your problem:

    {self.solution}
    """

        if self.meeting_agreed:
            body += f"""

    We have also scheduled a meeting to discuss this further.

    Meeting Date and Time: {self.schedule_date_time}
    # Start Time: {self.schedule_time}
    End Time: {self.schedule_end_time}

    You will receive a calendar invitation shortly.
    """

        body += """

    If you need further help, feel free to reply.

    Best regards,
    AI Assistant
    """
        try:
            await asyncio.to_thread(emailSend,self.user_email, body, subject)
        except Exception as e:
            return {"error": str(e)}
        
        return{'ok':"email_sent"}




    # async def email_sending(self, email: str):
    #     """Called when user confirms email"""

    #     if not self.solution:
    #         return {"error": "No solution available to send"}

    #     subject = "Solution to Your Problem"
    #     body = f"""
    #                 Hello,

    #                 Thank you for reaching out.

    #                 Here is the solution to your problem:

    #                 {self.solution}

    #                 If you need further help, feel free to reply.

    #                 Best regards,
    #                 AI Assistant
    # """

    #     emailSend(email, body, subject)
    #     return {"ok": "email_sent"}
    
    # @function_tool
    # async def shedule_meet(self, email: str,date,):
    #     """call this when user give an emailaddress"""
    #     eventCreate("summary","location","description",20,"00:17:00","00:17:30","usmanbutt2357@gmail.com")
    #     return {"ok": "solution_saved"}
        
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
      tts=groq.TTS(
      model = "playai-tts",
      voice = "Fritz-PlayAI",
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