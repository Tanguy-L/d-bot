import discord

class VCMMemberPool():
    __members = []

    def add(self, member) -> None:
        self.__members.append(member)

    def remove(self, member_id) -> None:
        for index, member in enumerate(self.__members):
            if member.id == member_id:
                self.__members.pop(index)

    def get(self, member_id) -> discord.Member:
        for member in self.__members:
            if member.id == member_id:
                return member
        return None

    def get_all(self) -> list:
        return self.__members
