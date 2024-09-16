import os
import sys
import uuid
import logging
from sqlalchemy import create_engine, insert, select, update, delete, Table, Column, Integer, String, DateTime, MetaData
from sqlalchemy.sql import func

SQLITE                                   = 'sqlite'
SUBSONIC_PLAYLIST                        = 'subsonic_playlist'
SUBSONIC_SONG                            = 'subsonic_song'
SUBSONIC_ARTIST                          = 'subsonic_artist'
SUBSONIC_SONG_ARTIST_RELATION            = 'subsonic_song_artist_relation'
SUBSONIC_SPOTIFY_RELATION                = 'subsonic_spotify_relation'
SPOTIFY_SONG                             = 'spotify_song'
SPOTIFY_ARTIST                           = 'spotify_artist'
SPOTIFY_SONG_ARTIST_RELATION             = 'spotify_song_artist_relation'

class Database:
  DB_ENGINE = {
      SQLITE: 'sqlite:///cache/{DB}'
  }

  # Main DB Connection Ref Obj
  db_engine = None
  def __init__(self, dbtype, username='', password='', dbname=''):
    dbtype = dbtype.lower()
    engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
    self.db_engine = create_engine(engine_url)

  metadata = MetaData()

  subsonic_playlist = Table(SUBSONIC_PLAYLIST, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('subsonic_playlist_id', String(500), nullable=False),
                Column('subsonic_playlist_name', String(500), nullable=False),
                Column('tms_insert', DateTime(timezone=True), server_default=func.now(), nullable=False),
                Column('tms_update', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
                )

  subsonic_song = Table(SUBSONIC_SONG, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('subsonic_song_id', String(500), nullable=False),
                Column('subsonic_song_name', String(500), nullable=False),
                Column('tms_insert', DateTime(timezone=True), server_default=func.now(), nullable=False),
                Column('tms_update', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
                )

  subsonic_song_artist_relation = Table(SUBSONIC_SONG_ARTIST_RELATION, metadata,
                Column('song_uuid', String(36), nullable=False),
                Column('artist_uuid', String(36), nullable=False)
                )

  subsonic_artist = Table(SUBSONIC_ARTIST, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('name', String(500), nullable=False),
                Column('subsonic_artist_id', String(500), nullable=False),
                Column('tms_insert', DateTime(timezone=True), server_default=func.now(), nullable=False),
                Column('tms_update', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
                )

  subsonic_spotify_relation = Table(SUBSONIC_SPOTIFY_RELATION, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('subsonic_song_uuid', String(36), nullable=True),
                Column('subsonic_playlist_uuid', String(36), nullable=False),
                Column('spotify_song_uuid', String(36), nullable=False),
                )

  spotify_song = Table(SPOTIFY_SONG, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('title', String(500), nullable=False),
                Column('album', String(500), nullable=False),
                Column('spotify_uri', String(500), nullable=False),
                Column('missing', Integer(), nullable=False),
                Column('tms_insert', DateTime(timezone=True), server_default=func.now(), nullable=False),
                Column('tms_update', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
                )

  spotify_song_artist_relation = Table(SPOTIFY_SONG_ARTIST_RELATION, metadata,
                Column('song_uuid', String(36), nullable=False),
                Column('artist_uuid', String(36), nullable=False)
                )

  spotify_artist = Table(SPOTIFY_ARTIST, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('name', String(500), nullable=False),
                Column('spotify_uri', String(500), nullable=False),
                Column('tms_insert', DateTime(timezone=True), server_default=func.now(), nullable=False),
                Column('tms_update', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
                )


def create_db_tables(self):
  self.metadata.create_all(self.db_engine)

def insert_song(self, playlist_name, subsonic_track, artist_spotify, track_spotify, missing, playlist_id):
  try:
    with self.db_engine.connect() as conn:
      insert_spotify_song(self, conn, artist_spotify, track_spotify, missing)
      conn.commit()
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def insert_subsonic_playlist(self, conn, subsonic_playlist_id):
  song_db = select_spotify_song_by_uri(self, conn, track_spotify["uri"])
  song_uuid = None
  if song_db is None:
    song_uuid = str(uuid.uuid4().hex)
    stmt = insert(self.spotify_song).values(uuid=song_uuid,title=track_spotify["name"], album=track_spotify["album"]["name"], spotify_uri=track_spotify["uri"], missing=missing)
    stmt.compile()
    conn.execute(stmt)
  elif song_db is not None and song_db.uuid is not None:
    song_uuid = song_db.uuid

  if song_uuid is not None:
    artist_uuid = insert_spotify_artist(self, conn, artist_spotify)
    if artist_uuid is not None:
      insert_spotify_song_artist_relation(self, conn, song_uuid, artist_uuid)

def insert_spotify_song(self, conn, artist_spotify, track_spotify, missing):
  song_db = select_spotify_song_by_uri(self, conn, track_spotify["uri"])
  song_uuid = None
  if song_db is None:
    song_uuid = str(uuid.uuid4().hex)
    stmt = insert(self.spotify_song).values(uuid=song_uuid,title=track_spotify["name"], album=track_spotify["album"]["name"], spotify_uri=track_spotify["uri"], missing=missing)
    stmt.compile()
    conn.execute(stmt)
  elif song_db is not None and song_db.uuid is not None:
    song_uuid = song_db.uuid

  if song_uuid is not None:
    artist_uuid = insert_spotify_artist(self, conn, artist_spotify)
    if artist_uuid is not None:
      insert_spotify_song_artist_relation(self, conn, song_uuid, artist_uuid)

def select_spotify_song_by_uri(self, conn, spotify_uri: str):
  value = None
  stmt = select(self.spotify_song.c.uuid,self.spotify_song.c.spotify_uri).where(self.spotify_song.c.spotify_uri==spotify_uri)
  stmt.compile()
  with self.db_engine.connect() as conn:
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
      value   =  row
      cursor.close()
    
  return value

def insert_spotify_artist(self, conn, artist_spotify):
  artist_db = select_spotify_artist_by_uri(self, conn, artist_spotify["uri"])
  if artist_db is None:
    artist_uuid=str(uuid.uuid4().hex)
    stmt = insert(self.spotify_artist).values(uuid=artist_uuid, name=artist_spotify["name"], spotify_uri=artist_spotify["uri"])
    stmt.compile()
    conn.execute(stmt)
    inserted_spotify_artist = select_spotify_artist_by_uri(self, conn, artist_spotify["uri"])
  elif artist_db is not None and artist_db.uuid is not None:
    return artist_db.uuid

def select_spotify_artist_by_uri(self, conn, spotify_uri: str):
  value = None
  stmt = select(self.spotify_artist.c.uuid,self.spotify_artist.c.name,self.spotify_artist.c.spotify_uri).where(self.spotify_artist.c.spotify_uri==spotify_uri)
  stmt.compile()
  cursor = conn.execute(stmt)
  records = cursor.fetchall()

  for row in records:
    value   =  row
    cursor.close()
  
  return value

def insert_spotify_song_artist_relation(self, conn, song_uuid: int, artist_uuid: int):
  if select_spotify_song_artist_relation(self, conn, song_uuid, artist_uuid) is None:
    stmt = insert(self.spotify_song_artist_relation).values(song_uuid=song_uuid, artist_uuid=artist_uuid)
    stmt.compile()
    conn.execute(stmt)
    conn.commit()

def select_spotify_song_artist_relation(self, conn, song_uuid: int, artist_uuid: int):
  value = None
  stmt = select(self.spotify_song_artist_relation.c.song_uuid,self.spotify_song_artist_relation.c.artist_uuid).where(self.spotify_song_artist_relation.c.song_uuid==song_uuid,self.spotify_song_artist_relation.c.artist_uuid==artist_uuid)
  stmt.compile()
  cursor = conn.execute(stmt)
  records = cursor.fetchall()

  for row in records:
    value   =  row
    cursor.close()
    
  return value