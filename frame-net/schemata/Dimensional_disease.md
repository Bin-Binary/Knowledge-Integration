# Dimensional Disease
Dimensional Disease occurs when Source Entities exhibit discrepancies in Dimensions, thereby preventing direct computation or fusion.

## schemate
[Source Entities] 1.Heterogenous data/ 2.Multi-dimensional attributes -> 
[Discrepancies Dimension] 1.Dimensional Space/ 2.Dimensional Measurement ->
[Inhibitor Factor] 1.Dimensional Escape / 2.Dimensional Normalization

## Instances
1. [RAG] 
Source Entities: BM25 (Token-based Sparse Text) & KNN (Embedding-based Dense Vector) -> Heterogeneous data
Discrepancies Dimension: Symbolic Space（BM25） vs. Vector Space（KNN）& Unbounded Positive Number (BM25) vs. Bounded [-1, 1] (KNN) -> Dimensional Space & Dimensional Measurement
Inhibitor Factor: via RRF ranking fusion -> Resolved by Dimensional Escape

2. [CSS]
Source Entities: Primary Web Font File (Vector Glyphs (Coordinate-based Relative Curve)) & Fallback System Font File -> Heterogeneous data
Discrepancies Dimension: Both Relative EM-Square Space But Arbitrary Design Units (UPM Scale) vs. Fixed Device Pixels (px Scale)-> Dimensional Measurement
Inhibitor Factor: via CSS @font-face { size-adjust: X%; } -> Resolved by Dimensional Normalization

## Minimal Pair

## Macro Invariant
