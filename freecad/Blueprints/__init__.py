
def _log(*args: object) -> None:
    ''' Convenience logger during development. '''
    from .helper.notify import Notify  # noqa: PLC0415
    Notify.Log.err(' '.join(str(x) for x in args))
