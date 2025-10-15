#!/usr/bin/env python3
"""
Axial Coding CLI for Failure Mode Analysis

This tool performs axial coding on open-coded results. Axial coding is the second phase
of grounded theory analysis where codes from individual samples are analyzed across
ALL samples to identify patterns, relationships, and higher-level categories.

The process:
1. Load open coding results from all samples
2. Analyze patterns across samples using constant comparison
3. Generate a taxonomy of axial codes (categories)
4. Apply these codes back to each sample
5. Output enriched results with both open and axial codes

Usage:
    python axial_coder.py --input <open_coded.jsonl> --output <axial_coded.jsonl>
"""

import argparse
import json
import logging
import os
import sys
import tiktoken
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import aiohttp
import asyncio

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
LOGS_DIR = SCRIPT_DIR.parent / "logs"
OUTPUTS_DIR = SCRIPT_DIR.parent / "outputs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
LOG_FILE = LOGS_DIR / f"axial_coding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
console_handler.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"📝 Logging to: {LOG_FILE}")


class AxialCoder:
    """Performs axial coding on open-coded results using OpenAI API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "o3"
        self.reasoning_effort = "high"
        self.base_url = "https://api.openai.com/v1/responses"
        self.encoding = tiktoken.encoding_for_model("gpt-4")  # Use gpt-4 encoding for token estimation
        logger.info(f"🤖 Initialized AxialCoder with model: {self.model} (reasoning: {self.reasoning_effort})")
        
    def load_open_coded_results(self, jsonl_path: Path) -> List[Dict[str, Any]]:
        """Load open coded results from JSONL file"""
        logger.info(f"📂 Loading open coded results from: {jsonl_path}")
        results = []
        
        try:
            with open(jsonl_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            results.append(result)
                            logger.debug(f"  Line {line_num}: Loaded sample {result.get('sample_id', 'unknown')}")
                        except json.JSONDecodeError as e:
                            logger.error(f"  Line {line_num}: JSON decode error: {e}")
            
            logger.info(f"✅ Loaded {len(results)} open coded samples")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to load open coded results: {e}")
            raise
    
    def extract_for_axial_coding(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relevant information for axial coding (exclude heavy context)"""
        logger.info(f"🔍 Extracting compact representations for axial coding...")
        
        compact_samples = []
        for result in results:
            compact = {
                "sample_id": result.get("sample_id", "unknown"),
                "success": result.get("success", False),
                "reward": result.get("reward", 0),
                "coding": result.get("coding", {})
            }
            
            # Only include summary from context, not full conversation
            if "context" in result:
                compact["conversation_length"] = len(result["context"].get("conversation", []))
            
            compact_samples.append(compact)
        
        logger.debug(f"✅ Created compact representations for {len(compact_samples)} samples")
        return compact_samples
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def build_axial_coding_prompt(self, compact_samples: List[Dict[str, Any]]) -> str:
        """Build prompt for axial coding across all samples"""
        
        prompt = f"""# Axial Coding Task: Cross-Sample Pattern Analysis

## Context: What is Axial Coding?

Axial coding is the second phase of grounded theory analysis. After open coding (analyzing individual samples), 
axial coding looks ACROSS all samples to:

1. **Identify Patterns**: Find recurring themes and commonalities
2. **Create Categories**: Group related observations into higher-level categories
3. **Build Taxonomy**: Develop a hierarchical structure of codes
4. **Establish Relationships**: Understand how categories relate to each other

## Your Task

You have {len(compact_samples)} samples with open coding analyses. Your job is to:

1. **Read through ALL open coding results** (provided below)
2. **Use constant comparison method** - compare each sample's observations to others
3. **Identify patterns** that appear across multiple samples
4. **Create axial codes** - categorical labels that group similar open codes
5. **Build a taxonomy** - organize these codes hierarchically

## Open Coded Samples

"""
        
        # Add all compact samples
        for i, sample in enumerate(compact_samples, 1):
            coding = sample.get('coding', {})
            prompt += f"\n### Sample {i} (ID: {sample['sample_id']})\n"
            prompt += f"**Success**: {sample['success']}, **Reward**: {sample['reward']}\n"
            if 'conversation_length' in sample:
                prompt += f"**Conversation Length**: {sample['conversation_length']} turns\n"
            
            prompt += f"\n**Summary**: {coding.get('descriptive_summary', 'N/A')}\n"
            prompt += f"\n**Issues Identified**:\n"
            for issue in coding.get('issues_identified', []):
                prompt += f"- {issue}\n"
            prompt += f"\n**Observations**: {coding.get('observations', 'N/A')}\n"
            prompt += f"\n---\n"
        
        prompt += """

## Instructions for Axial Coding

Based on your analysis of ALL samples above:

### Step 1: Identify Core Categories

Look across all samples and identify 5-10 **core categories** that capture the main patterns. Each category should:
- Represent a distinct type of issue or pattern
- Appear in multiple samples (not one-off issues)
- Be clearly defined and distinguishable from other categories

### Step 2: Build Taxonomy

Organize these categories into a hierarchical structure:
- **Primary Categories**: High-level groupings (3-5 categories)
- **Subcategories**: More specific issues within each primary category

### Step 3: Define Each Code

For each axial code in your taxonomy, provide:
- **Code Name**: Short, descriptive label (e.g., "tool_access_error", "communication_breakdown")
- **Definition**: Clear description of what this code means
- **Indicators**: What to look for when applying this code
- **Examples**: Which samples exhibit this pattern

### Step 4: Assign Codes to Samples

For each sample, identify:
- **Primary Code**: The main category that best describes the sample
- **Secondary Codes**: Additional relevant categories (0-3 codes)
- **Severity**: Critical | Major | Minor | None (for successful cases)

## Output Format

**CRITICAL**: Return ONLY a valid JSON object. Do NOT wrap it in markdown code blocks (```json). Do NOT include any text before or after the JSON. Your entire response must be parseable as JSON.

Required JSON format:

{
  "taxonomy": {
    "primary_categories": [
      {
        "name": "category_name",
        "definition": "What this category represents",
        "subcategories": [
          {
            "code": "specific_code_name",
            "definition": "What this specific code means",
            "indicators": ["indicator1", "indicator2"],
            "sample_ids": ["sample_id1", "sample_id2"]
          }
        ]
      }
    ]
  },
  "sample_assignments": [
    {
      "sample_id": "sample_id_here",
      "primary_code": "most_relevant_code",
      "secondary_codes": ["additional_code1", "additional_code2"],
      "severity": "critical|major|minor|none",
      "rationale": "Brief explanation of why these codes were assigned"
    }
  ]
}

**Important**: 
- Base codes on actual patterns in the data, not preconceived categories
- Each code should appear in at least 2 samples (avoid one-off codes)
- Use clear, descriptive names
- Ensure codes are mutually exclusive where possible
"""
        
        return prompt
    
    async def call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for axial coding"""
        logger.info(f"🤖 Calling OpenAI API for axial coding...")
        
        # Count tokens before call
        prompt_tokens_est = self.count_tokens(prompt)
        logger.info(f"📊 Estimated input tokens: {prompt_tokens_est:,}")
        
        if prompt_tokens_est > 100000:
            logger.warning(f"⚠️  Large prompt ({prompt_tokens_est:,} tokens) - may take longer")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": prompt,  # Responses API uses 'input' instead of 'messages'
            "reasoning": {"effort": self.reasoning_effort}  # High reasoning for systematic pattern analysis
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 minute timeout for large analysis
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ API error {response.status}: {error_text}")
                        raise Exception(f"API returned status {response.status}")
                    
                    result = await response.json()
                    
                    # Log actual token usage
                    usage = result.get('usage', {})
                    logger.info(f"📊 Actual token usage:")
                    logger.info(f"   Input tokens:  {usage.get('prompt_tokens', 0):,}")
                    logger.info(f"   Output tokens: {usage.get('completion_tokens', 0):,}")
                    logger.info(f"   Total tokens:  {usage.get('total_tokens', 0):,}")
                    
                    return result
                    
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            raise
    
    def parse_axial_coding_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the axial coding response from the model"""
        logger.debug("🔍 Parsing axial coding response")
        
        import re
        
        # Strategy 1: Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                logger.debug("✅ Successfully parsed JSON from markdown code block")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  JSON in code block invalid: {e}")
        
        # Strategy 2: Try to parse the entire response as JSON (no markdown wrapper)
        try:
            result = json.loads(response_text)
            logger.debug("✅ Successfully parsed direct JSON response")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Could not parse as direct JSON: {e}")
        
        # Strategy 3: Try to find JSON anywhere in response (find first { to last })
        try:
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1:
                json_str = response_text[start:end+1]
                result = json.loads(json_str)
                logger.debug("✅ Successfully extracted JSON from response")
                return result
        except Exception as e:
            logger.warning(f"⚠️  Could not extract JSON: {e}")
        
        # Last resort: return raw response with error
        logger.error("❌ Could not parse structured JSON from response")
        return {
            "taxonomy": {"primary_categories": []},
            "sample_assignments": [],
            "error": "Could not parse structured JSON from response",
            "raw_response": response_text
        }
    
    def enrich_samples_with_axial_codes(
        self, 
        original_results: List[Dict[str, Any]], 
        axial_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enrich original samples with axial codes"""
        logger.info(f"📊 Enriching {len(original_results)} samples with axial codes...")
        
        # Create lookup for assignments
        assignments = {
            a['sample_id']: a 
            for a in axial_analysis.get('sample_assignments', [])
        }
        
        enriched = []
        for result in original_results:
            sample_id = result.get('sample_id')
            enriched_result = result.copy()
            
            # Add axial codes
            if sample_id in assignments:
                enriched_result['axial_coding'] = assignments[sample_id]
                logger.debug(f"  ✓ Added axial codes to {sample_id}")
            else:
                logger.warning(f"  ⚠️  No axial codes found for {sample_id}")
                enriched_result['axial_coding'] = {
                    "primary_code": None,
                    "secondary_codes": [],
                    "severity": None,
                    "rationale": "No axial code assigned"
                }
            
            enriched.append(enriched_result)
        
        logger.info(f"✅ Enriched all samples with axial codes")
        return enriched
    
    def save_results(
        self, 
        enriched_results: List[Dict[str, Any]], 
        taxonomy: Dict[str, Any],
        output_path: Path
    ):
        """Save enriched results and taxonomy"""
        logger.info(f"💾 Saving results to: {output_path}")
        
        try:
            # Save enriched samples
            with open(output_path, 'w') as f:
                for result in enriched_results:
                    f.write(json.dumps(result) + '\n')
            
            # Save taxonomy separately
            taxonomy_path = output_path.parent / f"{output_path.stem}_taxonomy.json"
            with open(taxonomy_path, 'w') as f:
                json.dump(taxonomy, f, indent=2)
            
            logger.info(f"✅ Saved {len(enriched_results)} enriched results")
            logger.info(f"✅ Saved taxonomy to: {taxonomy_path}")
            
            # Generate summary
            code_distribution = {}
            severity_distribution = {}
            
            for r in enriched_results:
                axial = r.get('axial_coding', {})
                primary = axial.get('primary_code')
                severity = axial.get('severity')
                
                if primary:
                    code_distribution[primary] = code_distribution.get(primary, 0) + 1
                if severity:
                    severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
            
            logger.info(f"\n📊 Axial Coding Summary:")
            logger.info(f"\n📋 Primary Code Distribution:")
            for code, count in sorted(code_distribution.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {code:40s}: {count}")
            
            logger.info(f"\n⚠️  Severity Distribution:")
            for severity, count in sorted(severity_distribution.items()):
                logger.info(f"  {severity:15s}: {count}")
            
            logger.info(f"\n📁 Taxonomy Categories: {len(taxonomy.get('primary_categories', []))}")
            for cat in taxonomy.get('primary_categories', []):
                subcats = len(cat.get('subcategories', []))
                logger.info(f"  • {cat['name']:30s} ({subcats} subcategories)")
                
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            raise


async def main():
    parser = argparse.ArgumentParser(
        description="Axial Coding CLI for Failure Mode Analysis"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to open coded JSONL file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for axial coded results (default: auto-generated)"
    )
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Project name for organizing outputs (REQUIRED, should match open coding project)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing axial coding results if they exist"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("🔬 AXIAL CODING ANALYSIS")
    logger.info("="*60)
    logger.info(f"Input file: {args.input}")
    logger.info("")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize coder
    coder = AxialCoder(api_key)
    
    # Load open coded results
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    open_coded_results = coder.load_open_coded_results(input_path)
    
    if not open_coded_results:
        logger.error("❌ No open coded results loaded")
        sys.exit(1)
    
    # Extract compact representations
    compact_samples = coder.extract_for_axial_coding(open_coded_results)
    
    # Build prompt
    logger.info("📝 Building axial coding prompt...")
    prompt = coder.build_axial_coding_prompt(compact_samples)
    
    # Call API
    api_response = await coder.call_openai_api(prompt)
    
    # Parse response (handle responses API format)
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
    
    axial_analysis = coder.parse_axial_coding_response(content)
    
    # Enrich samples
    enriched_results = coder.enrich_samples_with_axial_codes(
        open_coded_results,
        axial_analysis
    )
    
    # Use required project name
    project_name = args.project
    project_dir = OUTPUTS_DIR / project_name
    
    # Check if project directory exists
    if not project_dir.exists():
        logger.error(f"❌ Project directory does not exist: {project_dir}")
        logger.error(f"   Run open_coder.py first to create the project")
        sys.exit(1)
    
    logger.info(f"📁 Project name: {project_name}")
    logger.info(f"📁 Project directory: {project_dir}")
    
    # Check if any axial coding results already exist
    existing_axial = list(project_dir.glob("axial_coded_*.jsonl"))
    if existing_axial and not args.overwrite:
        logger.error(f"❌ Axial coding results already exist in project: {project_name}")
        logger.error(f"   Found {len(existing_axial)} existing axial coded file(s)")
        logger.error(f"   Use --overwrite to overwrite existing results")
        sys.exit(1)
    elif existing_axial and args.overwrite:
        logger.warning(f"⚠️  Overwriting existing axial coding results ({len(existing_axial)} file(s))")
        # Remove old axial coding files
        for old_file in existing_axial:
            old_file.unlink()
            logger.debug(f"   Deleted: {old_file.name}")
        # Also remove taxonomy files
        for old_tax in project_dir.glob("axial_coded_*_taxonomy.json"):
            old_tax.unlink()
            logger.debug(f"   Deleted: {old_tax.name}")
    
    # Generate output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = project_dir / f"axial_coded_{timestamp}.jsonl"
    
    coder.save_results(
        enriched_results,
        axial_analysis.get('taxonomy', {}),
        output_path
    )
    
    logger.info("\n" + "="*60)
    logger.info("✅ AXIAL CODING COMPLETE")
    logger.info("="*60)
    logger.info(f"📁 Project: {project_name}")
    logger.info(f"📂 Directory: {project_dir}")
    logger.info(f"📄 Axial coded: {output_path}")
    logger.info(f"📄 Taxonomy: {output_path.parent / f'{output_path.stem}_taxonomy.json'}")
    logger.info(f"📝 Log file: {LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

