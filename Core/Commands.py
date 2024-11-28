class VCMCommand():
    def __init__(self, name, args_count, callback) -> None:
        self.name = name
        self.args_count = args_count - 1
        self.callback = callback
        self.args = []

    def check_requirement(self, name, args) -> bool:
        return self.name == name and self.args_count == len(args)

    async def execute(self, ctx):
        await self.callback(ctx, *self.args)