from XYZBootLoader.Utils.Singleton import singleton


@singleton
class _Cmd:

    SET_MODE = b'\xcc\xdd\xaa\xbb'
    SET_REGISTER = b'\xaa\xbb\xcc\xdd'
    SET_END = b'\xee\xff\x55\xaa'


CMD = _Cmd()
