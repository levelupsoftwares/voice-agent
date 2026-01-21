from dotenv import load_dotenv
from livekit.agents import function_tool
from services.sendMail.emailSend import emailSend
from services.meet import get_calendar_service, eventCreate
import asyncio
from typing import Annotated
from typing import Optional 
from services.time_resolver import resolve_time
from datetime import datetime
import pytz

import os

from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation , groq , elevenlabs ,silero
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
# from livekit.agents.beta.workflows import GetEmailTask



load_dotenv(".env.local")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY=os.getenv("ELEVEN_API_KEY")

def humanize_datetime(dt_str: str) -> str:
    """
    Convert ISO-8601 datetime string to human-friendly format
    Example:
    2026-01-21T21:02:41+05:00
    →
    Wednesday, 21 January 2026 at 09:02 PM
    """
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%A, %d %B %Y at %I:%M %p")


class Assistant(Agent):
    def __init__(self) -> None:
        with open('instructions.yaml','r') as file:
            content = file.read()
        
        current_dt = self.get_current_datetime()
        instructions = content.replace(
            "{{CURRENT_DATETIME}}",
            current_dt
        )
            # file.close()
        super().__init__(         
              instructions=instructions,
        )

        self.user_problem = None
        self.solution = None
        self.user_email = None
        self.meeting_agreed = False
        self.schedule_date_time = None
        self.schedule_end_time = None

    def get_current_datetime(self) -> str:
        """Return current date and time in Asia/Karachi as ISO-8601 string"""
        TZ = pytz.timezone("Asia/Karachi")
        return datetime.now(TZ).isoformat(timespec="seconds")
    
    async def start_session_context(self, session: AgentSession):
        """Inject current datetime into LLM context each time session starts"""
        current_dt = self.get_current_datetime()
        


    async def handle_schedule_intent(self, intent, email):
        """
         intent example:
            {
                "text": "Tomorrow at 2:30 PM"
            }
        """
        current_dt = self.get_current_datetime()
        times = resolve_time(intent, current_dt=current_dt)

        return await self.meeting_datetime(
            schedule_date_time=times["start"],
            schedule_end_time=times["end"],
            email=email
        )

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
    async def schedule_meeting_from_intent(
        self,
        day: str,
        hour: int,
        minute: int,
        email: Optional[str] = None
    ):
        if not self.meeting_agreed:
            return {"error": "User has not agreed to schedule a meeting"}

        intent = {
            "day": day,
            "hour": hour,
            "minute": minute
        }

        return await self.handle_schedule_intent(intent, email)


    
    @function_tool
    async def meeting_datetime(self,schedule_date_time:str,schedule_end_time:str, email: Optional[str] = None) -> dict:       
            """call when user agreed for meeting else ignore"""
            if email:
                self.user_email = email
                print(f"-: meeting_datetime -> email provided in call: {email}")

            if not self.user_email:
                return{"error": "User email is missing...."}
            
            
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

    Here are the recommended steps to address the issue:

    {effective_solution}
    """

        if self.meeting_agreed:
            human_S_time = humanize_datetime(self.schedule_date_time)
            human_E_time = humanize_datetime(self.schedule_end_time)
            body += f"""

    We have also scheduled a meeting to discuss this further.

    Meeting Date and Time: {human_S_time}

    Estimated Duration: 45 minutes (until {human_E_time})

    You will receive a calendar invitation shortly.
    """

        body += """

    If you need further help, feel free to reply.

    Best regards,
    William from SureShield Roofing
    """
        try:
            await asyncio.to_thread(emailSend,effective_email, body, subject)
            print(f"[DEBUG] email_sending -> emailSend succeeded to {effective_email}")
        except Exception as e:
            return {"error :-Email sending failed:": str(e)}
        
        return{'ok':"email_sent"}




server = AgentServer() 

@server.rtc_session(agent_name="my-voice-agent")
async def my_agent(ctx: agents.JobContext):
    await ctx.connect()
    agent_instance = Assistant()
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
    agent_instance = Assistant()
    current_dt = agent_instance.get_current_datetime()
      

    await session.start(
        room=ctx.room,
        agent=agent_instance,
        # demo_room=ctx.room.name,
        # agent=Assistant(),
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