from errors import ServerError


class S3UploadFileError(ServerError):
    message = 'Не удалось загрузить файл'
