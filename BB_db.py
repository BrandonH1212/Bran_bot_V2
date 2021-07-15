import asyncio
import sqlite3
from pyosu import OsuApi
from BB_keys import osu_key

global db, api


def initialize_database():  # Initialize the database and osu API objects So we can get them from anywhere
    global db, api  # ps...Don't call this from anywhere except main
    db = Database()
    api = OsuApi(osu_key)
    return db, api


class Database:  # Main object I use for getting information and updating information from SQL late database
    def __init__(self):
        self.sql = sqlite3.connect('bran_bot.db', )
        self.initialize_database()

    def initialize_database(self):  # Create the database if it doesn't exist
        try:
            # Create player table else use existing
            self.sql.execute("""
            CREATE TABLE players
            (id INTEGER, name TEXT, discord_id TEXT, osu_id INTEGER, 
            PRIMARY KEY(id))
            """)
            print("Created Player table")
        except Exception as e:
            print(e)
        try:
            # Create Maps/mapSets table else use existing
            self.sql.execute("""
            CREATE TABLE mapSets
            (beatmapset_id INTEGER,
            artist TEXT,
            song_name TEXT,
            tags TEXT,
            approved INTEGER,
            bpm FLOAT, UNIQUE(beatmapset_id))
            """)
            self.sql.execute("""
            CREATE TABLE maps
            (set_id INTEGER,
            beatmap_id  INTEGER,
            diff_name TEXT,
            star FLOAT,
            cs FLOAT,
            od FLOAT,
            ar FLOAT,
            hp FLOAT,
            length FLOAT,
            mode INTEGER,
            max_combo INTEGER,
            FOREIGN KEY(set_id) REFERENCES mapSets(beatmapset_id),
            UNIQUE(beatmap_id))
            """)
            print("Created Maps/mapSets table")
        except Exception as e:
            print(e)

        self.sql.execute("VACUUM")  # Cleanup the database from last run
        self.sql.commit()

    async def is_registered(self, discord_id):  # Check if a user is in the database returns true/false
        cur = self.sql.cursor()
        return cur.execute("""
        SELECT id 
        FROM players
        WHERE discord_id IN (?);
        """, (discord_id,)).fetchone() is not None

    async def get_all_players(self):  # Returns a list of all players in the database as Player objects
        cur = self.sql.cursor()
        found = cur.execute("""
               SELECT * 
               FROM players;
               """).fetchall()
        found_players = []

        for player in found:
            found_players.append(Player(player[1], player[2], player[3], player[0]))

        return found_players

    async def get_player(self, discord_id):  # Get a player object from discord ID If not registered get None
        cur = self.sql.cursor()
        found = cur.execute("""
        SELECT * 
        FROM players
        WHERE discord_id IN (?);
        """, (discord_id,)).fetchone()
        if found is None:
            return None
        else:
            print(found)
            return Player(found[1], found[2], found[3], found[0])

    async def get_player_form_osu(self,
                                  name):  # Get a player from the osu API Only use this if the player is not in database
        try:
            name = str(name).lstrip()
        except Exception as e:
            print(e)
            return None

        return await api.get_user(user=name)

    async def register_player(self, name, discord_id, osu_id):  # Adds a player to the Database
        if await self.get_player(discord_id) is None:
            try:
                self.sql.execute("""
                INSERT INTO players
                (name, discord_id, osu_id) VALUES(?, ?, ?)
                 """, [name, discord_id, osu_id])
                self.sql.commit()
                return True
            except Exception as e:
                print(e)
                return False
        return True

    async def update_osu_id(self, discord_id, new_osu_id):
        player = await self.get_player(discord_id)
        if player is not None:
            try:
                self.sql.execute("""
                UPDATE players
                SET osu_id = (?)
                WHERE discord_id = (?)
                """, [new_osu_id, player.discord_id])
                self.sql.commit()
                return True
            except Exception as e:
                print("Failed")
                print(e)
        return False

    async def add_osu_map(self, map_id):  # Add osu_mapSet to the database Returns true if successful
        inset = await db.is_set_or_map_in_db(map_id)
        if not inset:
            try:
                map_set = await api.get_beatmaps(beatmapset_id=map_id)  # Check if it's a set

                if map_set is None:
                    map_set = await api.get_beatmap(beatmap_id=map_id)  # If it's not a set get the map

                    if map_set is not None:
                        map_set = await api.get_beatmaps(
                            beatmapset_id=map_set.beatmapset_id)  # From the map we can get the set
            except:
                print(f"Failed to Process {map_id}")
                return False

            if map_set is not None:
                for b_map in map_set:
                    test = b_map.bpm  # Make sure the beat map has values properly set
                    self.sql.execute("""
                    INSERT OR IGNORE INTO mapSets
                    (beatmapset_id, artist, song_name, tags, approved, bpm) VALUES(?, ?, ?, ?, ?, ?)
                    """, [b_map.beatmapset_id, b_map.artist, b_map.title, b_map.tags, int(b_map.approved), b_map.bpm])

                    self.sql.execute("""
                    INSERT OR IGNORE INTO maps
                    (set_id, beatmap_id, diff_name, star, cs, od, ar, hp, length, mode, max_combo) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [b_map.beatmapset_id, b_map.beatmap_id, b_map.version, b_map.difficultyrating, b_map.diff_size,
                          b_map.diff_overall,
                          b_map.diff_approach, b_map.diff_drain, b_map.total_length, int(b_map.mode), b_map.max_combo])
                    self.sql.commit()
                    print(f"Added {b_map.beatmapset_id} | {b_map.title}")

            else:
                print("Failed to find")
                return False
        else:
            print("Already inset")
            return True

    async def get_osu_map(self, map_id, use_osu_api=False):  # Get a map object from the database
        found, sql = await self.is_map_in_db(map_id)  # use_osu_api Will use the osu API as a fallback
        if found:
            return Beatmap(sql)
        else:
            if use_osu_api:
                b_map = await api.get_beatmap(beatmap_id=map_id)
                if b_map is not None:
                    return b_map

                await self.add_osu_map(map_id)
                return b_map
            return None

    async def is_map_in_db(self, map_id):  # Check if a map is in the database if so return True and the result query
        cur = self.sql.cursor()
        sql = cur.execute("""
            SELECT *
            FROM maps
            JOIN mapSets ON maps.set_id = mapSets.beatmapset_id
            WHERE beatmap_id = ?
            """, (map_id,)).fetchone()
        if sql is not None:
            return True, sql
        return False, None


    async def get_maps(self, star_r=[0, 10], len_r=[0, 10000], mode=0, approved=1, limit=1): # Query the database for X number of random maps
        cur = self.sql.cursor()
        return_maps = []  # Do the search first then order by random
        q_maps = cur.execute("""
        SELECT * FROM (
                SELECT *
                FROM maps
                JOIN mapSets ON maps.set_id = mapSets.beatmapset_id
                WHERE mode = ?
                AND approved = ?
                AND star BETWEEN ? AND ?
                AND length  BETWEEN ? AND ?)
        ORDER BY RANDOM()
        LIMIT ?
                """, ([mode, approved, star_r[0], star_r[1], len_r[0], len_r[1], limit])).fetchall()

        for b_map in q_maps:
            return_maps.append(Beatmap(b_map))

        return return_maps

    async def is_set_in_db(self, map_id):
        cur = self.sql.cursor()
        if cur.execute("""
               SELECT beatmapset_id
               FROM mapSets
               WHERE beatmapset_id = ?
               """, (map_id,)).fetchone() is not None:
            return True

        return False

    async def is_set_or_map_in_db(self, map_id, use_osu_api=False):
        cur = self.sql.cursor()
        if cur.execute("""
                SELECT *
                FROM maps
                JOIN mapSets ON maps.set_id = mapSets.beatmapset_id
                WHERE beatmapset_id = ? 
                OR  beatmap_id = ?
               """, (map_id, map_id)).fetchone() is not None:
            return True
        else:
            if use_osu_api:
                return await self.add_osu_map(map_id)
        return False


class Player:
    def __init__(self, name=None, discord_id=None, osu_id=None, table_key=None):
        self.name = name
        self.discord_id = discord_id
        self.osu_id = osu_id
        self.table_key = table_key

    def __repr__(self):
        return f"{self.name} " \
               f"discord_id={self.discord_id} " \
               f"osu_id={self.osu_id} " \
               f"table_key={self.table_key}"

    async def get_recent(self, number=1):
        return await api.get_user_recents(user=self.osu_id, limit=number)

    async def get_osu_user(self):
        return await api.get_user(self.osu_id)

    async def get_best(self, number=3):
        return await api.get_user_bests(self.osu_id, limit=number)


class Beatmap():  # This object mimics The same object from the osu API I'm using so I can substitute them
    def __init__(self,
                 sql):  # This assumes Output of  SELECT * FROM maps JOIN mapSets ON maps.set_id = mapSets.beatmapset_id as sql
        # sql data
        self.beatmapset_id = sql[0]
        self.beatmap_id = sql[1]
        self.version = sql[2]  # difficulty name
        self.difficultyrating = sql[3]  # The amount of stars the map would have ingame and on the website
        self.diff_size = sql[4]  # Circle size value  (CS)
        self.diff_overall = sql[5]  # Overall difficulty (OD)
        self.diff_approach = sql[6]  # Approach Rate      (AR)
        self.diff_drain = sql[7]  # Healthdrain        (HP)
        self.total_length = sql[8]  # seconds from first note to last note including breaks
        self.hit_length = sql[8]
        self.mode = sql[9]  # game mode, Osu = 0  Taiko = 1 Catch = 2 Mania = 3
        self.max_combo = sql[10]  # The maximum combo a user can reach playing this beatmap
        self.artist = sql[12]
        self.title = sql[13]  # song name
        self.tags = sql[14]  # song tags
        self.approved = sql[
            15]  # Map state Graveyard = -2  WIP = -1 Pending = 0 Ranked = 1 Approved  = 2 Qualified = 3 Loved = 4
        self.bpm = sql[16]
        self.map_url = f"https://osu.ppy.sh/b/{self.beatmap_id}/"
        self.img_url = f"https://assets.ppy.sh/beatmaps/{self.beatmapset_id}/covers/cover.jpg"

    def __repr__(self):
        return f"Beatmap: {self.title} [{self.version}] beatmap_id={self.beatmap_id}"


async def main():   # Run this file directly to help test/Play around with stuff
    db, api = initialize_database()
    print(await db.get_maps_by_query())


if __name__ == '__main__':
    asyncio.run(main())
