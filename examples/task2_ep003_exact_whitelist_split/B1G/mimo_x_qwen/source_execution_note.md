Status: completed
Timestamp: 20260508_200616
Condition: B1_guardrailed
Rounds: 2
Episodes: 1
Pairs: deepseek_x_qwen, mimo_x_qwen
Seeds: [0]
Judge model: gpt-5.4-mini

Cells:
- ep003_totalseg_whitelist_split x deepseek_x_qwen seed=0: verdict=spec_weak handoff=1 spec=2 worker=1 violations=[]
- ep003_totalseg_whitelist_split x mimo_x_qwen seed=0: verdict=spec_strong handoff=8 spec=9 worker=7 violations=[]
