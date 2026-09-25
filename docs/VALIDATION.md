# Validation plan

Regression cases:
- definite leak at normal exit
- safe allocate/free
- leak on early return
- alias freed through another pointer
- pointer overwrite
- user function freeing an argument
- double free

Research metrics:
- files/functions analyzed
- execution states explored before/after merging
- analysis wall time
- peak RSS
- true positives / false positives / false negatives
- parse failures
