"""
Integration test for prompt patches system.

This tests the full flow: TOML config → loader → apiary patching → system prompt.
"""

import pytest
import sys
import os

# Add eval-ds root to path
eval_ds_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, eval_ds_root)

from prompt_patch_loader import load_patches


def test_patch_loading():
    """Test that patches can be loaded from files."""
    patches = load_patches(["TOOL_CONFUSION_AGENT_VS_USER"])
    
    assert len(patches) == 1
    assert "CRITICAL" in patches[0]
    assert "AGENT TOOLS" in patches[0]
    assert "USER DEVICE TOOLS" in patches[0]


def test_apiary_function_with_patches():
    """Test that apiary's get_chatbot_system_prompt accepts patches."""
    try:
        from comb.envs.tau2bench.utils.chatbot_system_prompt import get_chatbot_system_prompt
    except ImportError:
        pytest.skip("apiary not available in test environment")
    
    # Test without patches
    prompt1 = get_chatbot_system_prompt("Test policy")
    
    # Test with patches
    patches = load_patches(["TOOL_CONFUSION_AGENT_VS_USER"])
    prompt2 = get_chatbot_system_prompt("Test policy", prompt_patches=patches)
    
    # Verify patch was applied
    assert len(prompt2) > len(prompt1)
    assert "CRITICAL - Tool Access Boundaries" in prompt2
    assert "AGENT TOOLS" in prompt2
    assert "USER DEVICE TOOLS" in prompt2
    
    # Verify original parts are still there
    assert "<instructions>" in prompt2
    assert "</instructions>" in prompt2
    assert "<policy>" in prompt2
    assert "</policy>" in prompt2
    assert "Test policy" in prompt2


def test_patch_structure():
    """Test that patches maintain prompt structure."""
    try:
        from comb.envs.tau2bench.utils.chatbot_system_prompt import get_chatbot_system_prompt
    except ImportError:
        pytest.skip("apiary not available in test environment")
    
    patches = load_patches(["TOOL_CONFUSION_AGENT_VS_USER"])
    prompt = get_chatbot_system_prompt("Test policy content", prompt_patches=patches)
    
    # Check structure order
    inst_start = prompt.index("<instructions>")
    inst_end = prompt.index("</instructions>")
    policy_start = prompt.index("<policy>")
    policy_end = prompt.index("</policy>")
    critical_idx = prompt.index("CRITICAL")
    
    # Patch should be inside instructions, before policy
    assert inst_start < critical_idx < inst_end < policy_start < policy_end


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

