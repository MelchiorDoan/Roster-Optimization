"""
************************************************************************
  Linear Programming — Staff Roster Optimiser
 
  Developed by:
    Doan Nam Khanh
 
  Solves a binary linear program that decides WHICH DAYS each employee
  works, minimising total weekly labour cost, subject to:
    1. Daily hours coverage        (hours worked per day >= hours required per day)
    2. Individual weekly hour caps (each employee's scheduled hours <= their max)
    3. Availability                (nobody is scheduled on a day they have no shift)
 
*************************************************************************
 
DEPENDENCIES
    Python                 3.10+
    scipy                  1.9+    (provides the MILP solver)
    pandas                 2.0+    (CSV loading and result tables)
    numpy                  1.24+   (array/matrix operations feeding the solver)
 
NOTE ON SOLVER CHOICE
    This uses scipy.optimize.milp, a solver that comes with the scipy
    package, so no separate solver software needs to be installed.
 
*************************************************************************
INPUT FILES
    staff_availability.csv : one row per employee
        employee_id, weekday_payrate,
        monday_hours ... sunday_hours   (hours per shift on that day, not hours
                                         actually worked | 0 = unavailable, not "worked zero hours")
        max_weekly_hours                (most hours the employee can work in a week)
 
    staff_demand.csv : one row per day
        day, hours_required             (total hours of work needed that day,
                                         e.g. 3 people x 6 hours = 18)
 
    Saturday and Sunday pay are calculated automatically at 1.25x and 1.5x
    the weekday rate (standard penalty-rate assumption — edit PENALTY_RATES
    below if your case differs).
 
*************************************************************************
OUTPUT
    optimised_roster.csv : which employees work which days, plus each
    employee's total hours and total cost.
 
    The coverage check (hours required vs. hours scheduled) and the total
    weekly labour cost are shown on screen and in the pop-up window. They
    are not saved in the CSV.
 
*************************************************************************
USAGE
    To try the tool with the included sample data, just run:
 
        python roster_optimizer.py
 
    To run it on your own data, replace the sample file names with your own.
    The files must already exist in this same folder, or the script will fail
    with a FileNotFoundError:
 
        python roster_optimizer.py --staff my_real_staff_data.csv --demand my_real_demand.csv --out this_week_roster.csv
 
    A pop-up window showing the roster opens automatically every time you
    run this script (in addition to the terminal output) — this is what
    makes clicking VS Code's ▶ Run button show the pop-up too, with no
    extra flags needed.
 
    If you're running on a headless server or a remote terminal with no
    graphical display, add --no-popup to skip the window and avoid an
    error message:
 
        python roster_optimizer.py --no-popup
 
*************************************************************************
KNOWN MODELLING PITFALL (already fixed in this version — see build_and_solve)
    An earlier version of this model allowed an employee to be "scheduled"
    on a day they had zero available hours, since that costs nothing and
    still counts as a person on shift. The solver would exploit this to satisfy
    coverage requirements without any real staff present. Fixed by
    constraining each decision variable's upper bound to 0 on days the
    employee has no shift at all.
 
KNOWN LIMITATION
    Coverage is counted in total hours per day, not by time of day. Five
    people on 2-hour shifts add up to 10 hours even if all of them work at
    lunch and nobody is there in the evening. Covering specific times of
    day would need demand for each hour (for example from a queuing-theory
    calculation). Also, each employee works their whole listed shift or not
    at all, so a day can end up with slightly more hours than required.
"""

# ----------------------------- STANDARD LIBRARY -----------------------------
import argparse # Parses --staff / --demand / --out command-line arguments.
import sys # Used for sys.exit() on invalid input, with a readable error message.


# ----------------------------- THIRD-PARTY LIBRARIES ------------------------
import numpy as np # Builds the hours/rate/cost matrices fed into the solver.
import pandas as pd # Reads input CSVs and assembles the output roster/coverage tables.
from scipy.optimize import milp, LinearConstraint, Bounds  # Mixed-integer linear program solver (binary decision variables).

# ------------------------------- CONSTANTS -----------------------------------
# Canonical day ordering used throughout — every matrix column and every CSV day-column lines up against this list by position.

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Multiplier applied to weekday_payrate for weekend shifts. Change these if
# your case study uses different penalty rates (such as public holiday loading).
PENALTY_RATES = {"saturday": 1.25, "sunday": 1.5}

# ------------------------------- INPUT LOADING --------------------------------
# Load and validate the two input CSV files
def load_inputs(staff_path, demand_path):
    staff = pd.read_csv(staff_path)
    demand = pd.read_csv(demand_path)

    required_staff_cols = {f"{d}_hours" for d in DAYS} | {"employee_id", "weekday_payrate", "max_weekly_hours"}
    missing = required_staff_cols - set(staff.columns)
    if missing:
        sys.exit(f"staff_availability.csv is missing required column(s): {missing}")

    if "hours_required" not in demand.columns:
        sys.exit("staff_demand.csv must have a column called hours_required")
    demand = demand.set_index(demand["day"].str.lower())["hours_required"]

    missing_days = set(DAYS) - set(demand.index)
    if missing_days:
        sys.exit(f"staff_demand.csv is missing required day(s): {missing_days}")

    return staff, demand

# --------------------------- MODEL CONSTRUCTION & SOLVE -----------------------
def build_and_solve(staff, demand):    
    """
    Build the binary linear program and solve it.
 
    Decision variables
        x[e, j] in {0, 1} — 1 if employee e is scheduled on day j, else 0.
 
    Objective
        Minimise total labour cost = sum over all (e, j) of x[e, j] * cost[e, j].
 
    Constraints
        1. Coverage       — for each day, hours worked by the people scheduled
                             >= hours required that day.
        2. Hour cap       — for each employee, total scheduled hours <= their weekly max.
        3. Availability   — (enforced via variable bounds, not a constraint row)
                             an employee cannot be scheduled on a day they have
                             no shift hours availability for at all.
    """
    n_emp = len(staff)
    n_days = len(DAYS)

    # hours[e, j] = shift length for employee e on day j (0 if unavailable that day)
    hours = staff[[f"{d}_hours" for d in DAYS]].to_numpy(dtype=float)

    # rate[e, j] = pay rate that applies to employee e's hours on day j
    rate = np.zeros_like(hours)
    for j, d in enumerate(DAYS):
        multiplier = PENALTY_RATES.get(d, 1.0)
        rate[:, j] = staff["weekday_payrate"].to_numpy() * multiplier

    # cost[e, j] = cost of scheduling employee e on day j
    cost = hours * rate

    # Decision variables: x[e, j] in {0, 1}
    n_vars = n_emp * n_days

    def idx(e, j):
        # Converts (employee number e, day number j) into a position in the single long list the solver works with.
        return e * n_days + j

    # Objective: minimise total cost
    c = cost.flatten()

    constraints = []

    # Constraint 1 - coverage: for each day, total hours worked by the people
    # scheduled >= hours required. Each person counts as their shift length
    # (hours[e, j]), not as one head, so a 1-hour shift cannot stand in for a full day.
    # scipy's milp minimises, and LinearConstraint takes lb <= A.x <= ub, so we
    # express "at least required" as required <= (sum) <= the most hours that
    # could possibly be worked that day (a ceiling that never actually limits anything).
    for j, d in enumerate(DAYS):
        row = np.zeros(n_vars)
        for e in range(n_emp):
            row[idx(e, j)] = hours[e, j]
        constraints.append(LinearConstraint(row, lb=demand[d], ub=hours[:, j].sum()))

    # Constraint 2: weekly hour cap -- for each employee, sum of hours worked across the week <= their max_weekly_hours
    for e in range(n_emp):
        row = np.zeros(n_vars)
        for j in range(n_days):
            row[idx(e, j)] = hours[e, j]
        constraints.append(LinearConstraint(row, lb=0, ub=staff["max_weekly_hours"].iloc[e]))

    integrality = np.ones(n_vars)  # all variables binary

    # Constraint 3 — availability (via bounds, not a constraint row):
    # An employee can only be scheduled on a day they actually have a shift for.
    # Without this, the solver can "assign" someone to a 0-hour day for free,
    # which satisfies the coverage constraint without any real staff present.
    
    max_allowed = np.ones(n_vars) # highest value each box may take (1 = may be scheduled)
    for e in range(n_emp):
        for j in range(n_days):
            if hours[e, j] <= 0:
                max_allowed[idx(e, j)] = 0  # no shift that day -> box locked at 0
    bounds = Bounds(lb=0, ub=max_allowed)

    result = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)

    if not result.success:
        sys.exit(f"Solver failed to find a feasible roster: {result.message}\n"
                  f"Check that staff availability can actually meet the required hours.")

    x = result.x.reshape(n_emp, n_days)
    return x, hours, cost

# ------------------------------- OUTPUT BUILDING -------------------------------
def build_output(staff, demand, x, hours, cost):
    """
    Convert the solver's raw 0/1 array into readable results:
      - schedule  : which employee works which day, plus their weekly hours/cost
      - coverage  : hours required vs. hours scheduled per day, and whether it was met
      - total_cost: the single headline number (weekly labour cost)
    """
    schedule = pd.DataFrame(
        (x > 0.5).astype(int),
        index=staff["employee_id"],
        columns=DAYS,
    )

    scheduled_hours = schedule.to_numpy() * hours
    scheduled_cost = schedule.to_numpy() * cost

    schedule["total_hours"] = scheduled_hours.sum(axis=1)
    schedule["total_cost"] = scheduled_cost.sum(axis=1).round(2)

    coverage = pd.DataFrame({
        "day": DAYS,
        "hours_required": [demand[d] for d in DAYS],
        "hours_scheduled": scheduled_hours.sum(axis=0),
    })
    coverage["coverage_met"] = coverage["hours_scheduled"] >= coverage["hours_required"]

    total_cost = scheduled_cost.sum()
    return schedule.reset_index(), coverage, total_cost

# ------------------------------ READABLE SUMMARY --------------------------------
def format_roster_by_day(schedule, hours):
    """
    Turn the schedule table into a plain-English, day-by-day summary —
    e.g. "MONDAY: Employee_02 (5h), Employee_03 (4h)" — for someone who
    just wants to know who's working when and for how long, without
    opening the CSV or reading an employee-by-row grid of 0s and 1s.
 
    hours[row_position, day_index] gives the shift length for the employee
    in that row of `schedule` — row order matches the order hours was
    built in (see build_and_solve), which is preserved through
    build_output's reset_index().
    """
    lines = []
    for day_idx, day in enumerate(DAYS):
        working = []
        for row_idx, row in schedule.iterrows():
            if row[day] == 1:
                shift_hours = hours[row_idx, day_idx]
                working.append(f"{row['employee_id']} ({shift_hours:g}h)")
        day_label = day.upper()
        if working:
            lines.append(f"{day_label:<10} {', '.join(working)}")
        else:
            lines.append(f"{day_label:<10} (no one scheduled)")
    return "\n".join(lines)

# ----------------------------------- MAIN ---------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Optimise weekly staff roster to minimise labour cost.")
    parser.add_argument("--staff", default="staff_availability.csv")
    parser.add_argument("--demand", default="staff_demand.csv")
    parser.add_argument("--out", default="optimised_roster.csv")
    parser.add_argument("--no-popup", action="store_true",
                         help="Skip the graphical pop-up window and only print to the terminal.")
    args = parser.parse_args()

    staff, demand = load_inputs(args.staff, args.demand)
    x, hours, cost = build_and_solve(staff, demand)
    schedule, coverage, total_cost = build_output(staff, demand, x, hours, cost)

    schedule.to_csv(args.out, index=False)
    
    roster_text = format_roster_by_day(schedule, hours)
    coverage_text = coverage.to_string(index=False)

    print(f"Roster written to {args.out}\n")
    print("Who's working each day:")
    print(roster_text)
    print("\nCoverage check:")
    print(coverage_text)
    print(f"\nTotal weekly labour cost: ${total_cost:,.2f}")
 
    if not args.no_popup:
        try:
            from roster_display import show_roster_window  # the pop-up lives in its own file
            employees = [
                (row["employee_id"],
                 [hours[i, j] if row[day] == 1 else 0 for j, day in enumerate(DAYS)],
                 row["total_hours"])
                for i, row in schedule.iterrows()
            ]
            show_roster_window(DAYS, employees,
                               coverage["hours_required"].tolist(),
                               coverage["hours_scheduled"].tolist(),
                               total_cost)
        except Exception as e:
            print(f"\nCould not open pop-up window ({e}). "
                  f"This usually means there's no graphical display available "
                  f"(e.g. a headless server or remote SSH session). "
                  f"Run with --no-popup to skip this window and avoid seeing this message.")

if __name__ == "__main__":
    main()