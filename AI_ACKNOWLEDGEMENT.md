# AI Acknowledgement

**Author:** Doan Nam Khanh

This project uses AI assistance, and I want to be clear about where and how.

## What is mine

- The original university assignment: a staff scheduling problem for a fast-casual restaurant, analysed with linear programming and queuing theory.
- The optimisation model itself: the decision variables, the objective (minimise weekly labour cost) and the constraints (daily coverage, weekly hour caps, availability). I first built and solved it in Excel Solver.
- The decisions about how the tool should behave, for example measuring coverage in hours rather than headcount, and keeping the solver simple enough for me to understand.
- Running, testing and checking the tool on my own computer.
- Anonymising the data: all names, pay rates, availability and required hours in this repository are synthetic and are not taken from any real organisation.

## Where AI helped

I used Claude (made by Anthropic) to:

- translate my Excel Solver model into Python (using `scipy.optimize.milp`)
- structure the code, and write the pop-up window in its own file (`roster_display.py`)
- help find and fix problems, such as the solver scheduling people on days they were unavailable
- help set up Python and Visual Studio Code on Windows and troubleshoot errors
- draft and reword the README so that someone with no coding background can run the tool

## How I used it

I treated the AI output as a draft. I asked for explanations of the code, ran the tool, compared its results with my Excel model, and changed things that did not look right. I am responsible for the final project, including any mistakes in it.

## Why I'm sharing this

I built this to show how I turn an analytical model into a tool that non-technical people can use. Being open about the AI help is part of presenting that work honestly.
