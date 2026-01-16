from dotenv import load_dotenv
from livekit.agents import function_tool
from services.sendMail.emailSend import emailSend
from services.meet import get_calendar_service, eventCreate
import asyncio
from typing import Annotated
from typing import Optional 
# from datetime import daytime

import os

from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation , groq , elevenlabs ,silero
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.beta.workflows import GetEmailTask



load_dotenv(".env.local")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY=os.getenv("ELEVEN_API_KEY")

class Assistant(Agent):
    def __init__(self) -> None:
        with open('instructions.yaml','r') as file:
            content = file.read()
            # file.close()
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
    async def save_meeting_decision(self, agreed: Annotated[str, "Whether the user agreed (true/false)"]):
        """save the user decision regarding scheduling meeting"""
        self.meeting_agreed = str(agreed).strip().lower() in ("true", "yes", "1")
        print(f"-: save_meeting_decision -> meeting_agreed = {self.meeting_agreed}:-")
        return {"ok":"User decision saved"} 


    
    @function_tool
    async def meeting_datetime(self,schedule_date_time:str,schedule_end_time:str, email: Optional[str] = None) -> dict:       
            """call when user agreed for meeting else ignore"""
            if not self.user_email:
                return{"error": "User email is missing...."}
            
            if email:
                self.user_email = email
                print(f"-: meeting_datetime -> email provided in call: {email}")
            
            # tz = pytz.timezone("Asia/Karachi")
            self.schedule_date_time = schedule_date_time
            # self.schedule_time = schedule_time
            self.schedule_end_time = schedule_end_time
            
            try:
                 service = await asyncio.to_thread(get_calendar_service)
                 await asyncio.to_thread(eventCreate,service,"Schedule Meeting","Lahore","Diagnose the problem from root cause",schedule_date_time,schedule_end_time,self.user_email)

           
            # eventCreate("Schedule Meeting","Lahore","Dignose the problem from root cause",schedule_date,schedule_end_time,self.user_email)
            except Exception as e:
                 print(f"[ERROR] meeting_datetime -> calendar creation failed: {e}")
                 return {"error": f"Calendar event creation failed: {str(e)}"}            
            print(f"[DEBUG] meeting_datetime -> scheduled {schedule_date_time} to {schedule_end_time} for {self.user_email}")
            return {"ok": "Date and time set for meeting + calnedar event pushed"}
    
    @function_tool
    async def email_sending(self, confirm: Annotated[str, "Whether the user confirmed sending the email (true/false)"],user_email: Optional[str] = None,solution: Optional[str] = None ) -> dict:
        """Send final email with solution and optional meeting details"""
        print("enter in the emailsending function")

        try:
            if isinstance(confirm, str):
                confirm_bool = confirm.strip().lower() in ("true", "yes", "1")
            elif isinstance(confirm, bool):
                confirm_bool = confirm
            else:
                # fallback: attempt string conversion
                confirm_bool = str(confirm).strip().lower() in ("true", "yes", "1")
        except Exception:
            confirm_bool = False

        if not confirm_bool:
            return {"error": "Email sending not confirmed"}
        
        effective_email = user_email or self.user_email
        effective_solution = solution or self.solution
        print(f"[DEBUG] email_sending -> effective_email={effective_email}, has_solution={bool(effective_solution)}")


        if not effective_email or not effective_solution:
            return {"error": "Missing solution or email"}

        subject = "Solution to Your Problem"

        body = f"""
    Hello,

    Thank you for reaching out.

    Here is the solution to your problem:

    {effective_solution}
    """

        if self.meeting_agreed:
            body += f"""

    We have also scheduled a meeting to discuss this further.

    Meeting Date and Time: {self.schedule_date_time}

    End Time: {self.schedule_end_time}

    You will receive a calendar invitation shortly.
    """

        body += """

    If you need further help, feel free to reply.

    Best regards,
    AI Assistant
    """
        try:
            await asyncio.to_thread(emailSend,effective_email, body, subject)
            print(f"[DEBUG] email_sending -> emailSend succeeded to {effective_email}")
        except Exception as e:
            return {"error :-Email sending failed:": str(e)}
        
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

@server.rtc_session(agent_name="my-voice-agent")
async def my_agent(ctx: agents.JobContext):
    await ctx.connect()
    session = AgentSession(
        stt=groq.STT(
      model="whisper-large-v3-turbo",
      language="en",
   ),
        llm=groq.LLM(
        model="meta-llama/llama-4-scout-17b-16e-instruct"
    ),
    tts=elevenlabs.TTS(
    api_key=ELEVEN_API_KEY,
    voice_id="pNInz6obpgDQGcFmaJgB",
    model="eleven_flash_v2_5"
),

    vad=silero.VAD.load(),
    )

    print("---- Starting agent session...")

    await session.start(
        room=ctx.room,
        # demo_room=ctx.room.name,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )
    print("--------- Agent has started session----------")
    print("Room name:", ctx.room.name)
    print("Demo room:", ctx.room)
    

    # content =None
    # with open('instructions.yaml','r') as file:
    #         content = file.read()
    #         file.close()

    # await session.generate_reply(
    #     instructions = content
    # )
    
 


if __name__ == "__main__":
    agents.cli.run_app(server)