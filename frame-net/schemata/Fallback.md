# Fallaback
A fallback schema is a sequence of tiered remediation measures, activated by designated trigger conditions.

## Schemata
[Trigger Condition] 1.Failed/ 2.Timeout/ 3.Nullity 4.Cannot self-heal-> 
[Remediation Measures] 1.Graceful Degradation/ 2.Multi-tier Fallback/ 3.Side Effects/ 4.Manual Intervention

## Instances
1. [Python:3.11.9] 
Trigger Condition: `format(value, spec)`where spec is null or "" -> Nullity
Remediation Measures: `str(value)` -> Fallaback by Graceful Degradation

2. [K8s]
Trigger Condition: unicast_peer is null -> Nullity
Remediation Measures: multicast -> Fallaback by Side Effects

3. [K8s] 
Trigger Condition: Instance [2.[K8s]] network state degrades further -> Cannot self-heal
Remediation Measures: Kill the process via `stop keepalived` -> Fallaback by Manual Intervention

4. [RAG] 
Trigger Condition: rerank is Timeout/Failed -> Timeout & Failed
Remediation Measures: RRF fusion results -> Fallaback by Graceful Degradation

## Minimal Pair
Unavalible: Graceful Degradation VS Side Effects

## Macro Invariant
