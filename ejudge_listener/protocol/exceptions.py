class ProtocolNotFoundError(FileNotFoundError):
    pass


class TestsNotFoundError(ProtocolNotFoundError):
    pass


class XmlReportNotFoundError(ProtocolNotFoundError):
    pass


class AuditNotFoundError(ProtocolNotFoundError):
    pass


class SourcesNotFoundError(ProtocolNotFoundError):
    pass


class OutputNotFoundError(ProtocolNotFoundError):
    pass
