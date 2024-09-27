"""Spotisub database"""
import uuid
import string
import logging
from config import Config
from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import MetaData
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy import desc
from sqlalchemy import or_
from sqlalchemy import collate

VERSION = "0.3.1"
VERSIONS = ["0.3.0-alpha-01", "0.3.1"]

SQLITE = 'sqlite'
USER = 'user'
CONFIG_TABLE = 'config_table'
SUBSONIC_SPOTIFY_RELATION = 'subsonic_spotify_relation'
PLAYLIST_INFO = 'playlist_info'
SPOTIFY_SONG = 'spotify_song'
SPOTIFY_ARTIST = 'spotify_artist'
SPOTIFY_ALBUM = 'spotify_album'
SPOTIFY_SONG_ARTIST_RELATION = 'spotify_song_artist_relation'


class Database:
    """Spotisub Database class"""
    DB_ENGINE = {
        SQLITE: Config.SQLALCHEMY_DATABASE_PATH + '/{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None

    def __init__(self, dbtype, dbname=''):
        """Spotisub Database init"""
        dbtype = dbtype.lower()
        engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
        self.db_engine = create_engine(engine_url, isolation_level=None)

    metadata = MetaData()

    user = Table(USER, metadata,
                 Column(
                     'id', Integer, primary_key=True, autoincrement=True),
                 Column(
                     'username', String(36), unique=True, index=True, nullable=False),
                 Column(
                     'password_hash', String(128), nullable=False)
                 )

    config_table = Table(CONFIG_TABLE, metadata,
                         Column(
                             'id', Integer, primary_key=True, autoincrement=True),
                         Column(
                             'name', String(500), unique=True, index=True, nullable=False),
                         Column(
                             'value', String(500), nullable=False)
                         )

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
                                          'subsonic_playlist_name', String(500), nullable=False),
                                      Column(
                                          'spotify_song_uuid', String(36), nullable=False),
                                      )

    playlist_info = Table(PLAYLIST_INFO, metadata,
                                      Column(
                                          'uuid', String(36), primary_key=True, nullable=False),
                                      Column(
                                          'spotify_playlist_uri', String(36), nullable=True),
                                      Column(
                                          'type', String(36), nullable=False),
                                      Column(
                                          'subsonic_playlist_id', String(36), nullable=False)
                                      )

    spotify_song = Table(SPOTIFY_SONG, metadata,
                         Column(
                             'uuid',
                             String(36),
                             primary_key=True,
                             nullable=False),
                         Column(
                             'album_uuid', String(36), nullable=False),
                         Column('title', String(500), nullable=False),
                         Column(
                             'spotify_uri',
                             String(500),
                             nullable=False,
                             unique=True),
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
                           Column(
                               'spotify_uri',
                               String(500),
                               nullable=False,
                               unique=True),
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

    spotify_album = Table(SPOTIFY_ALBUM, metadata,
                          Column(
                              'uuid',
                              String(36),
                              primary_key=True,
                              nullable=False),
                          Column('name', String(500), nullable=False),
                          Column(
                              'spotify_uri',
                              String(500),
                              nullable=False,
                              unique=True),
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


def create_db_tables():
    """Create tables"""
    dbms.metadata.create_all(dbms.db_engine)
    upgrade()


def upgrade():
    """Upgrade db"""
    upgraded = False
    with dbms.db_engine.connect() as conn:
        fconfig = select_config_by_name(conn, 'VERSION')
        if fconfig is None or fconfig.value not in VERSIONS:
            # FIRST RELEASE 3.0.0 DROPPING ENTIRE DATABASE
            drop_table(conn, SPOTIFY_SONG)
            drop_table(conn, SPOTIFY_ALBUM)
            drop_table(conn, SPOTIFY_ARTIST)
            drop_table(conn, SPOTIFY_SONG_ARTIST_RELATION)
            drop_table(conn, SUBSONIC_SPOTIFY_RELATION)
        if fconfig is None or fconfig.value != VERSION:
            insert_or_update_config(conn, 'VERSION', VERSION)
            conn.commit()
            upgraded = True
        conn.close()
    if upgraded:
        dbms.metadata.create_all(dbms.db_engine)


def drop_table(conn, table_name):
    """Drops single table"""
    query = "DROP TABLE IF EXISTS " + table_name
    conn.execute(text(query))


def user_exists():
    """Check if user exists"""
    with dbms.db_engine.connect() as conn:
        stmt = select(dbms.user.c.id)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            cursor.close()
            conn.close()
            return True
        conn.close()

    return False


def insert_song(playlist_info, subsonic_track,
                artist_spotify, track_spotify):
    """insert song into database"""
    with dbms.db_engine.connect() as conn:
        spotify_song_uuid = insert_spotify_song(
            conn, artist_spotify, track_spotify)
        if spotify_song_uuid is not None:
            if subsonic_track is None:
                insert_playlist_relation(
                    conn, None, None, playlist_info, spotify_song_uuid)
            else:
                track_id = None
                artist_id = None
                if "id" in subsonic_track:
                    track_id = subsonic_track["id"]
                if "artistId" in subsonic_track:
                    artist_id = subsonic_track["artistId"]
                insert_playlist_relation(
                    conn,
                    track_id,
                    artist_id,
                    playlist_info,
                    spotify_song_uuid)
            insert_playlist_type(
                conn, playlist_info)
            conn.commit()
        else:
            conn.rollback()
        conn.close()

def insert_playlist_type(conn, playlist_info):
    """insert playlist into database"""
    playlist_info_db = select_playlist_info_by_uri_sub_id(conn, playlist_info)
    if playlist_info_db is None:
        stmt = insert(
            dbms.playlist_info).values(
            uuid=str(
                uuid.uuid4().hex),
            spotify_playlist_uri=playlist_info["spotify_uri"],
            type=playlist_info["type"],
            subsonic_playlist_id=playlist_info["subsonic_playlist_id"]).prefix_with('OR IGNORE')
        stmt.compile()
        conn.execute(stmt)


def select_playlist_info_by_uri_sub_id(conn, playlist_info):
    """select spotify artists by uuid"""
    value = None
    stmt = select(
        dbms.playlist_info.c.uuid).where(
        dbms.playlist_info.c.spotify_playlist_uri == playlist_info["spotify_uri"],
        dbms.playlist_info.c.subsonic_playlist_id == playlist_info["subsonic_playlist_id"])
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value

def delete_playlist_relation_by_id(playlist_id: str):
    """delete playlist from database"""
    stmt = delete(dbms.subsonic_spotify_relation).where(
        dbms.subsonic_spotify_relation.c.subsonic_playlist_id == playlist_id)
    stmt = delete(dbms.playlist_info).where(
        dbms.playlist_info.c.subsonic_playlist_id == playlist_id)
    stmt.compile()
    with dbms.db_engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()
        conn.close()


def delete_song_relation(playlist_id: str, subsonic_track):
    """delete playlist from database"""

    if "id" in subsonic_track:
        stmt = None
        if "artistId" in subsonic_track:
            stmt = delete(dbms.subsonic_spotify_relation).where(
                dbms.subsonic_spotify_relation.c.subsonic_playlist_id == playlist_id,
                dbms.subsonic_spotify_relation.c.subsonic_song_id == subsonic_track["id"],
                dbms.subsonic_spotify_relation.c.subsonic_artist_id == subsonic_track["artistId"])
        else:
            stmt = delete(dbms.subsonic_spotify_relation).where(
                dbms.subsonic_spotify_relation.c.subsonic_playlist_id == playlist_id,
                dbms.subsonic_spotify_relation.c.subsonic_song_id == subsonic_track["id"])

        stmt.compile()
        with dbms.db_engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()
            conn.close()


def insert_playlist_relation(conn, subsonic_song_id,
                             subsonic_artist_id, playlist_info, spotify_song_uuid):
    """insert playlist into database"""
    stmt = insert(
        dbms.subsonic_spotify_relation).values(
        uuid=str(
            uuid.uuid4().hex),
        subsonic_song_id=subsonic_song_id,
        subsonic_artist_id=subsonic_artist_id,
        subsonic_playlist_id=playlist_info["subsonic_playlist_id"],
        subsonic_playlist_name=playlist_info["name"],
        spotify_song_uuid=spotify_song_uuid).prefix_with('OR IGNORE')
    stmt.compile()
    conn.execute(stmt)


def select_all_songs(conn_ext=None, missing_only=False, page=None,
                         limit=None, order=None, asc=None, search=None, song_uuid = None):
    """select playlists from database"""
    records = []
    stmt = None
    with conn_ext if conn_ext is not None else dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.subsonic_spotify_relation.c.uuid,
            dbms.subsonic_spotify_relation.c.subsonic_song_id,
            dbms.subsonic_spotify_relation.c.subsonic_artist_id,
            dbms.subsonic_spotify_relation.c.subsonic_playlist_id,
            dbms.subsonic_spotify_relation.c.subsonic_playlist_name,
            dbms.subsonic_spotify_relation.c.spotify_song_uuid,
            dbms.spotify_song.c.title.label('spotify_song_title'),
            dbms.spotify_song.c.spotify_uri.label('spotify_song_uri'),
            dbms.spotify_song.c.album_uuid.label('spotify_album_uuid'),
            dbms.spotify_album.c.spotify_uri.label('spotify_album_uri'),
            dbms.spotify_album.c.name.label('spotify_album_name'),
            func.group_concat(dbms.spotify_artist.c.name).label(
                'spotify_artist_names'),
            func.group_concat(dbms.spotify_artist.c.uuid).label(
                'spotify_artist_uuids'),
            dbms.spotify_song.c.tms_insert)
        stmt = stmt.join(
            dbms.spotify_song,
            dbms.subsonic_spotify_relation.c.spotify_song_uuid == dbms.spotify_song.c.uuid)
        stmt = stmt.join(
            dbms.spotify_album,
            dbms.spotify_song.c.album_uuid == dbms.spotify_album.c.uuid)
        stmt = stmt.join(
            dbms.spotify_song_artist_relation,
            dbms.spotify_song.c.uuid == dbms.spotify_song_artist_relation.c.song_uuid)
        stmt = stmt.join(
            dbms.spotify_artist,
            dbms.spotify_song_artist_relation.c.artist_uuid == dbms.spotify_artist.c.uuid)
        if missing_only:
            stmt = stmt.where(
                dbms.subsonic_spotify_relation.c.subsonic_song_id == None,
                dbms.subsonic_spotify_relation.c.subsonic_artist_id == None)
        if song_uuid is not None:
            stmt = stmt.where(
                dbms.spotify_song.c.uuid == song_uuid)
        if search is not None:
            stmt = stmt.filter(or_(dbms.spotify_song.c.title.ilike(f'%{search}%'),
                                   dbms.spotify_album.c.name.ilike(
                                       f'%{search}%'),
                                   dbms.spotify_artist.c.name.ilike(
                                       f'%{search}%'),
                                   dbms.subsonic_spotify_relation.c.subsonic_playlist_name.ilike(f'%{search}%')))

        stmt = limit_and_order_stmt(
            stmt, page=page, limit=limit, order=order, asc=asc)

        stmt = stmt.group_by(
            dbms.subsonic_spotify_relation.c.spotify_song_uuid,
            dbms.subsonic_spotify_relation.c.subsonic_playlist_id)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        cursor.close()

        count = count_songs(conn, missing_only=missing_only, search=search, song_uuid = song_uuid)
        if conn_ext is None:
            conn.close()

    return records, count


def count_songs(conn, missing_only=False, search=None, song_uuid=None):
    """select playlists from database"""
    count = 0

    query = """select count(*) from (select subsonic_spotify_relation.uuid from
    subsonic_spotify_relation
    join spotify_song
    on subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid
    join spotify_album
    on spotify_song.album_uuid = spotify_album.uuid
    join spotify_song_artist_relation
    on spotify_song.uuid = spotify_song_artist_relation.song_uuid
    join spotify_artist
    on spotify_song_artist_relation.artist_uuid = spotify_artist.uuid """
    where = ""
    if missing_only:
        where = where + """ subsonic_spotify_relation.subsonic_song_id is null
        and subsonic_spotify_relation.subsonic_artist_id is null """
    if search is not None:
        if where != "":
            where = where + " and "
        where = where + """ Lower(spotify_song.title) LIKE Lower('""" + search + """')
            OR Lower(spotify_album.name) LIKE Lower('""" + search + """')
            OR Lower(spotify_artist.name) LIKE Lower('""" + search + """')
            OR Lower(subsonic_spotify_relation.subsonic_playlist_name) LIKE
            Lower('""" + search + """') """
    if song_uuid is not None:
        if where != "":
            where = where + " and "
        where = where + " spotify_song.uuid = '" + song_uuid + "' "

    if where != "":
        query = query + " where " + where

    query = query + """group by subsonic_spotify_relation.spotify_song_uuid,
    subsonic_spotify_relation.subsonic_playlist_id);"""

    count = conn.execute(text(query)).scalar()

    return count


def select_spotify_artists_by_uuid(conn, c_uuid):
    """select spotify artists by uuid"""
    value = None
    stmt = select(
        dbms.spotify_artist.c.uuid,
        dbms.spotify_artist.c.name,
        dbms.spotify_artist.c.spotify_uri).where(
        dbms.spotify_artist.c.uuid == c_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def insert_spotify_song(conn, artist_spotify, track_spotify):
    """insert spotify song"""
    song_db = select_spotify_song_by_uri(conn, track_spotify["uri"])
    song_uuid = None
    if song_db is None:
        song_uuid = str(uuid.uuid4().hex)
        album_uuid = insert_spotify_album(conn, track_spotify["album"])
        stmt = insert(
            dbms.spotify_song).values(
            uuid=song_uuid,
            album_uuid=album_uuid,
            title=track_spotify["name"],
            spotify_uri=track_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
    elif song_db is not None and song_db.uuid is not None:
        song_uuid = song_db.uuid

    if song_uuid is not None:
        artist_uuid = insert_spotify_artist(conn, artist_spotify)
        if artist_uuid is not None:
            insert_spotify_song_artist_relation(
                conn, song_uuid, artist_uuid)
            return song_uuid
    return song_uuid


def select_spotify_song_by_uri(conn, spotify_uri: str):
    """select spotify song by uri"""
    value = None
    stmt = select(
        dbms.spotify_song.c.uuid,
        dbms.spotify_song.c.spotify_uri,
        dbms.spotify_song.c.title).where(
        dbms.spotify_song.c.spotify_uri == spotify_uri)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value

def select_spotify_song_by_uuid(conn, uuid: str):
    """select spotify song by uri"""
    value = None
    stmt = select(
        dbms.spotify_song.c.uuid,
        dbms.spotify_song.c.spotify_uri,
        dbms.spotify_song.c.title).where(
        dbms.spotify_song.c.uuid == uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def insert_spotify_artist(conn, artist_spotify):
    """insert spotify artist"""
    artist_db = select_spotify_artist_by_uri(conn, artist_spotify["uri"])
    if artist_db is None:
        artist_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            dbms.spotify_artist).values(
            uuid=artist_uuid,
            name=artist_spotify["name"],
            spotify_uri=artist_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
        return artist_uuid
    if artist_db is not None and artist_db.uuid is not None:
        return artist_db.uuid
    return None


def insert_spotify_album(conn, album_spotify):
    """insert spotify artist"""
    album_uuid = select_spotify_album_by_uri(conn, album_spotify["uri"])
    if album_uuid is None:
        album_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            dbms.spotify_album).values(
            uuid=album_uuid,
            name=album_spotify["name"],
            spotify_uri=album_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
        return album_uuid
    if album_uuid is not None and album_uuid.uuid is not None:
        return album_uuid.uuid
    return None


def select_spotify_album_by_uri(conn, spotify_uri: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.spotify_album.c.uuid,
        dbms.spotify_album.c.name,
        dbms.spotify_album.c.spotify_uri).where(
        dbms.spotify_album.c.spotify_uri == spotify_uri)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def select_spotify_album_by_uuid(conn, uuid: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.spotify_album.c.uuid,
        dbms.spotify_album.c.name,
        dbms.spotify_album.c.spotify_uri).where(
        dbms.spotify_album.c.uuid == uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def select_spotify_artist_by_uri(conn, spotify_uri: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.spotify_artist.c.uuid,
        dbms.spotify_artist.c.name,
        dbms.spotify_artist.c.spotify_uri).where(
        dbms.spotify_artist.c.spotify_uri == spotify_uri)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def get_artist_and_songs(uuid: str, page=None,
                         limit=None, order=None, asc=None):
    songs = None
    artist = None
    count = 0
    with dbms.db_engine.connect() as conn:
        artist = select_spotify_artist_by_uuid(conn, uuid)
        songs = select_songs_by_artist_uuid(
            conn, uuid, page=page, limit=limit, order=order, asc=asc)
        count = select_count_songs_by_artist_uuid(conn, uuid)
        conn.close()
    return artist, songs, count


def get_album_and_songs(uuid: str, page=None,
                        limit=None, order=None, asc=None):
    songs = None
    artist = None
    count = 0
    with dbms.db_engine.connect() as conn:
        artist = select_spotify_album_by_uuid(conn, uuid)
        songs = select_songs_by_album_uuid(
            conn, uuid, page=page, limit=limit, order=order, asc=asc)
        count = select_count_songs_by_album_uuid(conn, uuid)
        conn.close()
    return artist, songs, count

def get_song_and_playlists(uuid: str, page=None,
                        limit=None, order=None, asc=None):
    songs = None
    artist = None
    count = 0
    with dbms.db_engine.connect() as conn:
        song = select_spotify_song_by_uuid(conn, uuid)
        playlists, count = select_all_songs(
            conn_ext=conn, page=page, limit=limit, order=order, asc=asc, song_uuid=uuid)
        conn.close()
    return song, playlists, count


def select_spotify_artist_by_uuid(conn, uuid: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.spotify_artist.c.uuid,
        dbms.spotify_artist.c.name,
        dbms.spotify_artist.c.spotify_uri).where(
        dbms.spotify_artist.c.uuid == uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def select_config_by_name(conn, name: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.config_table.c.value).where(
        dbms.config_table.c.name == name)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def insert_or_update_config(conn, name: str, value: str):
    """select spotify artist by uri"""
    fconfig = select_config_by_name(conn, name)
    stmt = None
    if fconfig is None:
        stmt = insert(
            dbms.config_table).values(
            name=name,
            value=value)
    else:
        stmt = update(
            dbms.config_table).where(
            dbms.config_table.c.name == name).values(
            value=value)
    stmt.compile()
    conn.execute(stmt)


def insert_spotify_song_artist_relation(
        conn, song_uuid: int, artist_uuid: int):
    """insert spotify song artist relation"""
    if select_spotify_song_artist_relation(
            conn, song_uuid, artist_uuid) is None:
        stmt = insert(
            dbms.spotify_song_artist_relation).values(
            song_uuid=song_uuid,
            artist_uuid=artist_uuid)
        stmt.compile()
        conn.execute(stmt)
        conn.commit()


def select_spotify_song_artist_relation(
        conn, song_uuid: int, artist_uuid: int):
    """select spotify song artist relation"""
    value = None
    stmt = select(
        dbms.spotify_song_artist_relation.c.song_uuid,
        dbms.spotify_song_artist_relation.c.artist_uuid).where(
        dbms.spotify_song_artist_relation.c.song_uuid == song_uuid,
        dbms.spotify_song_artist_relation.c.artist_uuid == artist_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def select_spotify_song_artists_relation_by_song_uuid(
        conn, song_uuid: int):
    """select spotify song artist relation by song uuid"""
    stmt = select(dbms.spotify_song_artist_relation.c.artist_uuid).where(
        dbms.spotify_song_artist_relation.c.song_uuid == song_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    cursor.close()

    return records


def limit_and_order_stmt(stmt, page=None, limit=None, order=None, asc=None):
    if page is not None and limit is not None:
        stmt = stmt.limit(limit).offset(page * limit)
    order_by = []
    if order is not None:
        if asc:
            stmt = stmt.order_by(collate(text(order), 'NOCASE'))
        else:
            stmt = stmt.order_by(desc(collate(text(order), 'NOCASE')))
    return stmt


def select_songs_by_artist_uuid(
        conn, artist_uuid: int, page=None, limit=None, order=None, asc=None):
    """select spotify song artist relation by artist uuid"""
    stmt = select(
        dbms.spotify_song_artist_relation.c.song_uuid,
        dbms.spotify_song.c.uuid,
        dbms.spotify_song.c.spotify_uri,
        dbms.spotify_song.c.title,
        dbms.spotify_song.c.album_uuid,
        dbms.spotify_album.c.name.label('album_name'),
        dbms.subsonic_spotify_relation.c.subsonic_song_id,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_name,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_id,
        func.group_concat(dbms.spotify_artist.c.name).label(
            'spotify_artist_names'),
        func.group_concat(dbms.spotify_artist.c.uuid).label('spotify_artist_uuids')).join(
        dbms.subsonic_spotify_relation, dbms.subsonic_spotify_relation.c.spotify_song_uuid == dbms.spotify_song.c.uuid).join(
        dbms.spotify_album, dbms.spotify_song.c.album_uuid == dbms.spotify_album.c.uuid).join(
        dbms.spotify_artist, dbms.spotify_artist.c.uuid == dbms.spotify_song_artist_relation.c.artist_uuid).join(
        dbms.spotify_song_artist_relation, dbms.spotify_song.c.uuid == dbms.spotify_song_artist_relation.c.song_uuid).where(
        dbms.spotify_song_artist_relation.c.artist_uuid == artist_uuid)

    stmt = limit_and_order_stmt(
        stmt,
        page=page,
        limit=limit,
        order=order,
        asc=asc)

    stmt = stmt.group_by(
        dbms.subsonic_spotify_relation.c.spotify_song_uuid,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_id)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    cursor.close()

    return records


def select_count_songs_by_artist_uuid(conn, artist_uuid):
    query = """select count(*) from (SELECT spotify_song_artist_relation.song_uuid, spotify_song.uuid, spotify_song.spotify_uri, spotify_song.title, spotify_song.album_uuid, spotify_album.name AS album_name, subsonic_spotify_relation.subsonic_song_id, subsonic_spotify_relation.subsonic_playlist_name, subsonic_spotify_relation.subsonic_playlist_id, group_concat(spotify_artist.name) AS spotify_artist_names, group_concat(spotify_artist.uuid) AS spotify_artist_uuids FROM spotify_song JOIN subsonic_spotify_relation ON subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid JOIN spotify_album ON spotify_song.album_uuid = spotify_album.uuid JOIN spotify_artist ON spotify_artist.uuid = spotify_song_artist_relation.artist_uuid JOIN spotify_song_artist_relation ON spotify_song.uuid = spotify_song_artist_relation.song_uuid WHERE spotify_song_artist_relation.artist_uuid = '""" + artist_uuid + """'  GROUP BY subsonic_spotify_relation.spotify_song_uuid, subsonic_spotify_relation.subsonic_playlist_id)"""

    count = conn.execute(text(query)).scalar()
    conn.close()

    return count


def select_songs_by_album_uuid(
        conn, album_uuid: int, page=None, limit=None, order=None, asc=None):
    """select spotify song artist relation by artist uuid"""
    stmt = select(
        dbms.spotify_song_artist_relation.c.song_uuid,
        dbms.spotify_song.c.uuid,
        dbms.spotify_song.c.spotify_uri,
        dbms.spotify_song.c.title,
        dbms.spotify_song.c.album_uuid,
        dbms.spotify_album.c.name.label('album_name'),
        dbms.subsonic_spotify_relation.c.subsonic_song_id,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_name,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_id,
        func.group_concat(dbms.spotify_artist.c.name).label(
            'spotify_artist_names'),
        func.group_concat(dbms.spotify_artist.c.uuid).label('spotify_artist_uuids')).join(
        dbms.subsonic_spotify_relation, dbms.subsonic_spotify_relation.c.spotify_song_uuid == dbms.spotify_song.c.uuid).join(
        dbms.spotify_album, dbms.spotify_song.c.album_uuid == dbms.spotify_album.c.uuid).join(
        dbms.spotify_song_artist_relation, dbms.spotify_song.c.uuid == dbms.spotify_song_artist_relation.c.song_uuid).join(
        dbms.spotify_artist, dbms.spotify_artist.c.uuid == dbms.spotify_song_artist_relation.c.artist_uuid).where(
        dbms.spotify_song.c.album_uuid == album_uuid)

    stmt = limit_and_order_stmt(
        stmt,
        page=page,
        limit=limit,
        order=order,
        asc=asc)

    stmt = stmt.group_by(
        dbms.subsonic_spotify_relation.c.spotify_song_uuid,
        dbms.subsonic_spotify_relation.c.subsonic_playlist_id)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    cursor.close()

    return records


def select_count_songs_by_album_uuid(conn, album_uuid):
    query = """select count(*) from (SELECT spotify_song_artist_relation.song_uuid, spotify_song.uuid, spotify_song.spotify_uri, spotify_song.title, spotify_song.album_uuid, spotify_album.name AS album_name, subsonic_spotify_relation.subsonic_song_id, subsonic_spotify_relation.subsonic_playlist_name, subsonic_spotify_relation.subsonic_playlist_id, group_concat(spotify_artist.name) AS spotify_artist_names, group_concat(spotify_artist.uuid) AS spotify_artist_uuids FROM spotify_song JOIN subsonic_spotify_relation ON subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid JOIN spotify_album ON spotify_song.album_uuid = spotify_album.uuid JOIN spotify_song_artist_relation ON spotify_song.uuid = spotify_song_artist_relation.song_uuid JOIN spotify_artist ON spotify_artist.uuid = spotify_song_artist_relation.artist_uuid WHERE spotify_song.album_uuid = '""" + album_uuid + """' GROUP BY subsonic_spotify_relation.spotify_song_uuid, subsonic_spotify_relation.subsonic_playlist_id)"""

    count = conn.execute(text(query)).scalar()
    conn.close()

    return count


def select_all_playlists(page=None, limit=None, order=None, asc=None):
    """select playlists from database"""
    records = []
    stmt = None
    with dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.subsonic_spotify_relation.c.subsonic_playlist_name,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.type).join(
            dbms.subsonic_spotify_relation,
            dbms.playlist_info.c.subsonic_playlist_id == dbms.subsonic_spotify_relation.c.subsonic_playlist_id)
        

        stmt = limit_and_order_stmt(
            stmt, page=page, limit=limit, order=order, asc=asc)

        stmt = stmt.group_by(
            dbms.playlist_info.c.subsonic_playlist_id)

            
        stmt.compile()
        cursor = conn.execute(stmt)
        rows = cursor.fetchall()
        for row in rows:
            total, matched, missing = get_playlist_counts(conn, row.subsonic_playlist_id)
            record = {}
            record["subsonic_playlist_id"] = row.subsonic_playlist_id
            record["subsonic_playlist_name"] = row.subsonic_playlist_name
            record["type"] = row.type
            record["type_desc"] = string.capwords(row.type.replace("_"," "))
            record["spotify_playlist_uri"] = "" if row.spotify_playlist_uri is None else str(row.spotify_playlist_uri).replace(":","/").replace("spotify","https://open.spotify.com")
            record["total"] = total
            record["matched"] = matched
            record["missing"] = missing
            record["percentage"] = int((matched/total)*100)

            records.append(record)


        cursor.close()

        count = count_playlists(conn)
        conn.close()

    return records, count


def count_playlists(conn):
    """select playlists from database"""
    count = 0

    query = """select count(*) from (SELECT playlist_info.subsonic_playlist_id, subsonic_spotify_relation.subsonic_playlist_name, playlist_info.spotify_playlist_uri, playlist_info.type FROM playlist_info JOIN subsonic_spotify_relation ON playlist_info.subsonic_playlist_id = subsonic_spotify_relation.subsonic_playlist_id GROUP BY playlist_info.subsonic_playlist_id);"""

    count = conn.execute(text(query)).scalar()

    return count


def get_playlist_counts(conn, subsonic_playlist_id):
    """select count songs from database"""
    total = 0
    missing = 0
    matched = 0
    
    total_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.subsonic_playlist_id = '" + subsonic_playlist_id + "');"
    matched_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.subsonic_playlist_id = '" + subsonic_playlist_id + "' and subsonic_spotify_relation.subsonic_song_id is not null);"
    missing_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.subsonic_playlist_id = '" + subsonic_playlist_id + "' and subsonic_spotify_relation.subsonic_song_id is null);"

    total = conn.execute(text(total_query)).scalar()
    matched = conn.execute(text(matched_query)).scalar()
    missing = conn.execute(text(missing_query)).scalar()

    return total, matched, missing


dbms = Database(SQLITE, dbname=Config.SQLALCHEMY_DATABASE_NAME)
create_db_tables()
