#!/usr/bin/env python3
"""
Open Coding CLI for Failure Mode Analysis

This tool performs open coding on tau2bench evaluation failures using OpenAI's o3-pro model.
Open coding is a qualitative research technique where data is broken down into discrete parts,
closely examined, and compared to identify patterns, themes, and categories.

Usage:
    python open_coder.py --input <bee_run.jsonl> --num-samples 10
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
LOGS_DIR = SCRIPT_DIR.parent / "logs"
OUTPUTS_DIR = SCRIPT_DIR.parent / "outputs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
LOG_FILE = LOGS_DIR / f"open_coding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set different levels for file vs console
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Only INFO and above to console

logger = logging.getLogger(__name__)
logger.info(f"📝 Logging to: {LOG_FILE}")


class OpenCoder:
    """Performs open coding on tau2bench failures using OpenAI API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "o3"
        self.reasoning_effort = "high"
        self.base_url = "https://api.openai.com/v1/responses"
        logger.info(f"🤖 Initialized OpenCoder with model: {self.model} (reasoning: {self.reasoning_effort})")
        
    def load_samples(self, jsonl_path: Path, num_samples: int = None) -> List[Dict[str, Any]]:
        """Load samples from bee run JSONL file"""
        logger.info(f"📂 Loading samples from: {jsonl_path}")
        samples = []
        
        try:
            with open(jsonl_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            sample = json.loads(line)
                            samples.append(sample)
                            logger.debug(f"  Line {line_num}: Loaded sample")
                        except json.JSONDecodeError as e:
                            logger.error(f"  Line {line_num}: JSON decode error: {e}")
            
            logger.info(f"✅ Loaded {len(samples)} samples")
            
            # Filter to num_samples if specified
            if num_samples and num_samples < len(samples):
                samples = samples[:num_samples]
                logger.info(f"📊 Limited to first {num_samples} samples")
                
            return samples
            
        except Exception as e:
            logger.error(f"❌ Failed to load samples: {e}")
            raise
    
    def extract_failure_context(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from a failure sample for open coding"""
        logger.debug(f"🔍 Extracting context from sample")
        
        context = {
            "sample_id": sample.get("sample_id", "unknown"),
            "task_name": sample.get("inputs", {}).get("task_name", "unknown"),
            "success": sample.get("outputs", {}).get("reward", 0) > 0.5,
            "reward": sample.get("outputs", {}).get("reward", 0),
            "conversation": sample.get("outputs", {}).get("conversation", []),
            "data_item": sample.get("inputs", {}).get("data_item", {}),
            "raw_prompt": sample.get("outputs", {}).get("raw_prompt", ""),
            "metadata": {
                "estimator": sample.get("estimator", "unknown"),
                "timestamp": sample.get("timestamp", "unknown")
            }
        }
        
        # Extract tau2bench-specific reward details if available
        outputs = sample.get("outputs", {})
        if "reward_details" in outputs or any(k.startswith("reward_") for k in outputs.keys()):
            context["tau2bench_rewards"] = {
                k: v for k, v in outputs.items() 
                if k.startswith("reward_") or k == "reward_details"
            }
        
        logger.debug(f"  Sample ID: {context['sample_id']}")
        logger.debug(f"  Success: {context['success']}, Reward: {context['reward']}")
        logger.debug(f"  Conversation turns: {len(context['conversation'])}")
        
        return context
    
    def build_open_coding_prompt(self, context: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for open coding analysis"""
        
        prompt = f"""# Open Coding Task: Failure Mode Analysis for Tau2Bench Telecom Evaluation

## Context: What is Tau2Bench?

Tau2Bench is a multi-agent simulation benchmark for evaluating AI customer service agents in the telecom domain. 
It simulates realistic customer service scenarios where an AI agent must help customers resolve telecom issues.

### Evaluation Structure:
- **Agent Under Test**: An AI chatbot (customer service agent) being evaluated
- **Simulated User**: An AI-powered user with a specific problem/goal
- **Tool Environment**: Backend systems (billing, network, etc.) and device-side tools
- **Success Criteria**: Whether the agent successfully helped the user achieve their goal

### Tool Access Model:
- **Agent-side tools** (prefixed with `assistant/`): Backend systems the agent can call directly
  Examples: `get_customer_by_phone`, `refuel_data`, `enable_roaming`
- **User-side tools** (prefixed with `user/`): Device actions the user must perform themselves
  Examples: `check_network_status`, `toggle_airplane_mode`, `reset_apn_settings`

### Reward Components:
Tau2Bench uses multiple reward signals to assess performance:
- **Total Reward**: Overall success (0 to 1)
- **Action Reward**: Based on tool calls made
- **Communication Reward**: Quality of agent-user interaction
- **NL Assertions**: Natural language goal checks

## Your Task: Open Coding

Perform **open coding** on this failure case. Open coding is a qualitative analysis technique where you:
1. Read through the data carefully
2. Identify specific failure modes and patterns
3. Create descriptive codes (labels) that capture what went wrong
4. Look for themes without preconceived categories

## Sample Data

**Sample ID**: {context['sample_id']}
**Task**: {context['task_name']}
**Success**: {context['success']}
**Reward**: {context['reward']}

### User's Goal/Scenario:
```json
{json.dumps(context.get('data_item', {}), indent=2)}
```

### Tau2Bench Reward Details:
```json
{json.dumps(context.get('tau2bench_rewards', {}), indent=2)}
```

### Conversation Transcript:
"""
        
        # Add conversation turns (truncate if too long)
        conversation = context.get('conversation', [])
        for i, turn in enumerate(conversation[:50]):  # Limit to first 50 turns
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            tool_calls = turn.get('tool_calls', [])
            tool_results = turn.get('tool_results', [])
            
            # Extract text from content (could be list of dicts or string)
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and 'text' in block:
                        text_parts.append(block['text'])
                content_text = '\n'.join(text_parts)
            else:
                content_text = str(content) if content else ''
            
            prompt += f"\n**Turn {i+1} - {role}**:\n"
            if content_text:
                prompt += f"Message: {content_text[:500]}\n"  # Limit message length
            if tool_calls:
                prompt += f"Tool Calls: {json.dumps(tool_calls, indent=2)}\n"
            if tool_results:
                prompt += f"Tool Results: {json.dumps(tool_results, indent=2)}\n"
        
        if len(conversation) > 50:
            prompt += f"\n... (truncated, {len(conversation) - 50} more turns) ...\n"
        
        prompt += """

## Instructions for Open Coding

Analyze this interaction and provide a **descriptive, detailed analysis** without predetermined categories.

Your task is to:

1. **Describe What Happened**: 
   - Read through the entire conversation carefully
   - Note specific behaviors, actions, and outcomes
   - Identify key moments (success or failure)
   - Point to specific turn numbers where important events occur

2. **Detailed Narrative Analysis**: 
   - What specifically happened in this interaction?
   - Where in the conversation did things go right or wrong?
   - What actions did the agent take?
   - How did the user respond?
   - What was the outcome?

3. **Identify Issues (if any)**:
   - What problems occurred?
   - What could have been done better?
   - Were there repeated patterns of behavior?

4. **Observations**:
   - Note any interesting patterns
   - Identify any systemic-looking issues
   - Note the quality of the interaction

5. **Recommendations**: 
   - What specific changes would improve this interaction?
   - What should the agent do differently?

**Important**: Do NOT create categorical labels (like "tool_confusion", "gave_up_early"). Instead, provide rich, descriptive analysis of what you observe. Categories will be created later by looking across all samples.

**CRITICAL**: Return ONLY a valid JSON object. Do NOT wrap it in markdown code blocks (```json). Do NOT include any text before or after the JSON. Your entire response must be parseable as JSON.

Required JSON format:

{
  "descriptive_summary": "Brief 2-3 sentence summary of what happened",
  "failure_point_turn": <turn_number or null>,
  "detailed_analysis": "Comprehensive narrative analysis of the interaction, describing specific behaviors and outcomes",
  "issues_identified": ["Specific issue 1 described in detail", "Specific issue 2 described in detail"],
  "observations": "Notable patterns or behaviors observed in this interaction",
  "recommendations": "Specific actionable recommendations for improving this interaction"
}
"""
        
        return prompt
    
    async def call_openai_api(self, prompt: str, sample_id: str) -> Dict[str, Any]:
        """Call OpenAI API with o3-pro model"""
        logger.info(f"🤖 Calling OpenAI API for sample {sample_id}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": prompt,  # Responses API uses 'input' instead of 'messages'
            "reasoning": {"effort": self.reasoning_effort}  # High reasoning for thorough analysis
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ API error {response.status}: {error_text}")
                        raise Exception(f"API returned status {response.status}")
                    
                    result = await response.json()
                    logger.debug(f"✅ Got response for sample {sample_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ API call failed for sample {sample_id}: {e}")
            raise
    
    async def process_sample(self, sample: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process a single sample: extract context, call API, parse results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Processing Sample {index + 1}")
        logger.info(f"{'='*60}")
        
        try:
            # Extract context
            context = self.extract_failure_context(sample)
            sample_id = context['sample_id']
            
            # Build prompt
            logger.debug(f"📝 Building prompt for sample {sample_id}")
            prompt = self.build_open_coding_prompt(context)
            
            # Call API
            api_response = await self.call_openai_api(prompt, sample_id)
            
            # Extract coding from response (handle responses API format)
            if 'output' in api_response:
                # Responses API format - output can be a list or string
                output = api_response['output']
                if isinstance(output, list):
                    # Output is a list of dicts with reasoning + message
                    # Find the message dict and extract its content
                    content = None
                    for item in output:
                        if isinstance(item, dict) and item.get('type') == 'message':
                            # Extract text from content array
                            content_items = item.get('content', [])
                            for content_item in content_items:
                                if isinstance(content_item, dict) and content_item.get('type') == 'output_text':
                                    content = content_item.get('text', '')
                                    break
                            if content:
                                break
                    
                    # Fallback: if no message found, stringify for debugging
                    if not content:
                        content = str(output)
                        logger.warning(f"⚠️  Could not find message in output list, using string repr")
                else:
                    content = str(output)
            elif 'choices' in api_response:
                # Chat completions API format (fallback)
                content = api_response['choices'][0]['message']['content']
            else:
                raise ValueError(f"Unknown API response format: {api_response.keys()}")
            
            logger.debug(f"📄 Response length: {len(content)} chars")
            logger.debug(f"📄 Response type: {type(api_response.get('output', 'N/A'))}")
            
            # Try to extract JSON from response
            coding_result = self.parse_coding_response(content)
            
            # Combine with context
            result = {
                "sample_id": sample_id,
                "success": context['success'],
                "reward": context['reward'],
                "context": context,
                "coding": coding_result,
                "raw_response": content,
                "api_usage": api_response.get('usage', {})
            }
            
            logger.info(f"✅ Completed coding for sample {sample_id}")
            summary = coding_result.get('descriptive_summary', 'N/A')
            logger.info(f"   Summary: {summary[:80]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process sample: {e}")
            return {
                "sample_id": sample.get("sample_id", "unknown"),
                "error": str(e)
            }
    
    def parse_coding_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the open coding response from the model"""
        logger.debug("🔍 Parsing coding response")
        
        import re
        
        # Strategy 1: Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        
        if json_match:
            try:
                coding = json.loads(json_match.group(1))
                logger.debug("✅ Successfully parsed JSON from markdown code block")
                return coding
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  JSON in code block invalid: {e}")
        
        # Strategy 2: Try to parse the entire response as JSON (no markdown wrapper)
        try:
            coding = json.loads(response_text)
            logger.debug("✅ Successfully parsed direct JSON response")
            return coding
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Could not parse as direct JSON: {e}")
        
        # Strategy 3: Try to extract JSON object from anywhere in the text
        json_object_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_object_match:
            try:
                coding = json.loads(json_object_match.group(0))
                logger.debug("✅ Successfully extracted and parsed JSON object")
                return coding
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Extracted JSON object invalid: {e}")
        
        # Fallback: return raw text with error
        logger.warning("⚠️  Could not parse structured JSON, returning raw response")
        return {
            "primary_code": "parse_error",
            "raw_response": response_text,
            "error": "Could not extract structured JSON from response"
        }
    
    async def process_batch(self, samples: List[Dict[str, Any]], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Process multiple samples in parallel"""
        logger.info(f"🚀 Processing {len(samples)} samples (max {max_concurrent} concurrent)")
        
        results = []
        for i in range(0, len(samples), max_concurrent):
            batch = samples[i:i+max_concurrent]
            logger.info(f"\n📦 Batch {i//max_concurrent + 1}: Processing samples {i+1} to {min(i+max_concurrent, len(samples))}")
            
            tasks = [self.process_sample(sample, i + j) for j, sample in enumerate(batch)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {result}")
                else:
                    results.append(result)
            
            # Small delay between batches to avoid rate limiting
            if i + max_concurrent < len(samples):
                logger.debug("⏸️  Waiting 2s before next batch...")
                await asyncio.sleep(2)
        
        logger.info(f"\n✅ Completed processing {len(results)} samples")
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Path):
        """Save coding results to JSONL file"""
        logger.info(f"💾 Saving results to: {output_path}")
        
        try:
            with open(output_path, 'w') as f:
                for result in results:
                    f.write(json.dumps(result) + '\n')
            
            logger.info(f"✅ Saved {len(results)} coded results")
            logger.info(f"📊 Summary:")
            
            # Generate summary
            successful = sum(1 for r in results if r.get('success', False))
            failed = len(results) - successful
            
            logger.info(f"\n📋 Open Coding Complete:")
            logger.info(f"  Total samples: {len(results)}")
            logger.info(f"  Successful: {successful}")
            logger.info(f"  Failed: {failed}")
            logger.info(f"\n  → Proceed to axial coding to categorize patterns across all samples")
                
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            raise


async def main():
    parser = argparse.ArgumentParser(
        description="Open Coding CLI for Failure Mode Analysis"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to bee run JSONL file"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to process (default: all)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent API calls (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for coded results (default: auto-generated)"
    )
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Project name for organizing outputs (REQUIRED)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing project directory if it exists"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("🔬 OPEN CODING FAILURE ANALYSIS")
    logger.info("="*60)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Num samples: {args.num_samples or 'all'}")
    logger.info(f"Max concurrent: {args.max_concurrent}")
    logger.info("")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize coder
    coder = OpenCoder(api_key)
    
    # Load samples
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    samples = coder.load_samples(input_path, args.num_samples)
    
    if not samples:
        logger.error("❌ No samples loaded")
        sys.exit(1)
    
    # Process samples
    results = await coder.process_batch(samples, args.max_concurrent)
    
    # Use required project name
    project_name = args.project
    logger.info(f"📁 Project name: {project_name}")
    
    # Check if project directory exists
    project_dir = OUTPUTS_DIR / project_name
    if project_dir.exists():
        if not args.overwrite:
            logger.error(f"❌ Project directory already exists: {project_dir}")
            logger.error(f"   Use --overwrite to overwrite existing project")
            sys.exit(1)
        else:
            logger.warning(f"⚠️  Overwriting existing project directory: {project_dir}")
            # Clean up old open coding files to ensure idempotency
            for old_file in project_dir.glob("open_coded_*.jsonl"):
                logger.info(f"🗑️  Removing old file: {old_file.name}")
                old_file.unlink()
    
    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Project directory: {project_dir}")
    
    # Copy original bee run file to project directory
    original_file_dest = project_dir / f"original_{input_path.name}"
    import shutil
    shutil.copy2(input_path, original_file_dest)
    logger.info(f"📄 Copied original file to: {original_file_dest}")
    
    # Save results to project directory
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = project_dir / f"open_coded_{timestamp}.jsonl"
    
    coder.save_results(results, output_path)
    
    logger.info("\n" + "="*60)
    logger.info("✅ OPEN CODING COMPLETE")
    logger.info("="*60)
    logger.info(f"📁 Project: {project_name}")
    logger.info(f"📂 Directory: {project_dir}")
    logger.info(f"📄 Original file: {original_file_dest}")
    logger.info(f"📄 Open coded: {output_path}")
    logger.info(f"📝 Log file: {LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

