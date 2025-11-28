# main.py
from controller import repair_code

if __name__ == "__main__":
    # 🔹 Try different buggy codes here

    # 1) IndexError example
    buggy_code = """
arr = [1, 2, 3]
for i in range(4):
    print(arr[i])
"""

    # 2) SyntaxError example (uncomment to test)
    # buggy_code = """
    # x = 10
    # if x > 5
    #     print("big")
    # """

    # 3) NameError example (uncomment to test)
    # buggy_code = """
    # arr = [1, 2, 3]
    # for i in range(len(arr)):
    #     print(ar[i])
    # """

    session = repair_code(buggy_code, max_iterations=3)

    print("=== REPAIR SUCCESS:", session.success)
    if session.failure_reason:
        print("=== FAILURE REASON:", session.failure_reason)

    print("\n=== ITERATION LOGS ===")
    for log in session.iterations:
        print(f"\n--- Iteration {log.iteration} ---")
        print("Success:", log.run_result.success)
        print("Timeout:", log.run_result.timeout)
        print("Return code:", log.run_result.return_code)
        print("STDOUT:")
        print(log.run_result.stdout)
        print("STDERR:")
        print(log.run_result.stderr)
        if log.patch:
            print("Patch description:", log.patch.description)
            print("---- New Code After Patch ----")
            print(log.patch.new_code)
        print("Notes:", log.notes)

    print("\n=== FINAL CODE ===")
    print(session.final_code)
