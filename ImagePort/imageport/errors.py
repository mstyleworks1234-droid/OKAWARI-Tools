class ImagePortError(Exception):
    """Expected conversion failure with a message safe to show in the UI."""


class AnimatedGifError(ImagePortError):
    pass


class UnsupportedFormatError(ImagePortError):
    pass
