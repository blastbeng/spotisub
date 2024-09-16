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

  subsonic_spotify_relation = Table(SUBSONIC_SPOTIFY_RELATION, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('subsonic_song_id', String(36), nullable=True),
                Column('subsonic_artist_id', String(36), nullable=True),
                Column('subsonic_playlist_id', String(36), nullable=False),
                Column('spotify_song_uuid', String(36), nullable=False),
                )

  spotify_song = Table(SPOTIFY_SONG, metadata,
                Column('uuid', String(36), primary_key=True, nullable=False),
                Column('title', String(500), nullable=False),
                Column('album', String(500), nullable=False),
                Column('spotify_uri', String(500), nullable=False),
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

def insert_song(self, playlist_id, subsonic_track, artist_spotify, track_spotify):
  try:
    with self.db_engine.connect() as conn:
      spotify_song_uuid = insert_spotify_song(self, conn, artist_spotify, track_spotify)
      if spotify_song_uuid is not None:
        if subsonic_track is None:
          insert_playlist_relation(self, conn, None, None, playlist_id, spotify_song_uuid)
        else:
          insert_playlist_relation(self, conn, subsonic_track["id"], subsonic_track["artistId"], playlist_id, spotify_song_uuid)
        conn.commit()      
      else:
        conn.rollback()
      conn.close()
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def delete_playlist_relation_by_id(self, playlist_id: str):
  try:
    stmt = delete(self.subsonic_spotify_relation).where(self.subsonic_spotify_relation.c.subsonic_playlist_id==playlist_id)
    compiled = stmt.compile()
    with self.db_engine.connect() as conn:
      result = conn.execute(stmt)
      conn.commit()
    conn.close()
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def insert_playlist_relation(self, conn, subsonic_song_id, subsonic_artist_id, subsonic_playlist_id, spotify_song_uuid):
  stmt = insert(self.subsonic_spotify_relation).values(uuid=str(uuid.uuid4().hex), subsonic_song_id=subsonic_song_id, subsonic_artist_id=subsonic_artist_id, subsonic_playlist_id=subsonic_playlist_id, spotify_song_uuid=spotify_song_uuid).prefix_with('OR IGNORE')
  stmt.compile()
  conn.execute(stmt)

def select_all_playlists(self, missing):
  value = []
  stmt = None
  with self.db_engine.connect() as conn:
    if missing:
      stmt = select(self.subsonic_spotify_relation.c.uuid,self.subsonic_spotify_relation.c.subsonic_song_id,self.subsonic_spotify_relation.c.subsonic_artist_id,self.subsonic_spotify_relation.c.subsonic_playlist_id,self.subsonic_spotify_relation.c.spotify_song_uuid).where(self.subsonic_spotify_relation.c.subsonic_song_id==None,self.subsonic_spotify_relation.c.subsonic_artist_id==None)
    else:
      stmt = select(self.subsonic_spotify_relation.c.uuid,self.subsonic_spotify_relation.c.subsonic_song_id,self.subsonic_spotify_relation.c.subsonic_artist_id,self.subsonic_spotify_relation.c.subsonic_playlist_id,self.subsonic_spotify_relation.c.spotify_song_uuid)
    stmt.compile()
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
      song = select_spotify_song_by_uuid(self, conn, row.spotify_song_uuid)
      if song is not None and song.title is not None:
        artists_relation = select_spotify_song_artists_relation_by_song_uuid(self, conn, row.spotify_song_uuid)
        artists = []
        for artist_rel in artists_relation:
          artist_found = select_spotify_artists_by_uuid(self, conn, artist_rel.artist_uuid)
          if artist_found is not None and artist_found.name is not None:
            artist_row = {}
            artist_row["name"] = artist_found.name
            artist_row["uri"] = artist_found.spotify_uri
            artists.append(artist_row)
        if(len(artists) > 0):
          result = {} 
          result["spotify_song_title"] = song.title
          result["spotify_song_uri"] = song.spotify_uri
          result["spotify_artists"] = artists
          result["subsonic_song_id"] = row.subsonic_song_id
          result["subsonic_artist_id"] = row.subsonic_artist_id
          result["subsonic_playlist_id"] = row.subsonic_playlist_id

        value.append(result)

    cursor.close()
    conn.close()
    
  return value


def select_spotify_artists_by_uuid(self, conn, uuid: str):
  value = None
  stmt = select(self.spotify_artist.c.uuid,self.spotify_artist.c.name,self.spotify_artist.c.spotify_uri).where(self.spotify_artist.c.uuid==uuid)
  stmt.compile()
  cursor = conn.execute(stmt)
  records = cursor.fetchall()

  for row in records:
    value   =  row
    cursor.close()
  
  return value

def insert_spotify_song(self, conn, artist_spotify, track_spotify):
  song_db = select_spotify_song_by_uri(self, conn, track_spotify["uri"])
  song_uuid = None
  if song_db is None:
    song_uuid = str(uuid.uuid4().hex)
    stmt = insert(self.spotify_song).values(uuid=song_uuid,title=track_spotify["name"], album=track_spotify["album"]["name"], spotify_uri=track_spotify["uri"])
    stmt.compile()
    conn.execute(stmt)
  elif song_db is not None and song_db.uuid is not None:
    song_uuid = song_db.uuid

  if song_uuid is not None:
    artist_uuid = insert_spotify_artist(self, conn, artist_spotify)
    if artist_uuid is not None:
      insert_spotify_song_artist_relation(self, conn, song_uuid, artist_uuid)
      return song_uuid

def select_spotify_song_by_uri(self, conn, spotify_uri: str):
  value = None
  stmt = select(self.spotify_song.c.uuid,self.spotify_song.c.spotify_uri,self.spotify_song.c.title).where(self.spotify_song.c.spotify_uri==spotify_uri)
  stmt.compile()
  with self.db_engine.connect() as conn:
    cursor = conn.execute(stmt)
    records = cursor.fetchall()

    for row in records:
      value   =  row
      cursor.close()
    
  return value

def select_spotify_song_by_uuid(self, conn, uuid: str):
  value = None
  stmt = select(self.spotify_song.c.uuid,self.spotify_song.c.spotify_uri,self.spotify_song.c.title).where(self.spotify_song.c.uuid==uuid)
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
    return artist_uuid
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

def select_spotify_song_artists_relation_by_song_uuid(self, conn, song_uuid: int):
  value = []
  stmt = select(self.spotify_song_artist_relation.c.artist_uuid).where(self.spotify_song_artist_relation.c.song_uuid==song_uuid)
  stmt.compile()
  cursor = conn.execute(stmt)
  records = cursor.fetchall()

  for row in records:
    value.append(row)
    cursor.close()
    
  return value