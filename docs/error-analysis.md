# Error analysis (stub)
Accuracy: 93.5%  Macro-F1: 0.94
## Confusion
| expected \ predicted | authentication | other | payment | refund | technical |
| authentication | 16 | 0 | 0 | 0 | 0 |
| other | 0 | 20 | 0 | 0 | 0 |
| payment | 0 | 0 | 20 | 0 | 0 |
| refund | 0 | 0 | 6 | 14 | 0 |
| technical | 0 | 0 | 0 | 0 | 16 |
## Top misses
- #30 exp=refund got=payment: Refund not received after cancelled subscription
- #36 exp=refund got=payment: Refund not received after cancelled subscription
- #64 exp=refund got=payment: Refund not received after cancelled subscription
- #79 exp=refund got=payment: Refund not received after cancelled subscription
- #85 exp=refund got=payment: Refund not received after cancelled subscription
- #92 exp=refund got=payment: Refund not received after cancelled subscription

