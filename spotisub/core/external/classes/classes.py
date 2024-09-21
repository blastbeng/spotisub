class ComparisonHelper:
  def __init__(self, track, artist_spotify, found, excluded, song_ids, track_helper):
    self.track = track
    self.artist_spotify = artist_spotify
    self.found = found
    self.excluded = excluded
    self.song_ids = song_ids
    self.track_helper = track_helper