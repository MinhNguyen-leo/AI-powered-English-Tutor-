# prompt_builder.py

def build_prompt(user_input, context):
    return f"""
You are an English tutor.

User sentence:
{user_input}

User past mistakes:
{context}

Tasks:
1. Correct the sentence
2. Explain errors
3. Suggest improvement

Return JSON only.
"""