class _DummyDownloader:
    def __init__(self):
        self.settings = {}

    def search_and_download(self, song):
        return None


class Spotdl:
    """Minimal stand-in for spotdl.Spotdl (test stub) -- avoids pulling in
    the real spotdl/yt-dlp dependency chain purely to satisfy an unconditional
    module-level import in spotisub.helpers.spotdl_helper."""

    def __init__(self, *args, **kwargs):
        self.downloader = _DummyDownloader()
