from src.domain.interfaces import ILabelValidator


class SimpleLabelValidator(ILabelValidator):
    """Simple label validator."""
    
    def __init__(self, min_length: int = 1, max_length: int = 100):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, label: str) -> bool:
        """Validate label."""
        if not label:
            return False
        
        label = label.strip()
        
        if len(label) < self.min_length:
            return False
        
        if len(label) > self.max_length:
            return False
        
        return True
    
    def get_validation_error(self, label: str) -> str:
        """Get validation error message."""
        if not label or not label.strip():
            return "Label cannot be empty"
        
        label = label.strip()
        
        if len(label) < self.min_length:
            return f"Label must be at least {self.min_length} characters"
        
        if len(label) > self.max_length:
            return f"Label cannot exceed {self.max_length} characters"
        
        return ""