"""Tests for the status header display."""

import pytest
from bee_sample_viewer.app import BeeViewerApp


@pytest.mark.asyncio
async def test_status_header_exists(test_jsonl_file):
    """Test that status header widget exists."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Check that status header exists
        status_header = app.query_one("#status-header")
        assert status_header is not None


@pytest.mark.asyncio
async def test_status_header_shows_passed(test_jsonl_file):
    """Test status header for a passed sample."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Find a sample with reward=1.0
        passed_index = None
        for i, sample in enumerate(app.samples):
            if sample.get("metrics", {}).get("mean_reward") == 1.0:
                passed_index = i
                break
        
        if passed_index is not None:
            app.show_sample(passed_index)
            await pilot.pause()
            
            status_header = app.query_one("#status-header")
            status_text = str(status_header.renderable)
            
            assert "PASSED" in status_text or "✅" in status_text
            assert "1.0" in status_text


@pytest.mark.asyncio
async def test_status_header_shows_failed(test_jsonl_file):
    """Test status header for a failed sample."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Find a sample with reward=0.0
        failed_index = None
        for i, sample in enumerate(app.samples):
            if sample.get("metrics", {}).get("mean_reward") == 0.0:
                failed_index = i
                break
        
        if failed_index is not None:
            app.show_sample(failed_index)
            await pilot.pause()
            
            status_header = app.query_one("#status-header")
            status_text = str(status_header.renderable)
            
            assert "FAILED" in status_text or "❌" in status_text
            assert "0.0" in status_text


@pytest.mark.asyncio
async def test_status_header_shows_sample_number(test_jsonl_file):
    """Test that status header shows correct sample number."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        app.show_sample(0)
        await pilot.pause()
        
        status_header = app.query_one("#status-header")
        # Label stores text in renderable, which can be a Text object
        status_text = str(status_header.render())
        
        assert "Sample #1" in status_text or "#1/" in status_text


@pytest.mark.asyncio
async def test_status_header_shows_task_name(test_jsonl_file):
    """Test that status header shows task name."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        app.show_sample(0)
        await pilot.pause()
        
        status_header = app.query_one("#status-header")
        # Label stores text in renderable, which can be a Text object
        status_text = str(status_header.render())
        
        # Should show abbreviated task name
        assert "Task:" in status_text


@pytest.mark.asyncio
async def test_status_header_shows_no_op(test_jsonl_file):
    """Test that status header shows no-op status."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        app.show_sample(0)
        await pilot.pause()
        
        status_header = app.query_one("#status-header")
        # Label stores text in renderable, which can be a Text object
        status_text = str(status_header.render())
        
        # Should show No-Op status
        assert "No-Op:" in status_text


@pytest.mark.asyncio
async def test_status_header_updates_on_navigation(test_jsonl_file):
    """Test that status header updates when navigating samples."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Show first sample
        app.show_sample(0)
        await pilot.pause()
        
        status_header = app.query_one("#status-header")
        # Label stores text in renderable, which can be a Text object
        first_text = str(status_header.render())
        
        # Navigate to second sample
        app.show_sample(1)
        await pilot.pause()
        
        second_text = str(status_header.render())
        
        # Status should have changed (different sample numbers at minimum)
        assert first_text != second_text
        assert "#1/" in first_text
        assert "#2/" in second_text


@pytest.mark.asyncio
async def test_status_header_shows_task_success_rate(test_jsonl_file):
    """Test that status header shows task-level success rate if available."""
    app = BeeViewerApp(test_jsonl_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        
        app.show_sample(0)
        await pilot.pause()
        
        # Check if first sample has task metrics
        sample = app.samples[0]
        task_metrics = sample.get("task_run_info", {}).get("task_metrics", {})
        
        if any("mean_reward" in key for key in task_metrics.keys()):
            status_header = app.query_one("#status-header")
            status_text = str(status_header.renderable)
            
            # Should show percentage for overall task success
            assert "overall" in status_text.lower() or "%" in status_text

