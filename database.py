import os
import sys
import logging
from sqlalchemy import create_engine, insert, select, update, delete, Table, Column, Integer, String, DateTime, MetaData
from sqlalchemy.sql import func

SQLITE            = 'subtify'
MISSING_SONGS     = 'missing_songs'

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

  missing_songs = Table(SUBITO, metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('title', String(500), nullable=False),
                Column('artist', String(500), nullable=False),
                Column('album', String(500), nullable=False),
                Column('tms_insert', Column(DateTime(timezone=True), server_default=func.now()), nullable=False),
                Column('tms_update', Column(DateTime(timezone=True), server_default=func.now()), nullable=False)
                )

def create_db_tables(self):
  try:
    self.metadata.create_all(self.db_engine)
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)


def insert_missing_songs(self, id: str, title: str, artist: str, album: str, tms_insert: str, tms_update: str):
  try:
    stmt = insert(self.missing_songs).values(id=id, title=title, artist=artist, album=album, tms_insert=tms_insert, tms_update=tms_update).prefix_with('OR IGNORE')
    compiled = stmt.compile()
    with self.db_engine.connect() as conn:
      result = conn.execute(stmt)
      conn.commit()
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def delete_missing_songs(self, id: str, title: str, artist: str, album: str):
  try:
    stmt = delete(self.missing_songs).where(self.missing_songs.c.title==title, self.missing_songs.c.artist==artist,self.missing_songs.c.album==album)
    compiled = stmt.compile()
    with self.db_engine.connect() as conn:
      result = conn.execute(stmt)
      conn.commit()
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def select_missing_songs(self, id: str, title: str, artist: str, album: str):
  try:
    value = None
    stmt = select(self.subito.c.id).where(self.missing_songs.c.title==title, self.missing_songs.c.artist==artist,self.missing_songs.c.album==album)
    compiled = stmt.compile()
    with self.db_engine.connect() as conn:
      cursor = conn.execute(stmt)
      records = cursor.fetchall()

      for row in records:
        value   =  row
        cursor.close()
      
      return value
  except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
    return None