def critic_agent(state):

    risk  = state["risk_score"]

    # Fix — copy the dict before mutating to avoid race conditions
    # in threaded Flask (app.run(threaded=True)) where two requests
    # could share the same allocation dict reference
    allocation = dict(state["allocation"])

    # Get how many times critic has already retried (default 0)
    count = state.get("retry_count", 0)

    # Determine if re-allocation is needed
    needs_retry = risk > 70 and allocation["Stocks"] < 60

    if needs_retry and count < 3:
        # Adjust allocation on the copy
        allocation["Stocks"] += 10
        allocation["Bonds"]  -= 5
        allocation["Cash"]   -= 5

        state["allocation"]  = allocation
        state["retry"]       = True
        state["retry_count"] = count + 1

        state["logs"].append(
            f"Critic triggered re-allocation (attempt {count + 1}/3)."
        )

    else:
        # Either allocation is good OR max retries (3) reached
        state["retry"]       = False
        state["retry_count"] = count

        if count >= 3:
            state["logs"].append(
                "Critic reached max retries (3). Proceeding with current allocation."
            )
        else:
            state["logs"].append("Critic approved strategy.")

    return state