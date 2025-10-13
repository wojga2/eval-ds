"""
Tests for the prompt patch loader.
"""

import pytest
from pathlib import Path
from prompt_patch_loader import PromptPatchLoader, load_patch, load_patches


def test_load_tool_confusion_patch():
    """Test loading the TOOL_CONFUSION_AGENT_VS_USER patch."""
    patch = load_patch("TOOL_CONFUSION_AGENT_VS_USER")
    
    assert "CRITICAL - Tool Access Boundaries" in patch
    assert "AGENT TOOLS" in patch
    assert "USER DEVICE TOOLS" in patch
    assert len(patch) > 100


def test_load_multiple_patches():
    """Test loading multiple patches at once."""
    patches = load_patches(["TOOL_CONFUSION_AGENT_VS_USER"])
    
    assert len(patches) == 1
    assert "CRITICAL" in patches[0]


def test_load_nonexistent_patch():
    """Test that loading a nonexistent patch raises an error."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_patch("nonexistent_patch")
    
    assert "not found" in str(exc_info.value)


def test_list_available_patches():
    """Test listing available patches."""
    loader = PromptPatchLoader()
    patches = loader.list_available_patches()
    
    assert "TOOL_CONFUSION_AGENT_VS_USER" in patches
    assert len(patches) >= 1


def test_patch_cache():
    """Test that patches are cached after first load."""
    loader = PromptPatchLoader()
    
    # Load once
    patch1 = loader.load_patch("TOOL_CONFUSION_AGENT_VS_USER")
    
    # Load again - should come from cache
    patch2 = loader.load_patch("TOOL_CONFUSION_AGENT_VS_USER")
    
    assert patch1 == patch2
    assert patch1 is patch2  # Same object reference


def test_get_failure_report_path():
    """Test getting the failure report path for a patch."""
    loader = PromptPatchLoader()
    path = loader.get_failure_report_path("TOOL_CONFUSION_AGENT_VS_USER")
    
    assert "failures" in str(path)
    assert "TOOL_CONFUSION_AGENT_VS_USER.md" in str(path)


def test_patch_content_not_empty():
    """Test that patch content is not empty."""
    loader = PromptPatchLoader()
    patch = loader.load_patch("TOOL_CONFUSION_AGENT_VS_USER")
    
    assert patch.strip()  # Not empty
    assert len(patch) > 50  # Has substantial content

