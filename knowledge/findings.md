# Findings

Use this file for distilled takeaways only, not raw experiment dumps.

## Iteration 01, initial implementation pass
_Preliminary, before formal reflection._

- The first event-study implementation ran successfully on **5,104 aligned trading days**.
- It found **572 setups**, produced **10,231 triggered event rows** across holding windows, and generated **288 summary rows**.
- Under the current heuristic verdict rules, **30 rows** were tagged `promote`.
- The strongest early cluster is **QQQ leading / DIA lagging**, especially in **S1** branches.
- In the early summary, **T1 (relative-strength turn)** and **T5 (gap compression)** look more promising than several other triggers when **QQQ leads**.
- A noteworthy detail: the **baseline control T0** already shows positive rows in some **QQQ-leading** cases, which means part of the effect may start on or near the setup itself.
- The opposite direction, **DIA leading / QQQ lagging**, looks less consistently strong in the initial pass, though not uniformly dead.

## Iteration 02, narrowed rerun
_Preliminary, before formal Iteration 02 reflection._

- Iteration 02 narrowed the search to **28 summary rows** and **593 filtered event rows**.
- The core **QQQ leads / DIA lags** hypothesis survived the narrowing.
- **S1_T1_QQQ_leads** remains the cleanest core branch, especially at **60-day** and **252-day** highs.
- **T1** now looks more convincing than the control **T0** in several QQQ-leading comparisons, especially around the **4-day** horizon.
- **S1_T5_QQQ_leads** remains alive, but it looks stronger at **252-day highs** than at **60-day highs**.
- **S1_T3_QQQ_leads** looks more mixed after narrowing and may be a drop candidate.
- The asymmetric wildcard **S2_T4_DIA_leads** is still alive, but mostly as a **2-day** effect; the 3-day window is weaker.

## Iteration 03, candidate-rule emergence
_Preliminary validation-stage read._

- Iteration 03 reduced the project to **18 summary rows** and **392 filtered event rows**.
- **T1** survived as the strongest primary trigger in the QQQ-leading core setup.
- The clearest T1 cluster is around **60-day / 4-day** and **252-day / 4 to 5-day**.
- **T5** survived as a selective secondary trigger, strongest in the **252-day** cluster and still alive at **60-day / 5-day**.
- **T0** remains meaningful as a control, especially in the 252-day setup, but it is no longer the preferred primary entry concept.
- The DIA-leading side remains non-core and survives only as a narrow exploratory 2-day wildcard.
- A research-stage candidate rule draft was formalized in `knowledge/candidate-rule-v0.md`.

## Candidate-rule validation
- Under **non-overlapping trade selection** and **next-open execution**, the setup-only control weakens substantially.
- The core thesis still survives, which increases confidence that the trigger logic is doing real work.
- The strongest validated shortlist is now:
  - `T1_60_4`
  - `T1_252_5`
  - `T5_252_5`
- `T5_252_5` looks particularly robust to simple cost drag.
- The project has now moved from branch search into shortlist comparison.

## Final shortlist comparison
- The evidence is stronger for a **2-rule family** than for one universal winner.
- Best faster candidate: `T1_60_4`
- Best slower, more cost-robust candidate: `T5_252_5`
- That 2-rule family is now formalized in `knowledge/candidate-rule-v2.md`.

## Promotion standard
A branch is worth carrying forward when it shows:
- positive average excess return,
- hit rate above 50%,
- and consistency across subperiods.
