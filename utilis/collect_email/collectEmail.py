from livekit.agents import AgentTask, function_tool

class CollectEmailAddress(AgentTask[bool]):
    def __init__(self, chat_ctx=None):
        with open('emailReq.txt','r') as file:
            content = file.read()
            file.close()

        super().__init__(
            instructions = content,
            chat_ctx=chat_ctx,
        )

    @function_tool
    async def address_given(self) -> None:
        """Use this when the user gives email address to record."""
        with open('emailDone.txt','a') as file:
            file.write('email added')
            file.close()
        self.complete(True)

    @function_tool
    async def address_notProvided(self) -> None:
        """Use this when the user denies to give email address."""
        self.complete(False)