"""
Prompt patch loader for tau2bench evaluations.

This module handles loading and managing prompt patches that fix specific issues
in tau2bench evaluations. Each patch has a unique snake_case identifier and
corresponds to a failure report in experiments/failures/.
"""

import os
from pathlib import Path
from typing import List, Optional


class PromptPatchLoader:
    """Loads and manages prompt patches for tau2bench."""
    
    def __init__(self, patches_dir: Optional[Path] = None):
        """
        Initialize the patch loader.
        
        Args:
            patches_dir: Directory containing patch files. If None, uses default.
        """
        if patches_dir is None:
            # Default to experiments/prompt_patches relative to this file
            repo_root = Path(__file__).parent
            patches_dir = repo_root / "experiments" / "prompt_patches"
        
        self.patches_dir = Path(patches_dir)
        self._cache = {}
    
    def load_patch(self, patch_id: str) -> str:
        """
        Load a single patch by ID.
        
        Args:
            patch_id: Snake_case identifier for the patch
        
        Returns:
            The patch content as a string
        
        Raises:
            FileNotFoundError: If the patch file doesn't exist
        """
        if patch_id in self._cache:
            return self._cache[patch_id]
        
        patch_file = self.patches_dir / f"{patch_id}.txt"
        
        if not patch_file.exists():
            raise FileNotFoundError(
                f"Patch '{patch_id}' not found at {patch_file}. "
                f"Available patches: {self.list_available_patches()}"
            )
        
        with open(patch_file, 'r') as f:
            content = f.read().strip()
        
        self._cache[patch_id] = content
        return content
    
    def load_patches(self, patch_ids: List[str]) -> List[str]:
        """
        Load multiple patches by ID.
        
        Args:
            patch_ids: List of patch identifiers
        
        Returns:
            List of patch contents in the same order
        """
        return [self.load_patch(patch_id) for patch_id in patch_ids]
    
    def list_available_patches(self) -> List[str]:
        """
        List all available patch IDs.
        
        Returns:
            List of patch identifiers (without .txt extension)
        """
        if not self.patches_dir.exists():
            return []
        
        return [
            f.stem for f in self.patches_dir.glob("*.txt")
            if not f.name.startswith("README")
        ]
    
    def get_patch_path(self, patch_id: str) -> Path:
        """Get the file path for a patch ID."""
        return self.patches_dir / f"{patch_id}.txt"
    
    def get_failure_report_path(self, patch_id: str) -> Path:
        """Get the failure report path for a patch ID."""
        failures_dir = self.patches_dir.parent / "failures"
        return failures_dir / f"{patch_id}.md"


# Singleton instance for easy access
_default_loader = None


def get_loader() -> PromptPatchLoader:
    """Get the default patch loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptPatchLoader()
    return _default_loader


def load_patch(patch_id: str) -> str:
    """Convenience function to load a single patch."""
    return get_loader().load_patch(patch_id)


def load_patches(patch_ids: List[str]) -> List[str]:
    """Convenience function to load multiple patches."""
    return get_loader().load_patches(patch_ids)

