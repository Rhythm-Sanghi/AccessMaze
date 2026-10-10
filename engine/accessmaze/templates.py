from accessmaze.models import Journey


def template(kind="accessible"):
    steps = [
        {"id": "open", "action": "navigate"},
        {
            "id": "name",
            "action": "fill",
            "target": {"role": "textbox", "name": "Applicant name"},
            "value": "Test Applicant",
        },
        {
            "id": "date",
            "action": "activate",
            "target": {"role": "button", "name": "Choose date"},
            "effect": True,
        },
        {
            "id": "review",
            "action": "activate",
            "target": {"role": "button", "name": "Review application"},
            "effect": True,
        },
        {
            "id": "ready",
            "action": "assert_visible",
            "target": {"role": "heading", "name": "Application ready"},
        },
    ]
    if kind == "modal":
        steps = [
            steps[0],
            {
                "id": "help",
                "action": "activate",
                "effect": True,
                "target": {"role": "button", "name": "Application help"},
            },
            {
                "id": "contained",
                "action": "assert_modal",
                "target": {"role": "dialog", "name": "Application help"},
            },
        ]
    if kind == "conditional":
        steps = [
            steps[0],
            steps[1],
            {
                "id": "international",
                "action": "activate",
                "effect": True,
                "target": {"role": "checkbox", "name": "International applicant"},
            },
            {
                "id": "passport-visible",
                "action": "assert_visible",
                "target": {"role": "textbox", "name": "Passport reference"},
            },
            {
                "id": "passport",
                "action": "fill",
                "value": "SYNTHETIC-000",
                "target": {"role": "textbox", "name": "Passport reference"},
            },
            steps[-2],
            steps[-1],
            {
                "id": "submit",
                "action": "activate",
                "effect": True,
                "target": {"role": "button", "name": "Submit synthetic application"},
            },
            {
                "id": "confirmed",
                "action": "assert_visible",
                "target": {"role": "heading", "name": "Application submitted"},
            },
        ]
    if kind == "errors":
        steps = [steps[0], steps[-2], {"id": "errors", "action": "assert_errors"}]
    if kind == "recovery":
        steps = [
            steps[0],
            steps[1],
            {"id": "disconnect", "action": "offline"},
            {"id": "reconnect", "action": "online"},
            {
                "id": "retained",
                "action": "assert_value",
                "target": steps[1]["target"],
                "value": "Test Applicant",
            },
        ]
    if kind == "slow":
        steps.insert(1, {"id": "slow", "action": "wait", "value": "10000"})
    if kind == "branch":
        steps += [
            {
                "id": "restart",
                "action": "activate",
                "target": {"role": "button", "name": "Start again"},
                "effect": True,
            },
            {
                "id": "empty-review",
                "action": "activate",
                "target": {"role": "button", "name": "Review application"},
                "effect": True,
            },
            {"id": "validation", "action": "assert_errors"},
        ]
    return Journey(name=f"Scholarship / {kind}", target=f"fixture://{kind}", steps=steps)
