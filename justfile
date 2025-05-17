dev:
    python main.py
test test_target="":
    pytest {{test_target}} --cov
