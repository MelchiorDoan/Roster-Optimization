# Roster Optimiser

**Author:** Doan Nam Khanh

**Tested with:** Python 3.15.1 and Visual Studio Code 1.143.1 on Windows

A binary linear program that builds a weekly staff roster at minimum labour
cost, subject to daily coverage requirements and each employee's weekly hour
cap. Built as a synthetic case study modelling a fast-casual restaurant's
scheduling problem (not based on real company data).

## What it does

Given:
- **who's available**, on which days, for how many hours, at what pay rate
- **how many hours of work are needed** on each day of the week

...it decides **which employees should work which days** to meet every
day's hours requirement at the lowest possible total cost, without
exceeding anyone's weekly hour limit.

This is a 0-1 (binary) assignment problem: each employee/day pair is either
"scheduled" (1) or "not scheduled" (0). It's solved as an integer linear
program using `scipy.optimize.milp`.

## Quick start for users with no background in coding

### Step 1: Install Python

Python is a free program that runs this tool. You only need to do this once.

1. Go to [python.org/downloads](https://www.python.org/downloads/) and click the download button.
2. Open the file you downloaded.
3. On the first screen, tick the box at the bottom that says **"Add python.exe to PATH"**. Do not skip this, the tool will not work without it. Then click **Install Now**.
4. When it says the setup was successful, click **Close**.

Already have Python? You can skip this step.

### Step 2: Open the project in Visual Studio Code

If you don't have it, download it free from https://code.visualstudio.com and install it.

1. Open Visual Studio Code.
2. Click **File** at the top, then **Open Folder...**
3. Select the folder you downloaded (the one containing `roster_optimizer.py`) and click **Select Folder**. If it asks "Do you trust the authors?", click **Yes**.
4. On the left you will now see the project's files, including `roster_optimizer.py`.
5. Click **Terminal** at the top, usually hidden within the 3 dots, then **New Terminal**. A panel opens at the bottom of the window. That is where you type the commands in the next steps.

**Using a different program (PyCharm, Spyder, IDLE, or similar)?** That works too. Open the same folder in your program and open its terminal. The commands in the next steps are the same, as long as the terminal is inside the folder that contains `roster_optimizer.py`.

### Step 3: Check that Python is installed

In the terminal at the bottom, type this and press **Enter**:

```shell
python --version
```
> [!NOTE]
> If you see an error saying Python is not installed, close Visual Studio Code and any other terminal or program you have open, then open it again. This happens when a program was already open before Python was installed.

### Step 4: Install the extra pieces the tool needs

You only need to do this once. Paste this into the terminal and press **Enter**:

```shell
pip install -r requirements.txt
```

This can take a few minutes, and the screen may show nothing for a while. Wait until you see a new line where you can type again.

If the terminal says `pip` is not recognised, paste this instead:

```shell
python -m pip install -r requirements.txt
```

### Step 5: Run the tool on the sample data

Paste this into the terminal and press **Enter**:

```shell
python roster_optimizer.py
```

A window opens showing who works each day. The same information is printed in the terminal, and a file called `optimised_roster.csv` is saved in the folder (you can open it in Excel).

If something goes wrong, see the **Troubleshooting** section further down.

## Using your own data

Replace the sample filenames with your own. **The names below are
placeholders** — they only work if files with exactly those names already
exist in this folder:

```shell
python roster_optimizer.py --staff my_staff.csv --demand my_demand.csv --out this_week_roster.csv
```

| option | what it does | default |
|---|---|---|
| `--staff` | staff availability CSV to read | `staff_availability.csv` |
| `--demand` | daily demand CSV to read | `staff_demand.csv` |
| `--out` | where to save the roster CSV | `optimised_roster.csv` |
| `--no-popup` | skip the pop-up window, print to the terminal only | pop-up is shown |

### `staff_availability.csv`
| column | meaning |
|---|---|
| `employee_id` | any label (use anonymised IDs if the data is real) |
| `weekday_payrate` | hourly rate, Mon–Fri |
| `monday_hours` … `sunday_hours` | length of the shift **if** scheduled that day, in hours. `0` means the employee is **not available** that day (it does not mean "worked zero hours") |
| `max_weekly_hours` | contracted weekly hour cap |

Saturday and Sunday pay are calculated automatically (1.25x and 1.5x the
weekday rate) — edit `PENALTY_RATES` in the script if your case uses
different multipliers.

### `staff_demand.csv`
| column | meaning |
|---|---|
| `day` | monday … sunday |
| `hours_required` | total hours of work needed that day. Work it out as people needed × hours each, for example 3 people × 6 hours = 18 |

> **Note on these figures:** in the original case study this project is based
> on, required staffing levels were an assumption rather than a measured
> value, and the hours in the sample file are illustrative in the same way.
> If you have real or modelled demand data (e.g. from a queuing theory /
> Erlang C calculation of servers needed to hit a target wait time), that's
> the more defensible way to populate this column.

## What you'll see

**1. A pop-up window** (opens automatically) with the full roster, coverage
check and total cost.

**2. The same information in the terminal**, for example:

```
Who's working each day:
MONDAY     Employee_04 (5h)
TUESDAY    Employee_02 (6h), Employee_05 (3h)
WEDNESDAY  Employee_04 (7h)
THURSDAY   Employee_03 (6h), Employee_04 (6h)
FRIDAY     Employee_01 (4h), Employee_02 (5h), Employee_03 (4h), Employee_05 (4h), Employee_06 (5h)
SATURDAY   Employee_02 (4h), Employee_03 (5h)
SUNDAY     Employee_02 (6h), Employee_05 (6h), Employee_06 (6h)

Coverage check:
      day  hours_required  hours_scheduled  coverage_met
   monday               5              5.0          True
  tuesday               9              9.0          True
wednesday               7              7.0          True
 thursday              12             12.0          True
   friday              20             22.0          True
 saturday               9              9.0          True
   sunday              18             18.0          True

Total weekly labour cost: $2,040.31
```

Each name is followed by the length of that day's shift. Friday shows 22 hours
against 20 required because each person works their whole listed shift or not
at all, so the cheapest combination that reaches 20 hours happens to give 22.

**3. `optimised_roster.csv`** — one row per employee: which days they're
scheduled (1 = working), total weekly hours, and total cost. Opens in Excel.
The coverage check and the total weekly cost are shown on screen only, not
saved in this file.

## Troubleshooting

| message | what it means | fix |
|---|---|---|
| `'python' is not recognized` (or a Microsoft Store window opens) | Python isn't installed, or it was installed without "Add python.exe to PATH" ticked | install Python from python.org (Step 1), tick the PATH box, then close the terminal and open a new one |
| `'pip' is not recognized` | the `pip` shortcut isn't set up, even though Python may be fine | use `python -m pip install -r requirements.txt` instead |
| `FileNotFoundError: ... No such file or directory` | the filename after `--staff` or `--demand` doesn't exist in this folder | check the spelling, or place the file in this folder |
| `ModuleNotFoundError: No module named 'numpy'` (or pandas / scipy) | the extra packages aren't installed for the Python you're running | run `python -m pip install -r requirements.txt` in the terminal (Step 4), then run the tool again |
| Running `python roster_optimizer.py` in the terminal works, but VS Code's ▶ Run button shows an error | VS Code is using a different Python from your terminal, one that may not have the packages installed | press Ctrl+Shift+P, choose **Python: Select Interpreter**, and pick the Python you installed in Step 1 (the one `python --version` shows) |
| `externally-managed-environment` | this Python is protected and refuses to install packages | create a separate environment for the project (see below) |
| `Could not open pop-up window` | no graphical display available (e.g. remote server), or `roster_display.py` is missing from the folder | run with `--no-popup`, or put `roster_display.py` next to `roster_optimizer.py` |
| `Solver failed to find a feasible roster` | the staff available can't provide the required hours on at least one day | lower `hours_required` for that day, or add availability |
| `staff_demand.csv must have a column called hours_required` | the demand file still uses the old `staff_required` column | rename the column to `hours_required` and enter hours instead of headcount |
| `... is missing required column(s)` | your CSV headers don't match the expected names | compare against the column tables above |

### If you see `externally-managed-environment`
 
Some Python installs (for example ones managed by `uv`) don't allow packages to be installed into them. Create a private environment inside the project folder instead. In the terminal, in the project folder, run these three lines one at a time:
 
```shell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```
 
On Mac, use `source .venv/bin/activate` for the second line. After that, run `python roster_optimizer.py` from the same terminal. In VS Code, press Ctrl+Shift+P, choose **Python: Select Interpreter**, and pick the one inside `.venv` so the ▶ Run button uses it too.

## Limitations

- **Hours are counted per day, not by time of day.** Five people on 2-hour
  shifts add up to 10 hours, even if all of them work at lunch and nobody is
  there in the evening. Treat the roster as a starting point: a manager should
  check it against the busy periods and, where needed, adjust start and finish
  times so more people are working when customers arrive. The next improvement
  would be entering demand per time block (for example lunch and dinner) so the
  tool covers time of day itself, with the numbers coming from a
  queuing-theory calculation.

- **Shifts are all-or-nothing.** Each employee works their whole listed shift
  on a day or not at all, so a day can end up with slightly more hours than
  required.
  
- **The sample data is made up.** The results show how the method works, not
  what a real restaurant should do.

## A modelling pitfall this project ran into (and fixed)

An earlier version of this model — including the original spreadsheet it
was translated from — allowed an employee to be "scheduled" on a day they
had zero available hours, because that costs nothing and still counts
toward coverage. The solver exploited this to satisfy coverage requirements
without any real staff present.

The fix: an employee can only be assigned to
a day where their available hours are greater than zero (enforced via
per-variable upper bounds). Worth knowing if you adapt this model —
it's an easy trap to fall into and easy to miss unless you inspect the
solver's output row by row.

A related trap: counting people instead of hours. When coverage was measured
as headcount, a 1-hour shift counted as a whole person and the solver used
1-hour shifts to "cover" entire days. Measuring coverage in hours removed it.

## Files

| file | purpose |
|---|---|
| `roster_optimizer.py` | the program |
| `requirements.txt` | Python packages to install |
| `staff_availability.csv` | sample staff input |
| `staff_demand.csv` | sample daily demand input (in hours) |
| `optimised_roster.csv` | sample output |
| `roster_display.py` | display the optimised roster |
| `AI_ACKNOWLEDGEMENT.md` | AI Acknowlegdement |

## Disclaimer

Staff names, pay rates, availability, and required-hours figures in the
sample data are synthetic/illustrative and not drawn from any real
organisation's actual roster.