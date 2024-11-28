from typing import Dict, Optional
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


"""  
===================================================

GLOBAL VAR

==================================
"""
load_dotenv()

#DB CONNECTION
_host = os.getenv("HOST")
_port = os.getenv("PORT")
_user=os.getenv("USERDB")
_password=os.getenv("PASSWORD")
_db_name=os.getenv("DATABASE")

create_tables_plg = """
    START TRANSACTION;

    CREATE TABLE IF NOT EXISTS `members` (
        `id` int NOT NULL,
        `discord_id` bigint UNSIGNED NOT NULL DEFAULT '0',
        `discord_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        `steam_id` bigint UNSIGNED DEFAULT NULL,
        `weight` int DEFAULT '6',
        `is_logged_in` tinyint(1) DEFAULT NULL,
        `smoke_color` enum('red','green','blue','blue-night','gold','white','black','turquoise','deep-purple','more-pink','yellow','pink','default','green-light') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'red'
        ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    

    CREATE TABLE IF NOT EXISTS `teams` (
        `team_id` int NOT NULL,
        `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '0',
        `channel_id` bigint UNSIGNED DEFAULT NULL,
        `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    CREATE TABLE IF NOT EXISTS `team_members` (
        `team_member_id` int NOT NULL,
        `team_id` int NOT NULL,
        `member_id` int NOT NULL
        ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    COMMIT;
"""
get_parties = """SELECT * FROM party"""
do_member_exists = """SELECT EXISTS (SELECT 1 FROM member WHERE %s=?)"""
add_member = """
    INSERT INTO members (
        discord_id,
        discord_name,
        steam_id,
        weight,
        is_logged_in,
        smoke_color
    ) VALUES (
    %s,
    %s,
    NULL
    ,0
    ,0,
    'red'
    )
"""
set_member_data = """UPDATE member SET %s=? WHERE %s=?"""

class VCMDatabase():
    """  
    ===================================================

    BASE CONFIG ON DB CONNECTION

    ==================================
    """
    def __connect(self) -> mysql.connector.connection.MySQLConnection:
        connection = None
        try:
            print(_host)
            print(_db_name)
            print(_user)
            print(_password)
            connection = mysql.connector.connect(
                host=_host,
                port=_port,
                database=_db_name,
                user=_user,
                password=_password
            )
            if connection.is_connected():
                print("Connected to MySQL database")
        except Error as err:
            print(f"Error: {err}")
        finally:
            return connection
    
    def __init_database(self) -> None:
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_tables_plg, multi=True)
            self.alter_teams()
            self.alter_members()
            self.alter_team_members()
        except Error as err:
            print(err)

    def __init__(self):
        self.connection = self.__connect()
        self.__init_database()

    def alter_team_members(self): 
        cursor = self.connection.cursor()

        # Check if teams table has a primary key
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'team_members' 
              AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        """)
        has_primary_key = cursor.fetchone()[0] > 0

        if not has_primary_key:
            # If no primary key, add primary key and unique keys
            cursor.execute("""
                ALTER TABLE `team_members`
                ADD PRIMARY KEY (`team_member_id`),
                ADD KEY `TEAM` (`team_id`),
                ADD KEY `MEMBER` (`member_id`);
                MODIFY `team_member_id` int NOT NULL AUTO_INCREMENT;
                ADD CONSTRAINT `MEMBER` FOREIGN KEY (`member_id`) REFERENCES `members` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
                ADD CONSTRAINT `TEAM` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`) ON DELETE CASCADE ON UPDATE CASCADE;
            """)
            print("Added primary key and unique keys to team_members table.")
        else:
            print("TeamMembers table already has a primary key.")

    def alter_teams(self): 
        cursor = self.connection.cursor()

        # Check if teams table has a primary key
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'teams' 
              AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        """)
        has_primary_key = cursor.fetchone()[0] > 0

        if not has_primary_key:
            # If no primary key, add primary key and unique keys
            cursor.execute("""
                ALTER TABLE `teams`
                ADD PRIMARY KEY (`team_id`),
                ADD UNIQUE KEY `TEAM KEY` (`name`),
                ADD UNIQUE KEY `CHANNEL KEY` (`channel_id`)
                MODIFY `team_id` int NOT NULL AUTO_INCREMENT;
            """)
            print("Added primary key and unique keys to teams table.")
        else:
            print("Teams table already has a primary key.")
    
    def alter_members(self):
        cursor = self.connection.cursor()

        # Check if members table has a primary key
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'members' 
              AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        """)
        has_primary_key = cursor.fetchone()[0] > 0

        if not has_primary_key:
            # If no primary key, add primary key and unique keys
            cursor.execute("""
                ALTER TABLE `members`
                ADD PRIMARY KEY (`id`),
                ADD UNIQUE KEY `IndexDiscordId` (`discord_id`),
                ADD UNIQUE KEY `IndexSteamId` (`steam_id`);
                MODIFY `id` int NOT NULL AUTO_INCREMENT;
            """)
            print("Added primary key and unique keys to members table.")
        else:
            print("Teams table already has a primary key.")
    """  
    ===================================================

    REQUESTS FOR THE DISCORD

    ==================================
    """
    def is_discord_member_known(self, discord_id: str) -> bool:
        query = "SELECT COUNT(*) FROM members WHERE discord_id = %s"
        print(query)
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, ([discord_id]))
            result = cursor.fetchone()
            print(result)
            return result[0] > 0 if result else False
        except Error as err:
            print(f"Error: {err}")
            return False

    def add_member(self, member_id: int, member_name: str) -> None:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(add_member, (member_id, member_name))
            self.connection.commit()
            print(f"Successfully added member: {member_name} with Discord ID: {member_id}")
        except Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

    def get_parties_channel(self):
        try:
            cursor = self.connection.cursor()
            rows = cursor.execute(get_parties).fetchall()
            cursor.close()

            parties = {}
            for r in rows:
                parties[r['CsId']] = r['ChannelId']
            return parties
        except Error as err:
            print(err)

    def get_member(self, member_id, filter_column="discord_id") -> Optional[Dict]:
        query = f"""
        SELECT m.*, t.team_id, t.name as team_name, t.channel_id as team_channel_id
        FROM members m
        LEFT JOIN team_members tm ON m.id = tm.member_id
        LEFT JOIN teams t ON tm.team_id = t.team_id
        WHERE m.{filter_column} = %s
        """
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (member_id,))
                row = cursor.fetchone()
            return row
        except Error as err:
            print(f"Error in get_member: {err}")
            return None


    def set_member_connection_state(self, member_id: int, state: bool):
        query = "UPDATE members SET is_logged_in = %s WHERE discord_id = %s"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (int(state), member_id))
            self.connection.commit()
        except Error as err:
            print(f"Error: {err}")
            self.connection.rollback()