import contextlib

from settings import Settings

with contextlib.suppress(ImportError):
    from uvicorn import run

from bootstrap import make_app  # noqa


def main() -> None:
    settings = Settings()
    run(
        app='main:make_app',
        host=settings.env.backend.host,
        port=settings.env.backend.port,
        factory=True,
        workers=1,
    )


if __name__ == '__main__':
    main()
