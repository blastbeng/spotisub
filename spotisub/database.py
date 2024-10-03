"""Spotisub database"""
import uuid
import string
import logging
import threading
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

VERSION = "0.3.2-alpha2"
VERSIONS = ["0.3.0-alpha-01", "0.3.1", "0.3.2-alpha2"]

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
                                          'spotify_song_uuid', String(36), nullable=True),
                                      Column(
                                          'playlist_info_uuid', String(36), nullable=False),
                                      Column(
                                          'ignored', Integer, nullable=False, default=0)
                                      )

    playlist_info = Table(PLAYLIST_INFO, metadata,
                                      Column(
                                          'uuid', String(36), primary_key=True, nullable=False),
                                      Column(
                                          'subsonic_playlist_id', String(36), unique=True, nullable=True),
                                      Column(
                                          'subsonic_playlist_name', String(500), unique=True, nullable=False),
                                      Column(
                                          'spotify_playlist_uri', String(36), nullable=True),
                                      Column(
                                          'import_arg', String(500), nullable=False),
                                      Column(
                                          'type', String(36), nullable=False),
                                      Column(
                                          'ignored', Integer, nullable=False, default=0)
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
                             nullable=False),
                        Column(
                             'ignored', Integer, nullable=False, default=0)
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
                               nullable=False),
                        Column(
                             'ignored', Integer, nullable=False, default=0)
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
                              nullable=False),
                        Column(
                             'ignored', Integer, nullable=False, default=0)
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
            #backup_table(conn, SPOTIFY_SONG)
            #backup_table(conn, SPOTIFY_ALBUM)
            #backup_table(conn, SPOTIFY_ARTIST)
            #backup_table(conn, SPOTIFY_SONG_ARTIST_RELATION)
            #backup_table(conn, SUBSONIC_SPOTIFY_RELATION)
            #backup_table(conn, PLAYLIST_INFO)
            drop_table(conn, SPOTIFY_SONG)
            drop_table(conn, SPOTIFY_ALBUM)
            drop_table(conn, SPOTIFY_ARTIST)
            drop_table(conn, SPOTIFY_SONG_ARTIST_RELATION)
            drop_table(conn, SUBSONIC_SPOTIFY_RELATION)
            drop_table(conn, PLAYLIST_INFO)
            upgraded = True
        if fconfig is None or fconfig.value != VERSION:
            insert_or_update_config(conn, 'VERSION', VERSION)
            conn.commit()
            upgraded = True
        conn.close()
    if upgraded:
        dbms.metadata.create_all(dbms.db_engine)
        #with dbms.db_engine.connect() as conn:
        #    clone_table_from_bak(conn, SPOTIFY_SONG)
        #    clone_table_from_bak(conn, SPOTIFY_ALBUM)
        #    clone_table_from_bak(conn, SPOTIFY_ARTIST)
        #    clone_table_from_bak(conn, SPOTIFY_SONG_ARTIST_RELATION)
        #    clone_table_from_bak(conn, SUBSONIC_SPOTIFY_RELATION)
        #    clone_table_from_bak(conn, PLAYLIST_INFO)
        #    conn.commit()
        #    conn.close()


def drop_table(conn, table_name):
    """Drops single table"""
    query = "DROP TABLE IF EXISTS " + table_name
    conn.execute(text(query))

def backup_table(conn, table_name):
    """Backup single table"""
    bak_name = table_name + "_bak"
    query_drop = "DROP TABLE IF EXISTS " + bak_name
    conn.execute(text(query_drop))
    if check_table(conn, table_name) == 1:
        query_alter = "ALTER TABLE " + table_name + " RENAME TO " + bak_name
        conn.execute(text(query_alter))

def check_table(conn, table_name):
    query_check = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='" + table_name + "'"
    count = conn.execute(text(query_check)).scalar()
    return count

def clone_table_from_bak(conn, table_name):
    """Clone table from bak"""
    if check_table(conn, table_name) == 1:
        bak_name = table_name + "_bak"
        if check_table(conn, bak_name) == 1:
            query = "INSERT INTO " + table_name + " SELECT * FROM " + bak_name
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
    """Create empty playlist into database"""
    return_dict = None
    with dbms.db_engine.connect() as conn:
        pl_info = insert_playlist_type(
                conn, playlist_info)
        if pl_info is not None:
            return_dict = insert_spotify_song(
                conn, artist_spotify, track_spotify)
            if return_dict["song_uuid"] is not None:
                pl_relation = None
                if subsonic_track is None:
                    pl_relation = insert_playlist_relation(
                        conn, None, None, playlist_info, return_dict["song_uuid"], pl_info.uuid)
                else:
                    track_id = None
                    artist_id = None
                    if "id" in subsonic_track:
                        track_id = subsonic_track["id"]
                    if "artistId" in subsonic_track:
                        artist_id = subsonic_track["artistId"]
                    pl_relation = insert_playlist_relation(
                        conn,
                        track_id,
                        artist_id,
                        playlist_info,
                        return_dict["song_uuid"],
                        pl_info.uuid)
            
                if pl_relation is not None:
                    return_dict["uuid"] = pl_relation.uuid
                    return_dict["ignored_pl"] = (pl_relation.ignored==1)
                    return_dict["ignored_whole_pl"] = (pl_info.ignored==1)
            conn.commit()
        else:
            conn.rollback()
        conn.close()
        return return_dict

def create_playlist(playlist_info):
    """Create empty playlist into database"""
    pl_info = None
    with dbms.db_engine.connect() as conn:
        pl_info = insert_playlist_type(
                conn, playlist_info)
        if pl_info is not None:
            conn.commit()
        else:
            conn.rollback()
        conn.close()
    return pl_info

def insert_playlist_type(conn, playlist_info):
    """insert playlist into database"""
    playlist_info_db = None
    uuid_input=None
    if "uuid" in playlist_info and playlist_info["uuid"] is not None:
        uuid_input = playlist_info["uuid"]
        playlist_info_db = select_playlist_info_by_uuid(uuid_input)
        if playlist_info_db is None:
            playlist_info_db = select_playlist_info_by_name(playlist_info["name"])
    else:
        uuid_input = str(uuid.uuid4().hex)
        playlist_info_db = select_playlist_info_by_name(playlist_info["name"])
    subsonic_playlist_id_info = playlist_info["subsonic_playlist_id"] if "subsonic_playlist_id" in playlist_info else None
    if playlist_info_db is None:
        stmt = insert(
            dbms.playlist_info).values(
            uuid=uuid_input,
            spotify_playlist_uri=playlist_info["spotify_uri"],
            type=playlist_info["type"],
            subsonic_playlist_id=subsonic_playlist_id_info,
            subsonic_playlist_name=playlist_info["name"],
            import_arg=playlist_info["import_arg"])
        stmt.compile()
        conn.execute(stmt)
        logging.info('(%s) Initializing empty playlist %s, to trigger the manual population use the Rescan function.', 
            str(threading.current_thread().ident), playlist_info["name"])
        return select_playlist_info_by_uuid(uuid_input)
    else:
        stmt = update(
            dbms.playlist_info).where(
            dbms.playlist_info.c.uuid == playlist_info_db.uuid).values(
            spotify_playlist_uri=playlist_info["spotify_uri"],
            type=playlist_info["type"],
            subsonic_playlist_id=subsonic_playlist_id_info,
            subsonic_playlist_name=playlist_info["name"])
        stmt.compile()
        conn.execute(stmt)
        return select_playlist_info_by_uuid(uuid_input)



def select_ignore_playlist_by_name(name):
    """select spotify artists by uuid"""
    value = None
    with dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.playlist_info.c.ignored).where(
            dbms.playlist_info.c.subsonic_playlist_name == name)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row.ignored
        cursor.close()

    return value

def select_playlist_info_by_name(name):
    """select spotify artists by uuid"""
    with dbms.db_engine.connect() as conn:
        value = None
        stmt = select(
            dbms.playlist_info.c.uuid,
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.ignored,
            dbms.playlist_info.c.type,
            dbms.playlist_info.c.import_arg).where(
            dbms.playlist_info.c.subsonic_playlist_name == name)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row
        cursor.close()
        conn.close()

    return value

def select_playlist_info_by_arg(arg):
    """select spotify artists by uuid"""
    with dbms.db_engine.connect() as conn:
        value = None
        stmt = select(
            dbms.playlist_info.c.uuid,
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.ignored,
            dbms.playlist_info.c.type,
            dbms.playlist_info.c.import_arg).where(
            dbms.playlist_info.c.import_arg == arg)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row
        cursor.close()
        conn.close()

    return value

def select_playlist_info_by_uuid(uuid):
    """select spotify artists by uuid"""
    with dbms.db_engine.connect() as conn:
        value = None
        stmt = select(
            dbms.playlist_info.c.uuid,
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.ignored,
            dbms.playlist_info.c.type,
            dbms.playlist_info.c.import_arg).where(
            dbms.playlist_info.c.uuid == uuid)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row
        cursor.close()
        conn.close()
    return value

def delete_playlist_relation_by_id(playlist_id: str):
    """delete playlist from database"""
    with dbms.db_engine.connect() as conn:
        pl_info = select_playlist_info_by_subsonic_id(playlist_id, conn_ext=conn)
        if pl_info is not None:
            stmt1 = delete(dbms.subsonic_spotify_relation).where(
                dbms.subsonic_spotify_relation.c.playlist_info_uuid == pl_info)
            stmt1.compile()
            stmt2 = delete(dbms.playlist_info).where(
                dbms.playlist_info.c.subsonic_playlist_id == playlist_id)
            stmt2.compile()
            conn.execute(stmt1)
            conn.execute(stmt2)
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
                             subsonic_artist_id, playlist_info, spotify_song_uuid, pl_info_uuid):
    """insert playlist into database"""
    old_relation = select_playlist_relation(conn, subsonic_song_id,
                            subsonic_artist_id, spotify_song_uuid, pl_info_uuid)
    if old_relation is None:
        new_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            dbms.subsonic_spotify_relation).values(
            uuid=new_uuid,
            subsonic_song_id=subsonic_song_id,
            subsonic_artist_id=subsonic_artist_id,
            spotify_song_uuid=spotify_song_uuid,
            playlist_info_uuid=pl_info_uuid)
        stmt.compile()
        conn.execute(stmt)
        return select_playlist_relation_by_uuid(new_uuid, conn_ext=conn)
    else:
        stmt = update(
            dbms.subsonic_spotify_relation).where(
            dbms.subsonic_spotify_relation.c.uuid == old_relation.uuid,
            dbms.subsonic_spotify_relation.c.playlist_info_uuid == pl_info_uuid).values(
            subsonic_song_id=subsonic_song_id,
            subsonic_artist_id=subsonic_artist_id,
            spotify_song_uuid=spotify_song_uuid)
        stmt.compile()
        conn.execute(stmt)
        return select_playlist_relation_by_uuid(old_relation.uuid, conn_ext=conn)

def select_playlist_info_by_subsonic_id(subsonic_playlist_uuid, conn_ext=None):
    """select spotify artists by uuid"""
    value = None
    with conn_ext if conn_ext is not None else dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.playlist_info.c.uuid,
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.ignored,
            dbms.playlist_info.c.type).where(
            dbms.playlist_info.c.subsonic_playlist_id == subsonic_playlist_uuid)

        stmt = stmt.group_by(
            dbms.playlist_info.c.uuid)

        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row
        cursor.close()
        if conn_ext is None:
            conn.close()

    return value



def select_playlist_relation(conn, subsonic_song_id,
                             subsonic_artist_id, spotify_song_uuid, pl_info_uuid):
    value = None
    """select playlist relation"""
    stmt = select(dbms.subsonic_spotify_relation.c.uuid,
        dbms.subsonic_spotify_relation.c.subsonic_song_id,
        dbms.subsonic_spotify_relation.c.subsonic_artist_id,
        dbms.subsonic_spotify_relation.c.spotify_song_uuid,
        dbms.subsonic_spotify_relation.c.ignored).where(
        dbms.subsonic_spotify_relation.c.subsonic_song_id==subsonic_song_id,
        dbms.subsonic_spotify_relation.c.subsonic_artist_id==subsonic_artist_id,
        dbms.subsonic_spotify_relation.c.playlist_info_uuid==pl_info_uuid,
        dbms.subsonic_spotify_relation.c.spotify_song_uuid==spotify_song_uuid)
    stmt.compile()


    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
        value = row
    cursor.close()

    return value


def select_playlist_relation_by_uuid(uuid, conn_ext=None):
    value = None
    """select playlist relation"""
    with conn_ext if conn_ext is not None else dbms.db_engine.connect() as conn:
        stmt = select(dbms.subsonic_spotify_relation.c.uuid,
            dbms.subsonic_spotify_relation.c.subsonic_song_id,
            dbms.subsonic_spotify_relation.c.subsonic_artist_id,
            dbms.subsonic_spotify_relation.c.spotify_song_uuid,
            dbms.subsonic_spotify_relation.c.ignored).where(
            dbms.subsonic_spotify_relation.c.uuid==uuid)
        stmt.compile()


        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        for row in records:
            value = row
        cursor.close()
        if conn_ext is None:
            conn.close()

    return value

def select_all_songs(conn_ext=None, missing_only=False, page=None,
                         limit=None, order=None, asc=None, search=None, song_uuid=None, subsonic_song_id=None, playlist_uuid=None):
    """select playlists from database"""
    records = []
    stmt = None
    with conn_ext if conn_ext is not None else dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.playlist_info.c.uuid,
            dbms.subsonic_spotify_relation.c.subsonic_song_id,
            dbms.subsonic_spotify_relation.c.uuid.label('relation_uuid'),
            dbms.subsonic_spotify_relation.c.subsonic_artist_id,
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.subsonic_spotify_relation.c.spotify_song_uuid,
            dbms.playlist_info.c.type,
            dbms.playlist_info.c.ignored.label('ignored_whole_pl'),
            dbms.subsonic_spotify_relation.c.ignored.label('ignored_pl'),
            dbms.spotify_song.c.ignored,
            dbms.spotify_song.c.title.label('spotify_song_title'),
            dbms.spotify_song.c.spotify_uri.label('spotify_song_uri'),
            dbms.spotify_song.c.album_uuid.label('spotify_album_uuid'),
            dbms.spotify_album.c.spotify_uri.label('spotify_album_uri'),
            dbms.spotify_album.c.name.label('spotify_album_name'),
            dbms.spotify_album.c.ignored.label('spotify_album_ignored'),
            func.group_concat(dbms.spotify_artist.c.name).label(
                'spotify_artist_names'),
            func.group_concat(dbms.spotify_artist.c.uuid).label(
                'spotify_artist_uuids'),
            func.group_concat(dbms.spotify_artist.c.ignored).label(
                'spotify_artist_ignored'),
            dbms.spotify_song.c.tms_insert)
        stmt = stmt.join(
            dbms.playlist_info,
            dbms.playlist_info.c.uuid == dbms.subsonic_spotify_relation.c.playlist_info_uuid)
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
        if subsonic_song_id is not None:
            stmt = stmt.where(
                dbms.subsonic_spotify_relation.c.subsonic_song_id == subsonic_song_id)
        if playlist_uuid is not None:
            stmt = stmt.where(
                dbms.playlist_info.c.uuid == playlist_uuid)
        if search is not None:
            stmt = stmt.filter(or_(dbms.spotify_song.c.title.ilike(f'%{search}%'),
                                   dbms.spotify_album.c.name.ilike(
                                       f'%{search}%'),
                                   dbms.spotify_artist.c.name.ilike(
                                       f'%{search}%'),
                                   dbms.playlist_info.c.subsonic_playlist_name.ilike(f'%{search}%')))

        stmt = limit_and_order_stmt(
            stmt, page=page, limit=limit, order=order, asc=asc)

        stmt = stmt.group_by(
            dbms.subsonic_spotify_relation.c.spotify_song_uuid,
            dbms.playlist_info.c.subsonic_playlist_name)
        stmt.compile()
        cursor = conn.execute(stmt)
        records = cursor.fetchall()

        cursor.close()

        count = count_songs(conn, missing_only=missing_only, search=search, song_uuid = song_uuid, playlist_id = playlist_uuid)
        if conn_ext is None:
            conn.close()

    return records, count


def count_songs(conn, missing_only=False, search=None, song_uuid=None, playlist_id=None):
    """select playlists from database"""
    count = 0

    query = """SELECT COUNT(*) FROM
        (SELECT playlist_info.uuid,
            subsonic_spotify_relation.subsonic_song_id,
            subsonic_spotify_relation.subsonic_artist_id,
            playlist_info.subsonic_playlist_id,
            playlist_info.subsonic_playlist_name,
            subsonic_spotify_relation.spotify_song_uuid,
            spotify_song.title AS spotify_song_title,
            spotify_song.spotify_uri AS spotify_song_uri,
            spotify_song.album_uuid AS spotify_album_uuid,
            spotify_album.spotify_uri AS spotify_album_uri,
            spotify_album.name AS spotify_album_name,
            group_concat(spotify_artist.name) AS spotify_artist_names,
            group_concat(spotify_artist.uuid) AS spotify_artist_uuids,
            spotify_song.tms_insert FROM playlist_info
        JOIN subsonic_spotify_relation ON playlist_info.uuid = subsonic_spotify_relation.playlist_info_uuid
        JOIN spotify_song ON subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid
        JOIN spotify_album ON spotify_song.album_uuid = spotify_album.uuid
        JOIN spotify_song_artist_relation ON spotify_song.uuid = spotify_song_artist_relation.song_uuid
        JOIN spotify_artist ON spotify_song_artist_relation.artist_uuid = spotify_artist.uuid """
    where = ""
    if missing_only:
        where = where + """ subsonic_spotify_relation.subsonic_song_id is null
        and subsonic_spotify_relation.subsonic_artist_id is null """
    if search is not None:
        if where != "":
            where = where + " and "
        where = where + """ (lower(spotify_song.title) LIKE lower('""" + search + """')
            OR lower(spotify_album.name) LIKE lower('""" + search + """')
            OR lower(spotify_artist.name) LIKE lower('""" + search + """')
            OR lower(playlist_info.subsonic_playlist_name) LIKE lower('""" + search + """') """
        where = where + """ OR lower(spotify_song.title) LIKE lower('%""" + search + """')
            OR lower(spotify_album.name) LIKE lower('%""" + search + """')
            OR lower(spotify_artist.name) LIKE lower('%""" + search + """')
            OR lower(playlist_info.subsonic_playlist_name) LIKE lower('%""" + search + """') """
        where = where + """ OR lower(spotify_song.title) LIKE lower('""" + search + """%')
            OR lower(spotify_album.name) LIKE lower('""" + search + """%')
            OR lower(spotify_artist.name) LIKE lower('""" + search + """%')
            OR lower(playlist_info.subsonic_playlist_name) LIKE lower('""" + search + """%') """
        where = where + """ OR lower(spotify_song.title) LIKE lower('%""" + search + """%')
            OR lower(spotify_album.name) LIKE lower('%""" + search + """%')
            OR lower(spotify_artist.name) LIKE lower('%""" + search + """%')
            OR lower(playlist_info.subsonic_playlist_name) LIKE lower('%""" + search + """%')) """
    if song_uuid is not None:
        if where != "":
            where = where + " and "
        where = where + " spotify_song.uuid = '" + song_uuid + "' "
    if playlist_id is not None:
        if where != "":
            where = where + " and "
        where = where + " playlist_info.uuid = '" + playlist_id + "' "

    if where != "":
        query = query + " where " + where

    query = query + """group by subsonic_spotify_relation.spotify_song_uuid,
        playlist_info.subsonic_playlist_name);"""

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
    return_dict = {}
    return_dict["song_uuid"] = None
    return_dict["song_ignored"] = False
    return_dict["ignored_pl"] = False
    return_dict["album_ignored"] = False
    return_dict["artist_ignored"] = False
    song_db = select_spotify_song_by_uri(conn, track_spotify["uri"])
    song_uuid = None
    if song_db is None:
        song_uuid = str(uuid.uuid4().hex)
        album = None
        if "album" in track_spotify:
            album = insert_spotify_album(conn, track_spotify["album"])
        if album is not None:
            return_dict["album_ignored"] = (album.ignored==1)
            stmt = insert(
                dbms.spotify_song).values(
                uuid=song_uuid,
                album_uuid=album.uuid,
                title=track_spotify["name"],
                spotify_uri=track_spotify["uri"])
            stmt.compile()
            conn.execute(stmt)
            return_dict["song_uuid"] = song_uuid
            return_dict["song_ignored"] = False
    elif song_db is not None and song_db.uuid is not None:
        return_dict["song_uuid"] = song_db.uuid
        return_dict["song_ignored"] = (song_db.ignored==1)

    if return_dict["song_uuid"] is not None:
        artist = insert_spotify_artist(conn, artist_spotify)
        if artist is not None:
            return_dict["artist_ignored"] = (artist.ignored==1)
            insert_spotify_song_artist_relation(
                conn, return_dict["song_uuid"], artist.uuid)
    return return_dict


def select_spotify_song_by_uri(conn, spotify_uri: str):
    """select spotify song by uri"""
    value = None
    stmt = select(
        dbms.spotify_song.c.uuid,
        dbms.spotify_song.c.spotify_uri,
        dbms.spotify_song.c.title,
        dbms.spotify_song.c.ignored).where(
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
        dbms.spotify_song.c.title,
        dbms.spotify_song.c.ignored).where(
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
        return select_spotify_artist_by_uri(conn, artist_spotify["uri"])
    return artist_db


def insert_spotify_album(conn, album_spotify):
    """insert spotify artist"""
    album = select_spotify_album_by_uri(conn, album_spotify["uri"])
    if album is None:
        album_uuid = str(uuid.uuid4().hex)
        stmt = insert(
            dbms.spotify_album).values(
            uuid=album_uuid,
            name=album_spotify["name"],
            spotify_uri=album_spotify["uri"])
        stmt.compile()
        conn.execute(stmt)
        return select_spotify_album_by_uuid(conn, album_uuid)
    return album


def select_spotify_album_by_uri(conn, spotify_uri: str):
    """select spotify artist by uri"""
    value = None
    stmt = select(
        dbms.spotify_album.c.uuid,
        dbms.spotify_album.c.name,
        dbms.spotify_album.c.spotify_uri,
        dbms.spotify_album.c.ignored).where(
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
        dbms.spotify_album.c.spotify_uri,
        dbms.spotify_album.c.ignored).where(
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
        dbms.spotify_artist.c.spotify_uri,
        dbms.spotify_artist.c.ignored).where(
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
    album = None
    count = 0
    with dbms.db_engine.connect() as conn:
        album = select_spotify_album_by_uuid(conn, uuid)
        songs = select_songs_by_album_uuid(
            conn, uuid, page=page, limit=limit, order=order, asc=asc)
        count = select_count_songs_by_album_uuid(conn, uuid)
        conn.close()
    return album, songs, count

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
        dbms.spotify_artist.c.spotify_uri,
        dbms.spotify_artist.c.ignored).where(
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
        dbms.spotify_song.c.ignored,
        dbms.playlist_info.c.ignored.label('ignored_whole_pl'),
        dbms.spotify_album.c.name.label('album_name'),
        dbms.spotify_album.c.ignored.label('spotify_album_ignored'),
        dbms.subsonic_spotify_relation.c.uuid.label('subsonic_spotify_relation_uuid'),
        dbms.subsonic_spotify_relation.c.subsonic_song_id,
        dbms.playlist_info.c.subsonic_playlist_name,
        dbms.playlist_info.c.subsonic_playlist_id,
        dbms.playlist_info.c.uuid.label('playlist_info_uuid'),
        dbms.subsonic_spotify_relation.c.ignored.label('ignored_pl'),
        dbms.subsonic_spotify_relation.c.uuid.label('relation_uuid'),
        func.group_concat(dbms.spotify_artist.c.name).label(
            'spotify_artist_names'),
        func.group_concat(dbms.spotify_artist.c.uuid).label('spotify_artist_uuids'),
        func.group_concat(dbms.spotify_artist.c.ignored).label('spotify_artist_ignored')).join(
        dbms.subsonic_spotify_relation, dbms.subsonic_spotify_relation.c.spotify_song_uuid == dbms.spotify_song.c.uuid).join(
        dbms.spotify_album, dbms.spotify_song.c.album_uuid == dbms.spotify_album.c.uuid).join(
        dbms.spotify_artist, dbms.spotify_artist.c.uuid == dbms.spotify_song_artist_relation.c.artist_uuid).join(
        dbms.spotify_song_artist_relation, dbms.spotify_song.c.uuid == dbms.spotify_song_artist_relation.c.song_uuid).join(
        dbms.playlist_info,
        dbms.playlist_info.c.uuid == dbms.subsonic_spotify_relation.c.playlist_info_uuid).where(
        dbms.spotify_song_artist_relation.c.artist_uuid == artist_uuid)

    stmt = limit_and_order_stmt(
        stmt,
        page=page,
        limit=limit,
        order=order,
        asc=asc)

    stmt = stmt.group_by(
        dbms.subsonic_spotify_relation.c.spotify_song_uuid,
        dbms.playlist_info.c.subsonic_playlist_name)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    cursor.close()

    return records


def select_count_songs_by_artist_uuid(conn, artist_uuid):
    query = """select count(*) from (SELECT spotify_song_artist_relation.song_uuid, spotify_song.uuid, spotify_song.spotify_uri, 
    spotify_song.title, spotify_song.album_uuid, spotify_album.name AS album_name, subsonic_spotify_relation.subsonic_song_id, 
    playlist_info.subsonic_playlist_name, playlist_info.subsonic_playlist_id, group_concat(spotify_artist.name) 
    AS spotify_artist_names, group_concat(spotify_artist.uuid) AS spotify_artist_uuids 
    FROM spotify_song JOIN subsonic_spotify_relation ON subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid 
    JOIN playlist_info ON subsonic_spotify_relation.playlist_info_uuid = playlist_info.uuid 
    JOIN spotify_album ON spotify_song.album_uuid = spotify_album.uuid JOIN spotify_artist ON spotify_artist.uuid = spotify_song_artist_relation.artist_uuid 
    JOIN spotify_song_artist_relation ON spotify_song.uuid = spotify_song_artist_relation.song_uuid 
    WHERE spotify_song_artist_relation.artist_uuid = '""" + artist_uuid + """'  GROUP BY subsonic_spotify_relation.spotify_song_uuid, playlist_info.subsonic_playlist_name)"""

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
        dbms.spotify_song.c.ignored,
        dbms.playlist_info.c.ignored.label('ignored_whole_pl'),
        dbms.spotify_album.c.name.label('album_name'),
        dbms.spotify_album.c.ignored.label('spotify_album_ignored'),
        dbms.subsonic_spotify_relation.c.subsonic_song_id,
        dbms.subsonic_spotify_relation.c.ignored.label('ignored_pl'),
        dbms.playlist_info.c.subsonic_playlist_name,
        dbms.playlist_info.c.subsonic_playlist_id,
        dbms.playlist_info.c.uuid.label('playlist_info_uuid'),
        dbms.subsonic_spotify_relation.c.uuid.label('relation_uuid'),
        func.group_concat(dbms.spotify_artist.c.name).label(
            'spotify_artist_names'),
        func.group_concat(dbms.spotify_artist.c.uuid).label('spotify_artist_uuids'),
        func.group_concat(dbms.spotify_artist.c.ignored).label('spotify_artist_ignored')).join(
        dbms.subsonic_spotify_relation, dbms.subsonic_spotify_relation.c.spotify_song_uuid == dbms.spotify_song.c.uuid).join(
        dbms.spotify_album, dbms.spotify_song.c.album_uuid == dbms.spotify_album.c.uuid).join(
        dbms.spotify_song_artist_relation, dbms.spotify_song.c.uuid == dbms.spotify_song_artist_relation.c.song_uuid).join(
        dbms.spotify_artist, dbms.spotify_artist.c.uuid == dbms.spotify_song_artist_relation.c.artist_uuid).join(
        dbms.playlist_info,
        dbms.playlist_info.c.uuid == dbms.subsonic_spotify_relation.c.playlist_info_uuid).where(
        dbms.spotify_song.c.album_uuid == album_uuid)

    stmt = limit_and_order_stmt(
        stmt,
        page=page,
        limit=limit,
        order=order,
        asc=asc)

    stmt = stmt.group_by(
        dbms.subsonic_spotify_relation.c.spotify_song_uuid,
        dbms.playlist_info.c.subsonic_playlist_name)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    cursor.close()

    return records


def select_count_songs_by_album_uuid(conn, album_uuid):
    query = """select count(*) from (SELECT spotify_song_artist_relation.song_uuid, spotify_song.uuid, 
    spotify_song.spotify_uri, spotify_song.title, spotify_song.album_uuid, spotify_album.name AS album_name,
    subsonic_spotify_relation.subsonic_song_id, playlist_info.subsonic_playlist_name, playlist_info.subsonic_playlist_id,
     group_concat(spotify_artist.name) AS spotify_artist_names, group_concat(spotify_artist.uuid) AS spotify_artist_uuids 
     FROM spotify_song 
     JOIN subsonic_spotify_relation ON subsonic_spotify_relation.spotify_song_uuid = spotify_song.uuid 
     JOIN playlist_info ON subsonic_spotify_relation.playlist_info_uuid = playlist_info.uuid 
     JOIN spotify_album ON spotify_song.album_uuid = spotify_album.uuid 
     JOIN spotify_song_artist_relation ON spotify_song.uuid = spotify_song_artist_relation.song_uuid 
     JOIN spotify_artist ON spotify_artist.uuid = spotify_song_artist_relation.artist_uuid 
     WHERE spotify_song.album_uuid = '""" + album_uuid + """' GROUP BY subsonic_spotify_relation.spotify_song_uuid, playlist_info.subsonic_playlist_name)"""

    count = conn.execute(text(query)).scalar()
    conn.close()

    return count


def select_all_playlists(conn_ext=None, page=None, limit=None, order=None, asc=None):
    """select playlists from database"""
    records = []
    stmt = None
    with conn_ext if conn_ext is not None else dbms.db_engine.connect() as conn:
        stmt = select(
            dbms.playlist_info.c.subsonic_playlist_id,
            dbms.playlist_info.c.subsonic_playlist_name,
            dbms.playlist_info.c.uuid,
            dbms.playlist_info.c.spotify_playlist_uri,
            dbms.playlist_info.c.type,
            dbms.playlist_info.c.ignored,
            dbms.playlist_info.c.import_arg)
        

        stmt = limit_and_order_stmt(
            stmt, page=page, limit=limit, order=order, asc=asc)

        stmt = stmt.group_by(
            dbms.playlist_info.c.subsonic_playlist_name)

            
        stmt.compile()
        cursor = conn.execute(stmt)
        rows = cursor.fetchall()
        for row in rows:
            total, matched, missing = get_playlist_counts(conn, row.uuid)
            record = {}
            record["uuid"] = row.uuid
            record["subsonic_playlist_id"] = row.subsonic_playlist_id
            record["subsonic_playlist_name"] = row.subsonic_playlist_name
            record["ignored_info"] = row.ignored
            record["import_arg"] = row.import_arg
            record["type"] = row.type
            record["type_desc"] = string.capwords(row.type.replace("_"," "))
            record["spotify_playlist_link"] = "" if row.spotify_playlist_uri is None else str(row.spotify_playlist_uri).replace(":","/").replace("spotify","https://open.spotify.com")
            record["spotify_playlist_uri"] = "" if row.spotify_playlist_uri is None else row.spotify_playlist_uri
            record["total"] = total
            record["matched"] = matched
            record["missing"] = missing
            record["percentage"] = int((matched/total)*100) if total != 0 else 0

            records.append(record)


        cursor.close()

        count = count_playlists(conn)
        if conn_ext is None:
            conn.close()

    return records, count


def count_playlists(conn):
    """select playlists from database"""
    count = 0

    query = """select count(*) from (SELECT playlist_info.subsonic_playlist_id, playlist_info.subsonic_playlist_name, playlist_info.spotify_playlist_uri, playlist_info.type FROM playlist_info GROUP BY playlist_info.subsonic_playlist_name);"""

    count = conn.execute(text(query)).scalar()

    return count


def get_playlist_counts(conn, pl_info_uuid):
    """select count songs from database"""
    total = 0
    missing = 0
    matched = 0
    
    total_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.playlist_info_uuid = '" + pl_info_uuid + "' and subsonic_spotify_relation.spotify_song_uuid is not null);"
    matched_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.playlist_info_uuid = '" + pl_info_uuid + "' and subsonic_spotify_relation.subsonic_song_id is not null and subsonic_spotify_relation.spotify_song_uuid is not null);"
    missing_query = "SELECT COUNT(*) FROM (SELECT subsonic_spotify_relation.uuid from subsonic_spotify_relation where subsonic_spotify_relation.playlist_info_uuid = '" + pl_info_uuid + "' and subsonic_spotify_relation.subsonic_song_id is null and subsonic_spotify_relation.spotify_song_uuid is not null);"

    total = conn.execute(text(total_query)).scalar()
    matched = conn.execute(text(matched_query)).scalar()
    missing = conn.execute(text(missing_query)).scalar()

    return total, matched, missing


def update_ignored_song(uuid, value):
    with dbms.db_engine.connect() as conn:
        stmt = update(
                dbms.spotify_song).where(
                dbms.spotify_song.c.uuid == uuid).values(
                ignored=value)
        stmt.compile()
        conn.execute(stmt)
        conn.commit()
        conn.close()


def update_ignored_artist(uuid, value):
    with dbms.db_engine.connect() as conn:
        stmt = update(
                dbms.spotify_artist).where(
                dbms.spotify_artist.c.uuid == uuid).values(
                ignored=value)

        stmt.compile()
        conn.execute(stmt)
        conn.commit()
        conn.close()

def update_ignored_album(uuid, value):
    with dbms.db_engine.connect() as conn:
        stmt = update(
                dbms.spotify_album).where(
                dbms.spotify_album.c.uuid == uuid).values(
                ignored=value)

        stmt.compile()
        conn.execute(stmt)
        conn.commit()
        conn.close()

def update_ignored_song_pl(uuid, value):
    with dbms.db_engine.connect() as conn:
        stmt = update(
                dbms.subsonic_spotify_relation).where(
                dbms.subsonic_spotify_relation.c.uuid == uuid).values(
                ignored=value)

        stmt.compile()
        conn.execute(stmt)
        conn.commit()
        conn.close()

def update_ignored_playlist(uuid, value):
    with dbms.db_engine.connect() as conn:
        stmt = update(
                dbms.playlist_info).where(
                dbms.playlist_info.c.uuid == uuid).values(
                ignored=value)

        stmt.compile()
        conn.execute(stmt)
        conn.commit()
        conn.close()

dbms = Database(SQLITE, dbname=Config.SQLALCHEMY_DATABASE_NAME)
create_db_tables()
