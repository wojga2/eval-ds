#!/usr/bin/env python3
"""
Sample Analyzer - Interactive Streamlit app for analyzing unsuccessful eval samples.

Displays model responses, expected responses, and scores for samples that scored poorly.
"""

import streamlit as st
import pandas as pd
import json
import ast
from pathlib import Path


def load_and_parse_data(csv_path: str) -> pd.DataFrame:
    """Load CSV data and parse JSON columns."""
    df = pd.read_csv(csv_path)
    
    # Parse JSON columns safely
    def safe_parse_json(text):
        if pd.isna(text) or text == "":
            return None
        try:
            # Handle list format like ['response']
            if isinstance(text, str) and text.startswith('[') and text.endswith(']'):
                return ast.literal_eval(text)
            # Handle JSON format
            elif isinstance(text, str) and (text.startswith('{') or text.startswith('[')):
                return json.loads(text)
            return text
        except (json.JSONDecodeError, ValueError, SyntaxError):
            return text
    
    # Parse relevant columns
    for col in df.columns:
        if 'output' in col or 'inputs' in col:
            df[col] = df[col].apply(safe_parse_json)
    
    return df


def extract_judge_score(judge_output):
    """Extract score from judge output."""
    if judge_output is None:
        return None
    
    try:
        if isinstance(judge_output, str):
            # Remove markdown code block formatting if present
            text = judge_output.strip()
            if text.startswith('```json\n') and text.endswith('\n```'):
                text = text[8:-4]  # Remove ```json\n and \n```
            elif text.startswith('```\n') and text.endswith('\n```'):
                text = text[4:-4]  # Remove ```\n and \n```
            
            # Parse JSON
            judge_output = json.loads(text)
        
        if isinstance(judge_output, dict):
            return judge_output.get('score')
        
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def extract_original_prompt(judge_input):
    """Extract the original prompt that was given to the model from judge input."""
    if judge_input is None:
        return None
    
    try:
        # Handle string inputs (JSON or Python string representation)
        if isinstance(judge_input, str):
            try:
                # Try JSON first
                judge_input = json.loads(judge_input)
            except json.JSONDecodeError:
                # Fall back to ast.literal_eval for Python string representation
                judge_input = ast.literal_eval(judge_input)
        
        # Handle both parsed lists and string-parsed lists
        if isinstance(judge_input, list) and len(judge_input) > 0:
            if isinstance(judge_input[0], dict) and 'content' in judge_input[0]:
                content = judge_input[0]['content']
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get('text', '')
                    # Extract the prompt from the evaluation text
                    # Try Arabic format first
                    if 'الإشارة التي تلقاها النموذج:' in text:
                        marker = 'الإشارة: "'
                        start = text.find(marker)
                        if start != -1:
                            start += len(marker)
                            end = text.find('"', start)
                            if end != -1 and end > start:
                                prompt = text[start:end]
                                return prompt.strip()
                    
                    # Try English format
                    elif 'Prompt:' in text:
                        marker = 'Prompt: "'
                        start = text.find(marker)
                        if start != -1:
                            start += len(marker)
                            end = text.find('"', start)
                            if end != -1 and end > start:
                                prompt = text[start:end]
                                return prompt.strip()
        
        return None
    except (json.JSONDecodeError, TypeError, IndexError, ValueError, SyntaxError):
        return None


def extract_reasoning(judge_output):
    """Extract reasoning from judge output."""
    if judge_output is None:
        return None
    
    try:
        if isinstance(judge_output, str):
            # Remove markdown code block formatting if present
            text = judge_output.strip()
            if text.startswith('```json\n') and text.endswith('\n```'):
                text = text[8:-4]  # Remove ```json\n and \n```
            elif text.startswith('```\n') and text.endswith('\n```'):
                text = text[4:-4]  # Remove ```\n and \n```
            
            # Parse JSON
            judge_output = json.loads(text)
        
        if isinstance(judge_output, dict):
            return judge_output.get('reasoning')
        
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def main():
    st.set_page_config(
        page_title="Sample Analyzer", 
        page_icon="🔍", 
        layout="wide"
    )
    
    st.title("🔍 Sample Analyzer")
    st.markdown("**Interactive analysis of unsuccessful eval samples**")
    
    # File selection
    st.sidebar.header("Configuration")
    
    # Look for CSV files in the output directory
    output_dir = Path("output")
    csv_files = list(output_dir.glob("*_samples_*.csv")) if output_dir.exists() else []
    
    if not csv_files:
        st.error("No sample CSV files found in the output directory.")
        st.stop()
    
    # Let user select the CSV file
    selected_file = st.sidebar.selectbox(
        "Select CSV file", 
        options=[f.name for f in csv_files],
        index=0
    )
    
    csv_path = output_dir / selected_file
    
    # Score threshold
    score_threshold = st.sidebar.slider(
        "Show samples with scores ≤", 
        min_value=1, max_value=4, value=2, step=1,
        help="Display samples scoring at or below this threshold"
    )
    
    # Load and process data
    with st.spinner("Loading and processing data..."):
        df = load_and_parse_data(str(csv_path))
        
        # Extract scores from both judge outputs
        df['deepseek_score'] = df['output_allam_identity_deepseek-v3_outputs_0'].apply(extract_judge_score)
        df['qwen_score'] = df['output_allam_identity_qwen3-235b-a22b-instruct-2507-tput_outputs_0'].apply(extract_judge_score)
        
        # Extract reasoning
        df['deepseek_reasoning'] = df['output_allam_identity_deepseek-v3_outputs_0'].apply(extract_reasoning)
        df['qwen_reasoning'] = df['output_allam_identity_qwen3-235b-a22b-instruct-2507-tput_outputs_0'].apply(extract_reasoning)
        
        # Extract original prompts
        df['original_prompt'] = df['output_allam_identity_deepseek-v3_inputs_0'].apply(extract_original_prompt)
        
        # Extract model response (clean up the list format)
        df['model_response'] = df['output_generations'].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else str(x) if x is not None else ""
        )
        
        # Get minimum score for each sample
        df['min_score'] = df[['deepseek_score', 'qwen_score']].min(axis=1)
        
        # Filter unsuccessful samples
        unsuccessful_samples = df[
            (df['min_score'] <= score_threshold) & 
            (df['min_score'].notna())
        ].copy()
    
    # Display statistics
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Statistics")
    st.sidebar.metric("Total samples", len(df))
    st.sidebar.metric("Unsuccessful samples", len(unsuccessful_samples))
    
    if len(unsuccessful_samples) == 0:
        st.warning(f"No samples found with scores ≤ {score_threshold}")
        st.stop()
    
    # Sort by worst score first
    unsuccessful_samples = unsuccessful_samples.sort_values('min_score')
    
    st.markdown(f"### Unsuccessful Samples (Score ≤ {score_threshold})")
    st.markdown(f"Found **{len(unsuccessful_samples)}** samples that need attention.")
    
    # Sample selector
    sample_options = [f"Sample {i+1} (Score: {row['min_score']})" for i, (_, row) in enumerate(unsuccessful_samples.iterrows())]
    selected_sample_idx = st.selectbox("Select sample to analyze:", options=range(len(sample_options)), format_func=lambda x: sample_options[x])
    
    if selected_sample_idx is not None:
        sample = unsuccessful_samples.iloc[selected_sample_idx]
        
        # Create three columns
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader("📝 Original Prompt")
            original_prompt = sample['original_prompt']
            if original_prompt:
                st.text_area("Prompt given to model:", value=original_prompt, height=150, disabled=True)
            else:
                st.info("Original prompt not available")
        
        with col2:
            st.subheader("🤖 Model Response")
            model_response = sample['model_response']
            st.text_area("Model's actual response:", value=model_response, height=150, disabled=True)
        
        with col3:
            st.subheader("📊 Evaluation Scores")
            deepseek_score = sample['deepseek_score']
            qwen_score = sample['qwen_score']
            
            if deepseek_score is not None:
                st.metric("DeepSeek Judge", deepseek_score, delta=f"{deepseek_score - 4} from perfect")
            if qwen_score is not None:
                st.metric("Qwen Judge", qwen_score, delta=f"{qwen_score - 4} from perfect")
        
        # Show reasoning from judges
        st.markdown("---")
        st.subheader("🧠 Judge Reasoning")
        
        judge_col1, judge_col2 = st.columns(2)
        
        with judge_col1:
            st.markdown("**DeepSeek Judge Reasoning:**")
            deepseek_reasoning = sample['deepseek_reasoning']
            if deepseek_reasoning:
                st.text_area("", value=deepseek_reasoning, height=100, disabled=True, key="deepseek_reasoning")
            else:
                st.info("No reasoning available")
        
        with judge_col2:
            st.markdown("**Qwen Judge Reasoning:**")
            qwen_reasoning = sample['qwen_reasoning']
            if qwen_reasoning:
                st.text_area("", value=qwen_reasoning, height=100, disabled=True, key="qwen_reasoning")
            else:
                st.info("No reasoning available")
        
        # Additional sample metadata
        st.markdown("---")
        st.subheader("📋 Sample Metadata")
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        
        with meta_col1:
            st.info(f"**Sample ID:** {sample['sample_id']}")
        with meta_col2:
            st.info(f"**Task Run ID:** {sample['task_run_id']}")
        with meta_col3:
            st.info(f"**Finish Reason:** {sample.get('output_finish_reasons', ['Unknown'])[0] if isinstance(sample.get('output_finish_reasons'), list) else sample.get('output_finish_reasons', 'Unknown')}")


if __name__ == "__main__":
    main()
