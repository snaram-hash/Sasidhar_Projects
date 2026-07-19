class CUISException(Exception):
    """Base exception class for all Credit Underwriting Intelligence Suite exceptions."""
    pass

class DocumentValidationError(CUISException):
    """Raised when uploaded documents fail structural, type, size, or readability validation."""
    pass

class DatabaseConnectionError(CUISException):
    """Raised when database connection, schema generation, or transactions fail."""
    pass

class FinancialDataError(CUISException):
    """Raised when calculation errors occur or financial data shows inconsistencies/missing values."""
    pass

class RiskEngineError(CUISException):
    """Raised when rule parsing, verification checks, or scorecards fail to evaluate."""
    pass

class CAMGenerationError(CUISException):
    """Raised when writing, updating, or formatting the Excel CAM sheet fails."""
    pass
