"""Spotisub database"""
import uuid
from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import MetaData
from sqlalchemy import DateTime
from sqlalchemy.sql import func

SQLITE = 'sqlite'
SUBSONIC_PLAYLIST = 'subsonic_playlist'
SUBSONIC_SONG = 'subsonic_song'
SUBSONIC_ARTIST = 'subsonic_artist'
SUBSONIC_SONG_ARTIST_RELATION = 'subsonic_song_artist_relation'
SUBSONIC_SPOTIFY_RELATION = 'subsonic_spotify_relation'
SPOTIFY_SONG = 'spotify_song'
SPOTIFY_ARTIST = 'spotify_artist'
SPOTIFY_SONG_ARTIST_RELATION = 'spotify_song_artist_relation'


class Database:
    """Spotisub Database class"""
    DB_ENGINE = {
        SQLITE: 'sqlite:///cache/{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None

    def __init__(self, dbtype, dbname=''):
        """Spotisub Database init"""
        dbtype = dbtype.lower()
        engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
        self.db_engine = create_engine(engine_url, isolation_level=None)

    metadata = MetaData()

    subsonic_spotify_relation = Table(SUBSONIC_SPOTIFY_RELATION, metadata,
                                      Column(
                                          'uuid', String(36), primary_key=True, nullable=False),
                                      Column(
                                          'subsonic_song_id', String(36), nullable=True),
                                      Column(
                                          'subsonic_artist_id', String(36), nullable=True),
                                      Column(
                                          'subsonic_playlist_id', String(36), nullable=False),
                                      Column(
                                          'spotify_song_uuid', String(36), nullable=False),
                                      )

    spotify_song = Table(SPOTIFY_SONG, metadata,
                         Column(
                             'uuid',
                             String(36),
                             primary_key=True,
                             nullable=False),
                         Column('title', String(500), nullable=False),
                         Column('spotify_uri', String(500), nullable=False),
                         Column(
                             'tms_insert',
                             DateTime(
                                 timezone=True),
                             server_default=func.now(),
                             nullable=False),
                         Column(
                             'tms_update',
                             DateTime(
                                 timezone=True),
                             server_default=func.now(),
                             onupdate=func.now(),
                             nullable=False)
                         )

    spotify_song_artist_relation = Table(SPOTIFY_SONG_ARTIST_RELATION, metadata,
                                         Column(
                                             'song_uuid', String(36), nullable=False),
                                         Column(
                                             'artist_uuid', String(36), nullable=False)
                                         )

    spotify_artist = Table(SPOTIFY_ARTIST, metadata,
                           Column(
                               'uuid',
                               String(36),
                               primary_key=True,
                               nullable=False),
                           Column('name', String(500), nullable=False),
                           Column('spotify_uri', String(500), nullable=False),
                           Column(
                               'tms_insert',
                               DateTime(
                                   timezone=True),
                               server_default=func.now(),
                               nullable=False),
                           Column(
                               'tms_update',
                               DateTime(
                                   timezone=True),
                               server_default=func.now(),
                               onupdate=func.now(),
                               nullable=False)
                           )


def create_db_tables(self):
    """Create tables"""
    self.metadata.create_all(self.db_engine)


def insert_song(self, playlist_id, subsonic_track,
                artist_spotify, track_spotify):
    """insert song into database"""
    with self.db_engine.connect() as conn:
        spotify_song_uuid = insert_spotify_song(
            self, conn, artist_spotify, track_spotify)
        if spotify_song_uuid is not None:
            if subsonic_track is None:
                insert_playlist_relation(
                    self, conn, None, None, playlist_id, spotify_song_uuid)
            else:
                track_id = None
                artist_id = None
                if "id" in subsonic_track:
                    track_id = subsonic_track["id"]
                if "artistId" in subsonic_track:
                    artist_id = subsonic_track["artistId"]
                insert_playlist_relation(
                    self,
                    conn,
                    track_id,
                    artist_id,
                    playlist_id,
                    spotify_song_uuid)
            conn.commit()
        else:
            conn.rollback()
        conn.close()


def delete_playlist_relation_by_id(self, playlist_id: str):
    """delete playlist from database"""
    stmt = delete(self.subsonic_spotify_relation).where(
        self.subsonic_spotify_relation.c.subsonic_playlist_id == playlist_id)
    stmt.compile()
    with self.db_engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()
    conn.close()


def insert_playlist_relation(self, conn, subsonic_song_id,
                             subsonic_artist_id, subsonic_playlist_id, spotify_song_uuid):
    """insert playlist into database"""
    stmt = insert(
        self.subsonic_spotify_relation).values(
        uuid=str(
            uuid.uuid4().hex),
        subsonic_song_id=subsonic_song_id,
        subsonic_artist_id=subsonic_artist_id,
        subsonic_playlist_id=subsonic_playlist_id,
        spotify_song_uuid=spotify_song_uuid).prefix_with('OR IGNORE')
    stmt.compile()
    conn.execute(stmt)


def select_all_playlists(self, missing_only):
    """select playlists from database"""
    value = {}
    stmt = None
    with self.db_engine.connect() as conn:
        if missing_only:
            stmt = select(
                self.subsonic_spotify_relation.c.uuid,
                self.subsonic_spotify_relation.c.subsonic_song_id,
                self.subsonic_spotify_relation.c.subsonic_artist_id,
                self.subsonic_spotify_relation.c.subsonic_playlist_id,
                self.subsonic_spotify_relation.c.spotify_song_uuid).where(
                self.subsonic_spotify_relation.c.subsonic_song_id is None,
                self.subsonic_spotify_relation.c.subsonic_artist_id is None)
        else:
            stmt = select(
                self.subsonic_spotify_relation.c.uuid,
                self.subsonic_spotify_relation.c.subsonic_song_id,
                self.subsonic_spotify_relation.c.subsonic_artist_id,
                self.subsonic_spotify_relation.c.subsonic_playlist_id,
                self.subsonic_spotify_relation.c.spotify_song_uuid)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            song = select_spotify_song_by_uuid(
                self, conn, row.spotify_song_uuid)
            if song is not None and song.title is not None:
                artists_relation = select_spotify_song_artists_relation_by_song_uuid(
                    self, conn, row.spotify_song_uuid)
                artists = []
                for artist_rel in artists_relation:
                    artist_found = select_spotify_artists_by_uuid(
                        self, conn, artist_rel.artist_uuid)
                    if artist_found is not None and artist_found.name is not None:
                        artist_row = {}
                        artist_row["name"] = artist_found.name
                        artist_row["uri"] = artist_found.spotify_uri
                        artists.append(artist_row)
                if len(artists) > 0:
                    result = {}
                    result["spotify_song_title"] = song.title
                    result["spotify_song_uri"] = song.spotify_uri
                    result["spotify_artists"] = artists
                    result["subsonic_song_id"] = row.subsonic_song_id
                    result["subsonic_artist_id"] = row.subsonic_artist_id
                    result["subsonic_playlist_id"] = row.subsonic_playlist_id

                    if row.subsonic_playlist_id not in value:
                        value[row.subsonic_playlist_id] = []
                    value[row.subsonic_playlist_id].append(result)

        cursor.close()
        conn.close()

    return value


def select_spotify_artists_by_uuid(self, conn, c_uuid):
    """select spotify artists by uuid"""
    value = None
    stmt = select(
        self.spotify_artist.c.uuid,
        self.spotify_artist.c.name,
        self.spotify_artist.c.spotify_uri).where(
        self.spotify_artist.c.uuid == c_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
        cursor.close()

    return value


def insert_spotify_song(self, conn, artist_spotify, track_spotify):
    """insert spotify song"""
    song_db = select_spotify_song_by_uri(self, conn, track_spotify["uri"])
    song_uuid = None
    if song_db is None:
        song_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            self.spotify_song).values(
            uuid=song_uuid,
            title=track_spotify["name"],
            spotify_uri=track_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
    elif song_db is not None and song_db.uuid is not None:
        song_uuid = song_db.uuid

    if song_uuid is not None:
        artist_uuid = insert_spotify_artist(self, conn, artist_spotify)
        if artist_uuid is not None:
            insert_spotify_song_artist_relation(
                self, conn, song_uuid, artist_uuid)
            return song_uuid
    return song_uuid


def select_spotify_song_by_uri(self, conn, spotify_uri: str):
    """select spotify song by uri"""
    value = None
    stmt = select(
        self.spotify_song.c.uuid,
        self.spotify_song.c.spotify_uri,
        self.spotify_song.c.title).where(
        self.spotify_song.c.spotify_uri == spotify_uri)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
        cursor.close()

    return value


def select_spotify_song_by_uuid(self, conn, c_uuid):
    """select spotify song by uuid"""
    value = None
    stmt = select(
        self.spotify_song.c.uuid,
        self.spotify_song.c.spotify_uri,
        self.spotify_song.c.title).where(
        self.spotify_song.c.uuid == c_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
        cursor.close()

    return value


def insert_spotify_artist(self, conn, artist_spotify):
    """insert spotify artist"""
    artist_db = select_spotify_artist_by_uri(self, conn, artist_spotify["uri"])
    if artist_db is None:
        artist_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            self.spotify_artist).values(
            uuid=artist_uuid,
            name=artist_spotify["name"],
            spotify_uri=artist_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
        return artist_uuid
    if artist_db is not None and artist_db.uuid is not None:
        return artist_db.uuid
    return None


def select_spotify_artist_by_uri(self, conn, spotify_uri: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        self.spotify_artist.c.uuid,
        self.spotify_artist.c.name,
        self.spotify_artist.c.spotify_uri).where(
        self.spotify_artist.c.spotify_uri == spotify_uri)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
        cursor.close()

    return value


def insert_spotify_song_artist_relation(
        self, conn, song_uuid: int, artist_uuid: int):
    """insert spotify song artist relation"""
    if select_spotify_song_artist_relation(
            self, conn, song_uuid, artist_uuid) is None:
        stmt = insert(
            self.spotify_song_artist_relation).values(
            song_uuid=song_uuid,
            artist_uuid=artist_uuid)
        stmt.compile()
        conn.execute(stmt)
        conn.commit()


def select_spotify_song_artist_relation(
        self, conn, song_uuid: int, artist_uuid: int):
    """select spotify song artist relation"""
    value = None
    stmt = select(
        self.spotify_song_artist_relation.c.song_uuid,
        self.spotify_song_artist_relation.c.artist_uuid).where(
        self.spotify_song_artist_relation.c.song_uuid == song_uuid,
        self.spotify_song_artist_relation.c.artist_uuid == artist_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
        cursor.close()

    return value


def select_spotify_song_artists_relation_by_song_uuid(
        self, conn, song_uuid: int):
    """select spotify song artist relation by song uuid"""
    value = []
    stmt = select(self.spotify_song_artist_relation.c.artist_uuid).where(
        self.spotify_song_artist_relation.c.song_uuid == song_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value.append(row)
        cursor.close()

    return value
