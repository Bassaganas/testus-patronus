from app.infrastructure.document_sources.file_source import FileDocumentSource

class DocumentProcessorFactory:
    _instance = None

    @classmethod
    def get_document_processor(cls):
        if cls._instance is None:
            cls._instance = FileDocumentSource()
        return cls._instance 