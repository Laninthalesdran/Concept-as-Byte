# Questions the model is trained on

ZophiaE 25M v3 is a specialist: it reasons inside eleven trained
families of logic. Inside that box it computes, refuses correctly, and
shows its work; outside it, the translator drops what it can't carry
(with a reason) or the model answers from the nearest shape it knows.
This file is the box, with paste-ready examples.

**House rules for every question**
- short declarative sentences, one fact each, ending in periods
- digits for numbers (`56`, not "fifty-six")
- exactly one question, at the end, with `?`
- plain words — the dictionary is bounded; if a sentence is dropped,
  the window tells you why; rephrase with simpler words
- the question word picks the answer type:
  *does / is / can / will* → **yes**, **no**, or **we can not say**;
  *what / which / where / how many* → an open answer with the work

The deepest trick in the whole file: **change a number and the verdict
follows the arithmetic, not the template.** Every example below stays
true if you vary the quantities — that's the point.

---

## 1. Arithmetic chains (the showcase — verified live)

Stock ÷ rate against a deadline, feeding a rule. One setup, four
different questions, four different correct behaviors:

    john has 56 breads. the group uses 4 breads each month. the bread
    must last 15 months. if the bread does not last, then the sun sets.
    does the sun set?

→ **yes** (56/4 = 14 < 15: the bread runs short, the rule fires).

    ... the bread must last 15 months. if the bread does not last,
    then the sun does not set. does the sun set?

→ **no** (same arithmetic, negative consequent).

    ... the bread must last 8 months. if the bread does not last, then
    the sun sets. does the sun set?

→ **we can not say** (14 ≥ 8: the bread lasts; the rule only speaks
about the case where it doesn't — refusing here is the correct move,
and the model explains why).

    ... the bread must last 15 months. if the bread does not last,
    then the sun sets. what happens to the sun?

→ the worked chain, no verdict word.

## 2. Plain conditionals (modus ponens, and the classic trap)

    if the rain falls, then the ground is wet. the rain falls. is the
    ground wet?

→ **yes**. And the trap that fools people:

    if the rain falls, then the ground is wet. the ground is wet. does
    the rain fall?

→ **we can not say** — wet ground doesn't prove rain. The model was
built specifically to stop falling for this.

## 3. Syllogism chains (verified live)

    a beetle is an insect. all insects are animals. so the beetle is
    an animal. if the beetle is an animal, then the horse sleeps. does
    the horse sleep?

→ **yes** — the taxonomy step feeds the conditional. Swap the last
sentence for `what happens to the horse?` for the open form, or make
the rule's condition `if the beetle is not an animal` for the refusal.

## 4. Claim-vetting (the skeptic)

    the neighbor finds a sign at the tree in the garden. the neighbor
    says the sign shows that the tree is dry. no one checked a second
    time. should we accept the conclusion?

→ **no**, with the reason (an unchecked reading doesn't carry the
claim). Variants that work: `another cause would also give exactly
that sign. does the conclusion stand?` → **no**;
`does that sign always show that?` → **we can not say**;
`what must we check before we may believe it?` → the open vetting
answer.

## 5. Defaults and exceptions

    usually birds fly. here is one bird in the river. will this one fly?

→ **we can not say** — a usual way is not a fact about this one; if it
turns out to be a penguin, it will not. Add `it is also a penguin.`
and ask again for the exception verdict.

## 6. Counting (inclusion–exclusion)

    7 children have an apple. 8 have a flower. 3 have both. how many
    children have one or more?

→ **12**, with the work: 7 + 8 − 3 = 12, and why the 3 would be
double-counted.

## 7. Proportions

    simon looked at 16 oils and found 8 bad ones. there are 64 oils in
    all. about how many is bad?

→ **about 32** — 8/16 of the group, 64 × 1/2 = 32.

## 8. Reachability and invariants (parity)

    the number is now 9. every move changes it by 4, up or down. can
    we reach 17?

→ **yes** (the difference 8 divides by 4). Ask about 7 instead →
**no**, with the invariant argument: the remainder after dividing by 4
never changes.

    we start at 30. every step takes away 4, and the number must stay
    bigger than 0. can this go on without end?

→ **no** — a falling whole number must stop; the model counts the
steps.

## 9. Time and duration

    the checking happened between 9 and 10. the usual time for the
    checking is 1 hour. did the checking run for a usual time?

→ **yes**, with the subtraction shown (10 − 9 = 1).

## 10. Board tactics (pins, skewers, forks)

State the geometry AND the values — the values are what the questions
turn on:

    the garden stands in front of the wall and must move, and then the
    wall is open. the garden is worth 6 and the wall is worth 3. is
    the garden worth more than the wall?

→ **yes**, plus why that order makes it a skewer and not a pin.

    the friend steps aside. behind it stands the brother. an attack on
    the well appears. where does the attack on the well come from?

→ **from the brother** — the mover only opened the way.

## 11. Queues

    a door can serve 9 persons each hour. 12 persons arrive each hour.
    will the line grow long?

→ **yes** — arrivals beat service. Flip the numbers for **no**.

---

## The known weak spot, stated plainly

Multi-clue placement puzzles ("five houses, five colors, who owns the
fish"-style constraint problems) are the model's hardest family — it
scores near 50% there, against 85–100% everywhere above. Play with
them if you like, but treat those answers as coin-flips; everything
else in this file is the strong ground.

## When you leave the box

Two different things can happen, and the window tells you which:

- **The translator refuses** — a sentence used words or grammar the
  dictionary can't carry. You'll see `dropped: … — reason`. Rephrase
  simpler; the question never reached the model.
- **The model improvises** — the sentence encoded fine but the shape
  is untrained. You'll get a fluent answer in a nearby trained shape;
  the verdict chip and confidence are your warning instruments. This
  is a 25-million-parameter specialist, not an oracle — the Verify
  tab shows exactly what it earns on never-seen questions inside the
  box, and nothing outside the box is covered by that number.
