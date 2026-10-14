# FrameNet Document Annotation: Python List

## Document Slicing

| Metric | Value |
|--------|-------|
| Total fragments | 15 |
| High value (nl_description) | 7 |
| Medium value (nl_action) | 2 |
| Low value | 5 |
| Skip | 1 |
| Eligible for analysis | 9 |
| Skipped | 6 |

## Overall Statistics

| Metric | Value |
|--------|-------|
| Processed fragments | 9 |
| Total annotated words | 34 |
| Unique frames | 15 |
| Frame relations found | 16 |
| High confidence | 8 |
| Medium confidence | 7 |
| Low confidence | 5 |
| No match | 14 |
| FrameNet LU matched | 19 |
| LLM inferred | 1 |

## Global Frame Index

| Frame | Triggers | Fragments | Conf | Source | Core FEs |
|-------|----------|-----------|------|--------|----------|
| Absence | empty | F04 | [+] low | FN | Absent_entity, Context |
| Activity | method, function | F09, F12 | [+] low | FN | Actor, Action |
| Aggregate | Lists, collections | F01 | [+++] high | FN | Individuals, Aggregate |
| Change_of_state | mutable | F01 | [+] low | LLM | Entity, Final_state, Initial_state |
| Creating | builds | F08 | [++] medium | FN | Creator, Created_entity |
| Diversity | homogeneous | F01 | [+++] high | FN | Group, Dimension |
| Entity | items, elements | F01, F14 | [++] medium | FN | Entity |
| Ordering | sorts, sorted | F09, F14 | [+++] high | FN | Ordered_entity, Ordering_predicate |
| Receiving | accepts | F11 | [++] medium | FN | Recipient, Theme |
| Removing | extract | F12 | [++] medium | FN | Agent, Theme, Source |
| Sequence | sequences, order | F01, F08 | [+++] high | FN | Entity_1, Entity_2, Entities |
| Signification | denote | F04 | [++] medium | FN | Sign, Signified |
| Storing | store | F01 | [+++] high | FN | Agent, Theme, Location |
| Typicality | typically | F01 | [+++] high | FN | State_of_affairs, Feature |
| Using | used | F01 | [+] low | FN | Agent, Instrument, Purpose |

## Cross-Frame Relations

| Source | Target | Relation | Direction | Detail |
|--------|--------|----------|-----------|--------|
| Aggregate | Using | hierarchical | sibling | common ancestor: Event |
| Aggregate | Storing | hierarchical | sibling | common ancestor: Event |
| Aggregate | Creating | hierarchical | sibling | common ancestor: Event |
| Aggregate | Receiving | hierarchical | sibling | common ancestor: Event |
| Aggregate | Removing | hierarchical | sibling | common ancestor: Event |
| Typicality | Diversity | hierarchical | sibling | common ancestor: Gradable_attributes |
| Using | Storing | hierarchical | sibling | common ancestor: Transitive_action |
| Using | Creating | hierarchical | sibling | common ancestor: Transitive_action |
| Using | Receiving | hierarchical | sibling | common ancestor: Event |
| Using | Removing | hierarchical | sibling | common ancestor: Transitive_action |
| Storing | Creating | hierarchical | sibling | common ancestor: Transitive_action |
| Storing | Receiving | hierarchical | sibling | common ancestor: Event |
| Storing | Removing | hierarchical | sibling | common ancestor: Transitive_action |
| Creating | Receiving | hierarchical | sibling | common ancestor: Event |
| Creating | Removing | hierarchical | sibling | common ancestor: Transitive_action |
| Receiving | Removing | hierarchical | sibling | common ancestor: Event |

## Fragment Annotations

### F01

> Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| Lists | Aggregate | [++] medium | FN | Individuals, Aggregate | Individuals→the items in the list; Aggregate→list |
| sequences | Sequence | [+++] high | FN | Entity_1, Entity_2, Entities | Entities→items in the sequence |
| typically | Typicality | [+++] high | FN | State_of_affairs, Feature | State_of_affairs→use of lists to store items |
| used | Using | [+] low | FN | Agent, Instrument, Purpose | Agent→programmer; Instrument→lists; Purpose→to store collections |
| store | Storing | [+++] high | FN | Agent, Theme, Location | Agent→implied; Theme→collections; Location→lists |
| collections | Aggregate | [+++] high | FN | Individuals, Aggregate | Individuals→items; Aggregate→collections |
| homogeneous | Diversity | [+++] high | FN | Group, Dimension | Group→collections/items; Dimension→homogeneous |
| items | Entity | [++] medium | FN | Entity | Entity→individual elements |
| mutable | Change_of_state | [+] low | LLM | Entity, Final_state, Initial_state | — |

### F04

> Using a pair of square brackets to denote the empty list: []

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| denote | Signification | [++] medium | FN | Sign, Signified | Sign→square brackets []; Signified→empty list |
| empty | Absence | [+] low | FN | Absent_entity, Context | Absent_entity→items; Context→the list |

### F05

> Using square brackets, separating items with commas: [a], [a, b, c]

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| separating | — | [-] none | — | — | — |
| commas | — | [-] none | — | — | — |

### F07

> Using the type constructor: list() or list(iterable)

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| constructor | — | [-] none | — | — | — |
| iterable | — | [-] none | — | — | — |

### F08

> The constructor builds a list whose items are the same and in the same order as iterable items.

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| builds | Creating | [++] medium | FN | Creator, Created_entity | Creator→constructor; Created_entity→a list |
| order | Sequence | [+++] high | FN | Entities | Entities→iterable items |
| constructor | — | [-] none | — | — | — |
| whose | — | [-] none | — | — | — |
| iterable | — | [-] none | — | — | — |

### F09

> This method sorts the list in place, using only < comparisons between items.

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| method | Activity | [+] low | FN | Actor, Action | Actor→list object; Action→sorting |
| sorts | Ordering | [+++] high | FN | Ordered_entity, Ordering_predicate | Ordered_entity→list elements; Ordering_predicate→< comparison |
| comparisons | — | [-] none | — | — | — |

### F11

> sort() accepts two arguments that can only be passed by keyword (keyword-only arguments):

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| accepts | Receiving | [++] medium | FN | Recipient, Theme | Recipient→sort() method; Theme→keyword arguments |
| keyword | — | [-] none | — | — | — |
| keyword | — | [-] none | — | — | — |

### F12

> key specifies a function of one argument that is used to extract a comparison key from each list element.

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| function | Activity | [+] low | FN | Actor, Action | Actor→key function; Action→extract comparison key |
| extract | Removing | [++] medium | FN | Agent, Theme, Source | Agent→key function; Theme→comparison key; Source→each list element |
| specifies | — | [-] none | — | — | — |
| comparison | — | [-] none | — | — | — |

### F14

> If set to True, then the list elements are sorted as if each comparison were reversed.

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| elements | Entity | [++] medium | FN | Entity | Entity→list elements |
| sorted | Ordering | [+++] high | FN | Ordered_entity | Ordered_entity→list elements |
| comparison | — | [-] none | — | — | — |
| reversed | — | [-] none | — | — | — |

## Skipped Fragments

F02, F03, F06, F10, F13, F15

<!-- generated: 2026-10-14T18:55:22.797398 -->
